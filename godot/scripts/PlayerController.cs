using Godot;

namespace TecateSimulator.Scripts;

public partial class PlayerController : CharacterBody3D
{
    [Export]
    public float Speed { get; set; } = 5.0f;

    [Export]
    public float MouseSensitivity { get; set; } = 0.002f;

    [Export]
    public float Gravity { get; set; } = 20.0f;

    private Marker3D? _eye;
    private Camera3D? _camera;
    private float _rotationX = 0f;

    public override void _Ready()
    {
        _eye = GetNodeOrNull<Marker3D>("Eye");
        if (_eye is not null)
        {
            _camera = _eye.GetNodeOrNull<Camera3D>("Camera3D");
            if (_camera is not null)
            {
                _camera.Current = true;
            }
        }

        // Capture the mouse cursor
        Input.MouseMode = Input.MouseModeEnum.Captured;
    }

    public override void _Input(InputEvent @event)
    {
        // Handle mouse look
        if (@event is InputEventMouseMotion mouseMotion && Input.MouseMode == Input.MouseModeEnum.Captured)
        {
            // Rotate character horizontally
            RotateY(-mouseMotion.Relative.X * MouseSensitivity);

            // Rotate camera vertically
            if (_eye is not null)
            {
                _rotationX -= mouseMotion.Relative.Y * MouseSensitivity;
                _rotationX = Mathf.Clamp(_rotationX, -Mathf.Pi / 2.2f, Mathf.Pi / 2.2f);
                _eye.Rotation = new Vector3(_rotationX, _eye.Rotation.Y, _eye.Rotation.Z);
            }
        }

        // Toggle mouse capture with UI cancel action (typically Escape)
        if (@event.IsActionPressed("ui_cancel"))
        {
            if (Input.MouseMode == Input.MouseModeEnum.Captured)
            {
                Input.MouseMode = Input.MouseModeEnum.Visible;
            }
            else
            {
                Input.MouseMode = Input.MouseModeEnum.Captured;
            }
        }
    }

    public override void _PhysicsProcess(double delta)
    {
        Vector3 velocity = Velocity;

        // Add gravity if not on floor
        if (!IsOnFloor())
        {
            velocity.Y -= Gravity * (float)delta;
        }

        // Get movement input direction relative to character rotation
        Vector2 inputDir = Input.GetVector("ui_left", "ui_right", "ui_up", "ui_down");
        Vector3 direction = (Transform.Basis * new Vector3(inputDir.X, 0, inputDir.Y)).Normalized();

        if (direction != Vector3.Zero)
        {
            velocity.X = direction.X * Speed;
            velocity.Z = direction.Z * Speed;
        }
        else
        {
            velocity.X = Mathf.MoveToward(Velocity.X, 0, Speed);
            velocity.Z = Mathf.MoveToward(Velocity.Z, 0, Speed);
        }

        Velocity = velocity;
        MoveAndSlide();
    }
}
