using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Godot;
using TecateSimulator.World;

namespace TecateSimulator.Systems;

public partial class TileStreamingSystem : Node
{
    [Signal]
    public delegate void TileStateChangedEventHandler(string tileId, string state);

    [Export]
    public string TileManifestPath { get; set; } = "res://resources/tile-manifest.json";

    [Export]
    public NodePath PlayerNodePath { get; set; } = new NodePath("");

    [Export]
    public int ActiveRadiusTiles { get; set; } = 5; // Keep all tiles loaded

    [Export]
    public int WarmRadiusTiles { get; set; } = 5;

    [Export]
    public WorldOrigin? OriginOverride { get; set; }

    private readonly Dictionary<string, PreparedTileRecord> _tilesById = new();
    private readonly Dictionary<(int X, int Y), PreparedTileRecord> _tilesByCoordinate = new();
    private readonly Dictionary<string, RuntimeTileState> _states = new();
    private readonly Dictionary<string, Node3D> _activeTileNodes = new();
    private PreparedTileManifest? _manifest;
    private WorldOrigin? _origin;

    // Shared materials - created once, reused across all tiles
    private ShaderMaterial? _terrainShaderMaterial;
    private StandardMaterial3D? _asphaltMat;
    private StandardMaterial3D? _concreteMat;
    private StandardMaterial3D? _yellowLineMat;
    private StandardMaterial3D? _polesMat;

    // Tecate architectural color palette - diverse per-building colors
    private static readonly Color[] BuildingPalette = new Color[]
    {
        new Color(0.90f, 0.88f, 0.84f, 1f),  // Plaster White
        new Color(0.85f, 0.82f, 0.74f, 1f),  // Cream/Off-white
        new Color(0.72f, 0.41f, 0.30f, 1f),  // Warm Terracotta
        new Color(0.85f, 0.68f, 0.38f, 1f),  // Pale Gold/Ochre
        new Color(0.40f, 0.65f, 0.68f, 1f),  // Soft Turquoise
        new Color(0.80f, 0.76f, 0.68f, 1f),  // Sandy Beige
        new Color(0.78f, 0.55f, 0.62f, 1f),  // Faded Rose
        new Color(0.65f, 0.72f, 0.65f, 1f),  // Sage Green
        new Color(0.75f, 0.60f, 0.45f, 1f),  // Adobe Tan
        new Color(0.60f, 0.55f, 0.50f, 1f),  // Concrete Grey
        new Color(0.82f, 0.78f, 0.70f, 1f),  // Light Sand
        new Color(0.55f, 0.40f, 0.35f, 1f),  // Dark Adobe
        new Color(0.70f, 0.75f, 0.82f, 1f),  // Pale Blue
        new Color(0.88f, 0.85f, 0.78f, 1f),  // Warm White
        new Color(0.72f, 0.65f, 0.55f, 1f),  // Khaki
        new Color(0.50f, 0.58f, 0.62f, 1f),  // Steel Blue-Grey
    };

    public override void _Ready()
    {
        InitializeMaterials();
        LoadManifestIfAvailable();
    }

    public override void _Process(double delta)
    {
        if (string.IsNullOrEmpty(PlayerNodePath.ToString()) || _manifest is null)
        {
            return;
        }

        Node3D? player = GetNodeOrNull<Node3D>(PlayerNodePath);
        if (player is not null)
        {
            UpdateStreaming(player.GlobalPosition);
        }
    }

    private void InitializeMaterials()
    {
        // Terrain: ShaderMaterial using the altitude/slope terrain shader
        Shader? terrainShader = GD.Load<Shader>("res://shaders/terrain.gdshader");
        if (terrainShader is not null)
        {
            _terrainShaderMaterial = new ShaderMaterial();
            _terrainShaderMaterial.Shader = terrainShader;
        }
        else
        {
            GD.PushWarning("Terrain shader not found at res://shaders/terrain.gdshader, using fallback material.");
        }

        // Road materials
        _asphaltMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.18f, 0.19f, 0.22f, 1f), // Dark slate road
            Roughness = 0.8f
        };

        _concreteMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.68f, 0.70f, 0.72f, 1f), // Concrete sidewalk grey
            Roughness = 0.7f
        };

        _yellowLineMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.85f, 0.75f, 0.15f, 1f), // Bright yellow lane divider
            Roughness = 0.6f
        };

        _polesMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.55f, 0.56f, 0.58f, 1f), // Concrete pole shade
            Roughness = 0.8f
        };
    }

    public void UpdateStreaming(Vector3 playerWorldPosition)
    {
        if (_manifest is null || _origin is null)
        {
            return;
        }

        Wgs84Point playerWgs84 = _origin.LocalMetersToWgs84(playerWorldPosition);
        PreparedTileRecord? currentTile = FindTile(playerWgs84);

        if (currentTile is null)
        {
            return;
        }

        HashSet<string> activeTiles = TilesWithinRadius(currentTile, ActiveRadiusTiles);
        HashSet<string> warmTiles = TilesWithinRadius(currentTile, WarmRadiusTiles);

        foreach (PreparedTileRecord tile in _manifest.Tiles)
        {
            RuntimeTileState targetState = RuntimeTileState.Cold;

            if (activeTiles.Contains(tile.Id))
            {
                targetState = RuntimeTileState.Active;
            }
            else if (warmTiles.Contains(tile.Id))
            {
                targetState = RuntimeTileState.Warm;
            }

            SetTileState(tile.Id, targetState);
        }
    }

    public RuntimeTileState GetTileState(string tileId)
    {
        return _states.TryGetValue(tileId, out RuntimeTileState state) ? state : RuntimeTileState.Missing;
    }

    private void LoadManifestIfAvailable()
    {
        if (!Godot.FileAccess.FileExists(TileManifestPath))
        {
            GD.PushWarning($"Tile manifest not found at {TileManifestPath}. Generate and copy a prepared manifest before runtime streaming.");
            return;
        }

        string absolutePath = ProjectSettings.GlobalizePath(TileManifestPath);
        string json = File.ReadAllText(absolutePath);

        _manifest = JsonSerializer.Deserialize<PreparedTileManifest>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        if (_manifest is null)
        {
            GD.PushError($"Tile manifest at {TileManifestPath} could not be deserialized.");
            return;
        }

        _origin = OriginOverride ?? WorldOrigin.FromCoordinateOrigin(new CoordinateOrigin(
            _manifest.CoordinateOriginWgs84.Latitude,
            _manifest.CoordinateOriginWgs84.Longitude,
            _manifest.CoordinateOriginWgs84.ElevationMeters
        ));

        _tilesById.Clear();
        _tilesByCoordinate.Clear();
        _states.Clear();

        foreach (PreparedTileRecord tile in _manifest.Tiles)
        {
            _tilesById[tile.Id] = tile;
            _tilesByCoordinate[(tile.X, tile.Y)] = tile;
            _states[tile.Id] = RuntimeTileState.Cold;
        }

        GD.Print($"Loaded tile manifest with {_manifest.Tiles.Count} tiles.");
    }

    private PreparedTileRecord? FindTile(Wgs84Point point)
    {
        if (_manifest is null)
        {
            return null;
        }

        return _manifest.Tiles.FirstOrDefault(tile => tile.BoundsWgs84.Contains(point.Latitude, point.Longitude));
    }

    private HashSet<string> TilesWithinRadius(PreparedTileRecord centerTile, int radius)
    {
        HashSet<string> result = new();

        for (int y = centerTile.Y - radius; y <= centerTile.Y + radius; y += 1)
        {
            for (int x = centerTile.X - radius; x <= centerTile.X + radius; x += 1)
            {
                if (_tilesByCoordinate.TryGetValue((x, y), out PreparedTileRecord? tile))
                {
                    result.Add(tile.Id);
                }
            }
        }

        return result;
    }

    private void SetTileState(string tileId, RuntimeTileState state)
    {
        if (_states.TryGetValue(tileId, out RuntimeTileState existingState) && existingState == state)
        {
            return;
        }

        _states[tileId] = state;

        if (state == RuntimeTileState.Active)
        {
            if (!_activeTileNodes.ContainsKey(tileId) && _tilesById.TryGetValue(tileId, out PreparedTileRecord? tile))
            {
                Node3D tileNode = LoadTileMeshes(tile);
                AddChild(tileNode);
                _activeTileNodes[tileId] = tileNode;
            }
        }
        else
        {
            if (_activeTileNodes.TryGetValue(tileId, out Node3D? tileNode))
            {
                RemoveChild(tileNode);
                tileNode.QueueFree();
                _activeTileNodes.Remove(tileId);
            }
        }

        EmitSignal(SignalName.TileStateChanged, tileId, state.ToString().ToLowerInvariant());
    }

    /// <summary>
    /// Gets a deterministic building color from the palette based on the tile+surface index.
    /// Uses a hash to distribute colors evenly across buildings within a tile.
    /// </summary>
    private static StandardMaterial3D CreateBuildingMaterial(string tileId, int surfaceIndex)
    {
        // Combine tile ID hash with surface index for per-building variation
        int hash = Math.Abs(HashCode.Combine(tileId, surfaceIndex));
        Color color = BuildingPalette[hash % BuildingPalette.Length];

        // Add slight per-building variation to avoid exact palette repetition
        float variation = ((hash >> 8) & 0xFF) / 1024.0f - 0.125f;
        color = new Color(
            Mathf.Clamp(color.R + variation, 0.1f, 1.0f),
            Mathf.Clamp(color.G + variation * 0.8f, 0.1f, 1.0f),
            Mathf.Clamp(color.B + variation * 0.6f, 0.1f, 1.0f)
        );

        return new StandardMaterial3D
        {
            AlbedoColor = color,
            Roughness = 0.65f + ((hash >> 4) & 0xF) / 160.0f // Slight roughness variation
        };
    }

    private Node3D LoadTileMeshes(PreparedTileRecord tile)
    {
        Node3D tileNode = new Node3D();
        tileNode.Name = "Tile_" + tile.Id;

        foreach (var kvp in tile.Files)
        {
            string kind = kvp.Key;
            string relativePath = kvp.Value;

            // Convert path if needed (ensure res:// prefix)
            string resPath = relativePath;
            if (relativePath.StartsWith("godot/"))
            {
                resPath = "res://" + relativePath.Substring("godot/".Length);
            }
            else if (!relativePath.StartsWith("res://"))
            {
                resPath = "res://" + relativePath;
            }

            if (!Godot.FileAccess.FileExists(resPath))
            {
                GD.PushWarning($"Mesh resource file not found at {resPath} for tile {tile.Id}");
                continue;
            }

            Mesh? mesh = GD.Load<Mesh>(resPath);
            if (mesh is null)
            {
                GD.PushError($"Failed to load mesh at {resPath} for tile {tile.Id}");
                continue;
            }

            // Create MeshInstance3D
            MeshInstance3D meshInstance = new MeshInstance3D();
            meshInstance.Mesh = mesh;
            meshInstance.Name = kind;

            // Apply materials based on mesh type
            if (kind == "terrain_mesh")
            {
                if (_terrainShaderMaterial is not null)
                {
                    meshInstance.MaterialOverride = _terrainShaderMaterial;
                }
                else
                {
                    // Fallback to improved StandardMaterial3D
                    meshInstance.MaterialOverride = new StandardMaterial3D
                    {
                        AlbedoColor = new Color(0.55f, 0.48f, 0.38f, 1f),
                        Roughness = 0.9f
                    };
                }
            }
            else if (kind == "roads_mesh")
            {
                int surfaceCount = mesh.GetSurfaceCount();
                if (surfaceCount > 0) meshInstance.SetSurfaceOverrideMaterial(0, _asphaltMat);
                if (surfaceCount > 1) meshInstance.SetSurfaceOverrideMaterial(1, _concreteMat);
                if (surfaceCount > 2) meshInstance.SetSurfaceOverrideMaterial(2, _yellowLineMat);
                if (surfaceCount > 3) meshInstance.SetSurfaceOverrideMaterial(3, _polesMat);
            }
            else if (kind == "buildings_mesh")
            {
                // Apply per-surface (per-building-group) materials for visual variety
                int surfaceCount = mesh.GetSurfaceCount();
                if (surfaceCount <= 1)
                {
                    // Single surface: use tile-hash-based color (legacy behavior, slightly improved)
                    meshInstance.MaterialOverride = CreateBuildingMaterial(tile.Id, 0);
                }
                else
                {
                    // Multiple surfaces: assign different colors per surface
                    for (int i = 0; i < surfaceCount; i += 1)
                    {
                        meshInstance.SetSurfaceOverrideMaterial(i, CreateBuildingMaterial(tile.Id, i));
                    }
                }
            }

            tileNode.AddChild(meshInstance);

            // Create physics body and shape for collision
            StaticBody3D staticBody = new StaticBody3D();
            staticBody.Name = "StaticBody_" + kind;

            CollisionShape3D collisionShape = new CollisionShape3D();
            collisionShape.Name = "CollisionShape";

            ConcavePolygonShape3D shape = mesh.CreateTrimeshShape();
            collisionShape.Shape = shape;

            staticBody.AddChild(collisionShape);
            tileNode.AddChild(staticBody);
        }

        return tileNode;
    }
}
