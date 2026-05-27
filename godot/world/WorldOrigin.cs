using Godot;

namespace TecateSimulator.World;

[GlobalClass]
public partial class WorldOrigin : Resource
{
    private const double EarthRadiusMeters = 6378137.0;

    [Export]
    public double Latitude { get; set; } = 32.5668;

    [Export]
    public double Longitude { get; set; } = -116.6253;

    [Export]
    public double ElevationMeters { get; set; } = 540.0;

    public Wgs84Point LocalMetersToWgs84(Vector3 localPosition)
    {
        (double originX, double originY) = LonLatToWebMercator(Longitude, Latitude);
        double x = originX + localPosition.X;
        double y = originY - localPosition.Z;
        (double longitude, double latitude) = WebMercatorToLonLat(x, y);
        return new Wgs84Point(latitude, longitude);
    }

    public Vector3 Wgs84ToLocalMeters(Wgs84Point point)
    {
        (double originX, double originY) = LonLatToWebMercator(Longitude, Latitude);
        (double pointX, double pointY) = LonLatToWebMercator(point.Longitude, point.Latitude);
        return new Vector3((float)(pointX - originX), 0f, (float)-(pointY - originY));
    }

    public static WorldOrigin FromCoordinateOrigin(CoordinateOrigin coordinateOrigin)
    {
        return new WorldOrigin
        {
            Latitude = coordinateOrigin.Latitude,
            Longitude = coordinateOrigin.Longitude,
            ElevationMeters = coordinateOrigin.ElevationMeters
        };
    }

    private static (double X, double Y) LonLatToWebMercator(double longitude, double latitude)
    {
        double longitudeRadians = DegreesToRadians(longitude);
        double latitudeRadians = DegreesToRadians(latitude);
        double x = EarthRadiusMeters * longitudeRadians;
        double y = EarthRadiusMeters * System.Math.Log(System.Math.Tan(System.Math.PI / 4.0 + latitudeRadians / 2.0));
        return (x, y);
    }

    private static (double Longitude, double Latitude) WebMercatorToLonLat(double x, double y)
    {
        double longitude = RadiansToDegrees(x / EarthRadiusMeters);
        double latitude = RadiansToDegrees(2.0 * System.Math.Atan(System.Math.Exp(y / EarthRadiusMeters)) - System.Math.PI / 2.0);
        return (longitude, latitude);
    }

    private static double DegreesToRadians(double degrees)
    {
        return degrees * System.Math.PI / 180.0;
    }

    private static double RadiansToDegrees(double radians)
    {
        return radians * 180.0 / System.Math.PI;
    }
}

public readonly record struct Wgs84Point(double Latitude, double Longitude);

public readonly record struct CoordinateOrigin(double Latitude, double Longitude, double ElevationMeters);
