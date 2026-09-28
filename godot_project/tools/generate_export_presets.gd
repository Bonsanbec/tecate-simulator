## Script temporal para generar export_presets.cfg con los presets
## Android e iOS correctamente formateados.
## Uso: godot-mono --headless --path . --script res://tools/generate_export_presets.gd --quit
@tool
extends SceneTree

func _init() -> void:
	var cfg := ConfigFile.new()

	# ─── preset.0 : Android ─────────────────────────────────────────
	cfg.set_value("preset.0", "name", "Android")
	cfg.set_value("preset.0", "platform", "Android")
	cfg.set_value("preset.0", "runnable", true)
	cfg.set_value("preset.0", "dedicated_server", false)
	cfg.set_value("preset.0", "custom_features", "")
	cfg.set_value("preset.0", "export_filter", "all_resources")
	cfg.set_value("preset.0", "include_filter", "")
	cfg.set_value("preset.0", "exclude_filter", "")
	cfg.set_value("preset.0", "export_path", "build/android/tecate.apk")
	cfg.set_value("preset.0", "encryption_include_filters", "")
	cfg.set_value("preset.0", "encryption_exclude_filters", "")
	cfg.set_value("preset.0", "encrypt_pck", false)
	cfg.set_value("preset.0", "encrypt_directory", false)

	cfg.set_value("preset.0.options", "custom_template/debug", "")
	cfg.set_value("preset.0.options", "custom_template/release", "")
	cfg.set_value("preset.0.options", "gradle_build/use_gradle_build", false)
	cfg.set_value("preset.0.options", "gradle_build/export_format", 0)
	cfg.set_value("preset.0.options", "architectures/armeabi-v7a", false)
	cfg.set_value("preset.0.options", "architectures/arm64-v8a", true)
	cfg.set_value("preset.0.options", "architectures/x86", false)
	cfg.set_value("preset.0.options", "architectures/x86_64", false)
	cfg.set_value("preset.0.options", "version/code", 1)
	cfg.set_value("preset.0.options", "version/name", "1.0.0")
	cfg.set_value("preset.0.options", "package/unique_name", "dev.bonsanbec.tecate")
	cfg.set_value("preset.0.options", "package/name", "Tecate Simulator")
	cfg.set_value("preset.0.options", "screen/immersive_mode", true)
	cfg.set_value("preset.0.options", "keystore/debug", "")
	cfg.set_value("preset.0.options", "keystore/debug_user", "")
	cfg.set_value("preset.0.options", "keystore/debug_password", "")
	cfg.set_value("preset.0.options", "keystore/release", "")
	cfg.set_value("preset.0.options", "keystore/release_user", "")
	cfg.set_value("preset.0.options", "keystore/release_password", "")

	# ─── preset.1 : iOS ─────────────────────────────────────────────
	cfg.set_value("preset.1", "name", "iOS")
	cfg.set_value("preset.1", "platform", "iOS")
	cfg.set_value("preset.1", "runnable", true)
	cfg.set_value("preset.1", "dedicated_server", false)
	cfg.set_value("preset.1", "custom_features", "")
	cfg.set_value("preset.1", "export_filter", "all_resources")
	cfg.set_value("preset.1", "include_filter", "")
	cfg.set_value("preset.1", "exclude_filter", "")
	cfg.set_value("preset.1", "export_path", "build/ios/tecate.xcodeproj")
	cfg.set_value("preset.1", "encryption_include_filters", "")
	cfg.set_value("preset.1", "encryption_exclude_filters", "")
	cfg.set_value("preset.1", "encrypt_pck", false)
	cfg.set_value("preset.1", "encrypt_directory", false)

	cfg.set_value("preset.1.options", "custom_template/debug", "")
	cfg.set_value("preset.1.options", "custom_template/release", "")
	cfg.set_value("preset.1.options", "application/bundle_identifier", "dev.bonsanbec.tecate")
	cfg.set_value("preset.1.options", "application/short_version", "1.0")
	cfg.set_value("preset.1.options", "application/version", "1")
	cfg.set_value("preset.1.options", "application/app_store_team_id", "")
	cfg.set_value("preset.1.options", "application/code_sign_identity_debug", "iPhone Developer")
	cfg.set_value("preset.1.options", "application/code_sign_identity_release", "iPhone Distribution")

	var err := cfg.save("res://export_presets.cfg")
	if err == OK:
		print("✅ export_presets.cfg generado correctamente.")
	else:
		printerr("❌ Error al guardar export_presets.cfg: ", err)

	quit()
