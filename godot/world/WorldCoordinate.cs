using Godot;

namespace TecateSimulator.World;

public readonly record struct WorldCoordinate(double EastMeters, double UpMeters, double SouthMeters)
{
	public Vector3 ToVector3()
	{
		return new Vector3((float)EastMeters, (float)UpMeters, (float)SouthMeters);
	}

	public static WorldCoordinate FromVector3(Vector3 value)
	{
		return new WorldCoordinate(value.X, value.Y, value.Z);
	}
}
