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
    public int ActiveRadiusTiles { get; set; } = 1;

    [Export]
    public int WarmRadiusTiles { get; set; } = 2;

    [Export]
    public WorldOrigin? OriginOverride { get; set; }

    private readonly Dictionary<string, PreparedTileRecord> _tilesById = new();
    private readonly Dictionary<(int X, int Y), PreparedTileRecord> _tilesByCoordinate = new();
    private readonly Dictionary<string, RuntimeTileState> _states = new();
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
        EmitSignal(SignalName.TileStateChanged, tileId, state.ToString().ToLowerInvariant());
    }
}
