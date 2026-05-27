# Development Environment

## Installed Tooling

The local development environment uses:

- Node.js 24.x and npm 11.x for TypeScript tooling.
- TypeScript, tsx, and Node type definitions installed as project dev dependencies.
- .NET SDK 8.0.421 installed under the user profile at `/Users/hakkindavid/.dotnet`.
- `dotnet` linked from `/opt/homebrew/bin/dotnet`.
- Godot .NET 4.6.3 installed as `/Applications/Godot_mono.app`.
- Godot CLI available as `godot-mono`.
- GDAL 3.13.0 for GIS and raster/vector conversion.
- PROJ 9.8.1 for coordinate operations.
- Git through Homebrew/system tooling.

## Version Pinning

The repository pins the .NET SDK through `global.json`.

Godot C# packages are restored through `godot/TecateSimulator.csproj`. If the installed Godot editor version changes, verify that the Godot .NET SDK package used by the project still compiles before changing runtime code.

## Verification Commands

Run these commands from the repository root:

```sh
npm run typecheck
npm run validate
godot-mono --headless --path godot --quit
```

Run this command from `godot/`:

```sh
dotnet build TecateSimulator.csproj --no-restore
```

## Notes

The Homebrew `godot-mono` cask declares a `dotnet-sdk` cask dependency that may require `sudo` on macOS. This environment uses a user-profile .NET installation instead, which is sufficient for project restore and compilation.

