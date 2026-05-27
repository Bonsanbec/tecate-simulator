using Godot;
using TecateSimulator.Systems;

namespace TecateSimulator.Scripts;

public partial class GameBootstrap : Node3D
{
    public override void _Ready()
    {
        TileStreamingSystem? streamingSystem = GetNodeOrNull<TileStreamingSystem>("WorldRoot/TileStreamingSystem");

        if (streamingSystem is null)
        {
            GD.PushWarning("TileStreamingSystem is not present under WorldRoot.");
            return;
        }

        GD.Print("Tecate runtime scaffold ready. Runtime expects prepared offline tile manifests.");
    }
}

