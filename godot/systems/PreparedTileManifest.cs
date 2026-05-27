using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace TecateSimulator.Systems;

public sealed class PreparedTileManifest
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } = string.Empty;

    [JsonPropertyName("projectId")]
    public string ProjectId { get; set; } = string.Empty;

    [JsonPropertyName("generatedBy")]
    public string GeneratedBy { get; set; } = string.Empty;

    [JsonPropertyName("generatedAt")]
    public string GeneratedAt { get; set; } = string.Empty;

    [JsonPropertyName("coordinateOriginWgs84")]
    public CoordinateOriginData CoordinateOriginWgs84 { get; set; } = new();

    [JsonPropertyName("zoom")]
    public int Zoom { get; set; }

    [JsonPropertyName("tiles")]
    public List<PreparedTileRecord> Tiles { get; set; } = new();
}

public sealed class CoordinateOriginData
{
    [JsonPropertyName("latitude")]
    public double Latitude { get; set; }

    [JsonPropertyName("longitude")]
    public double Longitude { get; set; }

    [JsonPropertyName("elevationMeters")]
    public double ElevationMeters { get; set; }
}

public sealed class PreparedTileRecord
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("x")]
    public int X { get; set; }

    [JsonPropertyName("y")]
    public int Y { get; set; }

    [JsonPropertyName("z")]
    public int Z { get; set; }

    [JsonPropertyName("boundsWgs84")]
    public Wgs84BoundsData BoundsWgs84 { get; set; } = new();

    [JsonPropertyName("state")]
    public string State { get; set; } = "planned";

    [JsonPropertyName("corridorIds")]
    public List<string> CorridorIds { get; set; } = new();

    [JsonPropertyName("files")]
    public Dictionary<string, string> Files { get; set; } = new();
}

public sealed class Wgs84BoundsData
{
    [JsonPropertyName("west")]
    public double West { get; set; }

    [JsonPropertyName("south")]
    public double South { get; set; }

    [JsonPropertyName("east")]
    public double East { get; set; }

    [JsonPropertyName("north")]
    public double North { get; set; }

    public bool Contains(double latitude, double longitude)
    {
        return longitude >= West && longitude <= East && latitude >= South && latitude <= North;
    }
}

