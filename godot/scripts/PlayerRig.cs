using Godot;

namespace TecateSimulator.Scripts;

[GlobalClass]
public partial class PlayerRig : CharacterBody3D
{
    [Export]
    public float Speed { get; set; } = 4.0f; // Human walking scale (~14 km/h max walking speed)

    [Export]
    public float MouseSensitivity { get; set; } = 0.002f;

    private Marker3D _eye = null!;
    private float _rotationX = 0f;
    private float _gravity = ProjectSettings.GetSetting("physics/3d/default_gravity").AsSingle();

    public override void _Ready()
    {
        _eye = GetNode<Marker3D>("Eye");
        Input.MouseMode = Input.MouseModeEnum.Captured;
    }

    public override void _Input(InputEvent @event)
    {
        if (@event is InputEventMouseMotion mouseMotion && Input.MouseMode == Input.MouseModeEnum.Captured)
        {
            // Rotate horizontally (around Y axis)
            RotateY(-mouseMotion.Relative.X * MouseSensitivity);

            // Rotate vertically (around X axis of the eye)
            _rotationX -= mouseMotion.Relative.Y * MouseSensitivity;
            _rotationX = Mathf.Clamp(_rotationX, -Mathf.Pi / 2.2f, Mathf.Pi / 2.2f);
            
            Vector3 eyeRot = _eye.Rotation;
            eyeRot.X = _rotationX;
            _eye.Rotation = eyeRot;
        }

        // Release mouse control with Escape key
        if (Input.IsKeyPressed(Key.Escape))
        {
            Input.MouseMode = Input.MouseModeEnum.Visible;
        }

        // Re-capture mouse on clicking inside screen
        if (@event is InputEventMouseButton mouseButton && mouseButton.Pressed && mouseButton.ButtonIndex == MouseButton.Left)
        {
            Input.MouseMode = Input.MouseModeEnum.Captured;
        }
    }

    public override void _PhysicsProcess(double delta)
    {
        Vector3 velocity = Velocity;

        // Apply gravity if not standing on the ground
        if (!IsOnFloor())
        {
            velocity.Y -= _gravity * (float)delta;
        }

        // Handle walking movement
        Vector2 inputDir = Vector2.Zero;

        if (Input.IsKeyPressed(Key.W))
        {
            inputDir.Y -= 1f;
        }
        if (Input.IsKeyPressed(Key.S))
        {
            inputDir.Y += 1f;
        }
        if (Input.IsKeyPressed(Key.A))
        {
            inputDir.X -= 1f;
        }
        if (Input.IsKeyPressed(Key.D))
        {
            inputDir.X += 1f;
        }

        inputDir = inputDir.Normalized();

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
