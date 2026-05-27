using Godot;

namespace TecateSimulator.Resources;

[GlobalClass]
public partial class PlayerNavigationProfile : Resource
{
    [Export]
    public float WalkSpeedMetersPerSecond { get; set; } = 1.4f;

    [Export]
    public float BriskWalkSpeedMetersPerSecond { get; set; } = 2.2f;

    [Export]
    public float EyeHeightMeters { get; set; } = 1.65f;

    [Export]
    public float HorizontalLookSensitivity { get; set; } = 0.12f;

    [Export]
    public float VerticalLookSensitivity { get; set; } = 0.1f;
}

