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
    public int ActiveRadiusTiles { get; set; } = 5; // Radical streaming expansion to keep all tiles loaded

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

    public override void _Ready()
    {
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

    private Node3D LoadTileMeshes(PreparedTileRecord tile)
    {
        Node3D tileNode = new Node3D();
        tileNode.Name = "Tile_" + tile.Id;

        // Custom materials for a beautiful, premium, and recognizable Mexican aesthetic
        StandardMaterial3D terrainMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.35f, 0.45f, 0.32f, 1f), // soft semi-arid green-brown
            Roughness = 0.9f
        };

        StandardMaterial3D asphaltMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.18f, 0.19f, 0.22f, 1f), // dark slate road
            Roughness = 0.8f
        };

        StandardMaterial3D concreteMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.68f, 0.70f, 0.72f, 1f), // concrete sidewalk grey
            Roughness = 0.7f
        };

        StandardMaterial3D yellowLineMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.85f, 0.75f, 0.15f, 1f), // bright yellow lane divider
            Roughness = 0.6f
        };

        StandardMaterial3D polesMat = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.55f, 0.56f, 0.58f, 1f), // concrete pole shade
            Roughness = 0.8f
        };

        // Vibrant Mexican architectural pastel palette for district spatial recognition
        Color[] bldColors = new Color[]
        {
            new Color(0.72f, 0.41f, 0.30f, 1f), // Warm Terracotta
            new Color(0.85f, 0.68f, 0.38f, 1f), // Pale Gold/Ochre
            new Color(0.40f, 0.65f, 0.68f, 1f), // Soft Turquoise
            new Color(0.90f, 0.88f, 0.84f, 1f), // Plaster White
            new Color(0.80f, 0.76f, 0.68f, 1f), // Sandy Beige
            new Color(0.78f, 0.55f, 0.62f, 1f), // Faded Rose
        };

        int bldHash = Math.Abs(tile.Id.GetHashCode());
        StandardMaterial3D buildingsMat = new StandardMaterial3D
        {
            AlbedoColor = bldColors[bldHash % bldColors.Length],
            Roughness = 0.65f
        };

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

            // Apply specific premium materials
            if (kind == "terrain_mesh")
            {
                meshInstance.MaterialOverride = terrainMat;
            }
            else if (kind == "roads_mesh")
            {
                int surfaceCount = mesh.GetSurfaceCount();
                if (surfaceCount > 0) meshInstance.SetSurfaceOverrideMaterial(0, asphaltMat);
                if (surfaceCount > 1) meshInstance.SetSurfaceOverrideMaterial(1, concreteMat);
                if (surfaceCount > 2) meshInstance.SetSurfaceOverrideMaterial(2, yellowLineMat);
                if (surfaceCount > 3) meshInstance.SetSurfaceOverrideMaterial(3, polesMat);
            }
            else if (kind == "buildings_mesh")
            {
                meshInstance.MaterialOverride = buildingsMat;
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
