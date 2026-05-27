using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Godot;

namespace TecateSimulator.Systems;

public partial class TileMeshLoader : Node3D
{
    [Export]
    public NodePath TileStreamingSystemPath { get; set; } = "../TileStreamingSystem";

    private TileStreamingSystem? _streamingSystem;
    private readonly Dictionary<string, Node3D> _loadedTileNodes = new();
    private string _workspaceRoot = "";

    // Materials
    private StandardMaterial3D? _terrainMaterial;
    private StandardMaterial3D? _roadMaterial;
    private StandardMaterial3D? _buildingMaterial;

    public class JsonMeshData
    {
        public float[] Vertices { get; set; } = Array.Empty<float>();
        public int[] Indices { get; set; } = Array.Empty<int>();
    }

    public override void _Ready()
    {
        // Resolve workspace root directory (one level up from the 'godot' project directory)
        string resPath = ProjectSettings.GlobalizePath("res://");
        _workspaceRoot = Directory.GetParent(resPath.TrimEnd('/', '\\'))?.FullName ?? resPath;
        GD.Print($"[TileMeshLoader] Resolved workspace root: {_workspaceRoot}");

        // Initialize materials
        InitMaterials();

        // Connect to streaming system
        if (!string.IsNullOrEmpty(TileStreamingSystemPath.ToString()))
        {
            _streamingSystem = GetNodeOrNull<TileStreamingSystem>(TileStreamingSystemPath);
        }

        if (_streamingSystem is not null)
        {
            _streamingSystem.TileStateChanged += OnTileStateChanged;
            GD.Print("[TileMeshLoader] Connected to TileStreamingSystem.");
        }
        else
        {
            GD.PushError("[TileMeshLoader] TileStreamingSystem not found!");
        }
    }

    private void InitMaterials()
    {
        // Earthy, warm Tecate desert terrain
        _terrainMaterial = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.76f, 0.70f, 0.58f), // Sandy dust
            Roughness = 0.9f,
            Metallic = 0.0f
        };

        // Dark road asphalt
        _roadMaterial = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.18f, 0.18f, 0.18f), // Off-black asphalt
            Roughness = 0.8f,
            Metallic = 0.05f
        };

        // Pastel stucco building facades (classic Mexican urban style)
        _buildingMaterial = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.88f, 0.84f, 0.76f), // Light beige concrete/stucco
            Roughness = 0.7f,
            Metallic = 0.0f
        };
    }

    private void OnTileStateChanged(string tileId, string state)
    {
        if (state == "active")
        {
            LoadTileMeshes(tileId);
        }
        else if (state == "cold" || state == "warm")
        {
            UnloadTileMeshes(tileId);
        }
    }

    private void LoadTileMeshes(string tileId)
    {
        if (_streamingSystem is null) return;
        if (_loadedTileNodes.ContainsKey(tileId)) return; // Already loaded

        // Retrieve tile record
        PreparedTileRecord? tileRecord = null;
        if (_streamingSystem.Manifest?.Tiles is not null)
        {
            tileRecord = _streamingSystem.Manifest.Tiles.Find(t => t.Id == tileId);
        }

        if (tileRecord is null || tileRecord.Files is null || tileRecord.Files.Count == 0)
        {
            return;
        }

        GD.Print($"[TileMeshLoader] Loading meshes for active tile: {tileId}");

        // Create container node for this tile's geometry
        Node3D tileContainer = new() { Name = tileId };
        AddChild(tileContainer);
        _loadedTileNodes[tileId] = tileContainer;

        foreach (var filePair in tileRecord.Files)
        {
            string kind = filePair.Key;
            string relativePath = filePair.Value;

            string absolutePath = Path.Combine(_workspaceRoot, relativePath);
            if (!File.Exists(absolutePath))
            {
                GD.PushWarning($"[TileMeshLoader] Mesh file not found at: {absolutePath}");
                continue;
            }

            try
            {
                string json = File.ReadAllText(absolutePath);
                JsonMeshData? meshData = JsonSerializer.Deserialize<JsonMeshData>(json, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                if (meshData is null || meshData.Vertices.Length == 0 || meshData.Indices.Length == 0)
                {
                    GD.PushWarning($"[TileMeshLoader] Empty or invalid mesh data in: {relativePath}");
                    continue;
                }

                // Create mesh node
                CreateMeshNode(tileContainer, meshData, kind);
            }
            catch (Exception ex)
            {
                GD.PushError($"[TileMeshLoader] Failed to load mesh '{kind}' for tile '{tileId}': {ex.Message}");
            }
        }
    }

    private void CreateMeshNode(Node3D parent, JsonMeshData data, string kind)
    {
        // 1. Prepare vectors and indices
        Vector3[] vertices = new Vector3[data.Vertices.Length / 3];
        for (int i = 0; i < vertices.Length; i++)
        {
            vertices[i] = new Vector3(data.Vertices[i * 3], data.Vertices[i * 3 + 1], data.Vertices[i * 3 + 2]);
        }

        int[] indices = data.Indices;

        // 2. Build the mesh using SurfaceTool to automatically generate smooth normals and tangents
        SurfaceTool st = new();
        st.Begin(Mesh.PrimitiveType.Triangles);
        
        for (int i = 0; i < vertices.Length; i++)
        {
            st.AddVertex(vertices[i]);
        }
        for (int i = 0; i < indices.Length; i++)
        {
            st.AddIndex(indices[i]);
        }

        st.GenerateNormals();

        ArrayMesh arrayMesh = st.Commit();

        // 3. Create MeshInstance3D
        MeshInstance3D meshInstance = new()
        {
            Mesh = arrayMesh,
            Name = $"{kind}_mesh"
        };

        // Assign correct material
        switch (kind.ToLowerInvariant())
        {
            case "terrain":
                meshInstance.MaterialOverride = _terrainMaterial;
                break;
            case "roads":
                meshInstance.MaterialOverride = _roadMaterial;
                break;
            case "buildings":
                meshInstance.MaterialOverride = _buildingMaterial;
                break;
            default:
                meshInstance.MaterialOverride = _buildingMaterial;
                break;
        }

        parent.AddChild(meshInstance);

        // 4. Create collision shapes so the player can walk on the terrain and collide with buildings
        StaticBody3D staticBody = new() { Name = $"{kind}_collision_body" };
        meshInstance.AddChild(staticBody);

        ConcavePolygonShape3D collisionShape = arrayMesh.CreateTrimeshShape();
        
        CollisionShape3D shapeNode = new()
        {
            Shape = collisionShape,
            Name = $"{kind}_collision_shape"
        };
        staticBody.AddChild(shapeNode);
    }

    private void UnloadTileMeshes(string tileId)
    {
        if (_loadedTileNodes.TryGetValue(tileId, out Node3D? tileContainer))
        {
            GD.Print($"[TileMeshLoader] Unloading meshes for cold tile: {tileId}");
            tileContainer.QueueFree();
            _loadedTileNodes.Remove(tileId);
        }
    }
}
