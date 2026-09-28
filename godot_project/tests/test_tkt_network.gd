extends SceneTree

## Prueba de compatibilidad y verificación binaria para TKTCodec en Godot 4.

func _init():
	print("--- Iniciando verificación binaria de TKTCodec (Godot 4) ---")

	# 1. Prueba de encabezado común
	var hdr = TKTCodec.Header.new()
	hdr.message_type = TKTCodec.MessageType.WELCOME
	hdr.flags = TKTCodec.PacketFlags.RELIABLE
	hdr.session_id = 9876
	hdr.sequence = 12
	hdr.ack = 11
	hdr.timestamp = 54321
	hdr.payload_length = 16
	hdr.payload_checksum = 1234

	var raw_hdr = TKTCodec.encode_header(hdr)
	assert(raw_hdr.size() == 28, "El encabezado TKT/1 debe medir exactamente 28 bytes")

	var dec_hdr = TKTCodec.decode_header(raw_hdr)
	assert(dec_hdr != null, "El encabezado debe decodificarse exitosamente")
	assert(dec_hdr.message_type == TKTCodec.MessageType.WELCOME, "MessageType debe ser WELCOME")
	assert(dec_hdr.session_id == 9876, "SessionID debe coincidir")
	assert(dec_hdr.sequence == 12, "Sequence debe coincidir")
	assert(dec_hdr.timestamp == 54321, "Timestamp debe coincidir")
	print("✓ Cabecera TKT/1 (28 bytes Little-Endian) verificada.")

	# 2. Prueba de HELLO
	var hello_bytes = TKTCodec.encode_hello("1.0.0", "token_abc")
	assert(hello_bytes.size() > 0, "HELLO payload debe tener bytes")
	print("✓ Payload HELLO codificado con éxito (%d bytes)." % hello_bytes.size())

	# 3. Prueba de WELCOME
	var sp_w = StreamPeerBuffer.new()
	sp_w.big_endian = false
	sp_w.put_u32(101)  # session_id
	sp_w.put_u32(5)    # player_entity_id
	sp_w.put_u32(300)  # server_tick
	sp_w.put_u32(9999) # server_time
	var welcome_dict = TKTCodec.decode_welcome(sp_w.data_array)
	assert(welcome_dict["session_id"] == 101, "SessionID debe ser 101")
	assert(welcome_dict["player_entity_id"] == 5, "PlayerID debe ser 5")
	assert(welcome_dict["server_tick"] == 300, "Tick debe ser 300")
	print("✓ Payload WELCOME decodificado con éxito.")

	# 4. Prueba de INPUT
	var inp_bytes = TKTCodec.encode_input(
		45,
		Vector3(-6.684, 400.21, 2.68),
		180.0,
		-10.0,
		Vector3(1.5, 0.0, -2.0),
		5
	)
	assert(inp_bytes.size() == 38, "INPUT payload debe medir exactamente 38 bytes")
	print("✓ Payload INPUT (38 bytes) verificado.")

	# 5. Prueba de SNAPSHOT
	var sp_s = StreamPeerBuffer.new()
	sp_s.big_endian = false
	sp_s.put_u32(50)   # server_tick
	sp_s.put_u32(2000) # server_time
	sp_s.put_u16(1)    # count = 1
	# EntityRecord 38 bytes
	sp_s.put_u32(7)    # entity_id
	sp_s.put_u8(1)     # entity_type
	sp_s.put_u8(1)     # flags
	sp_s.put_float(10.0) # pos.x
	sp_s.put_float(20.0) # pos.y
	sp_s.put_float(30.0) # pos.z
	sp_s.put_float(90.0) # yaw
	sp_s.put_float(0.0)  # pitch
	sp_s.put_float(2.0)  # vel.x
	sp_s.put_float(0.0)  # vel.y
	sp_s.put_float(1.0)  # vel.z

	var snap_dict = TKTCodec.decode_snapshot(sp_s.data_array)
	assert(snap_dict["server_tick"] == 50, "Server tick debe coincidir")
	assert(snap_dict["entities"].size() == 1, "Debe contener 1 entidad")
	var ent: TKTCodec.EntityRecord = snap_dict["entities"][0]
	assert(ent.entity_id == 7, "EntityID debe ser 7")
	assert(is_equal_approx(ent.position.x, 10.0), "Pos.x debe ser 10.0")
	assert(is_equal_approx(ent.yaw, 90.0), "Yaw debe ser 90.0")
	print("✓ Payload SNAPSHOT decodificado con éxito.")

	# 6. Prueba de Checksum y paquete completo
	var chat_bytes = TKTCodec.encode_chat(0, "Prueba TKT")
	var full_pkt = TKTCodec.encode_packet(hdr, chat_bytes)
	assert(full_pkt.size() == 28 + chat_bytes.size(), "Paquete completo debe sumar cabecera + payload")
	print("✓ Paquete completo y cálculo de checksum verificados.")

	# 7. Prueba de EVENT y VEHICLE_ENTER
	var enter_data = TKTCodec.encode_vehicle_enter_data(1001, 1, true)
	assert(enter_data.size() == 6, "VEHICLE_ENTER data debe medir 6 bytes")
	var dec_enter = TKTCodec.decode_vehicle_enter_data(enter_data)
	assert(dec_enter["vehicle_id"] == 1001, "Vehicle ID debe ser 1001")
	assert(dec_enter["seat_index"] == 1, "Seat index debe ser 1")
	assert(dec_enter["role"] == 1, "Role debe ser 1 (conductor)")

	var ev_bytes = TKTCodec.encode_event(55, TKTCodec.EventCode.VEHICLE_ENTER, 10, 8888, enter_data)
	assert(ev_bytes.size() == 16 + 6, "Payload EVENT debe medir 22 bytes")
	var dec_ev = TKTCodec.decode_event(ev_bytes)
	assert(dec_ev["event_id"] == 55, "Event ID debe coincidir")
	assert(dec_ev["event_code"] == TKTCodec.EventCode.VEHICLE_ENTER, "Event code debe ser VEHICLE_ENTER")
	assert(dec_ev["entity_id"] == 10, "Entity ID debe ser 10")
	var inner_enter = TKTCodec.decode_vehicle_enter_data(dec_ev["data"])
	assert(inner_enter["vehicle_id"] == 1001, "Inner vehicle ID debe ser 1001")
	print("✓ Payload EVENT (VEHICLE_ENTER) verificado.")

	# 8. Prueba de VEHICLE_EXIT y VEHICLE_REFUEL
	var exit_data = TKTCodec.encode_vehicle_exit_data(1001, 1)
	assert(exit_data.size() == 5, "VEHICLE_EXIT data debe medir 5 bytes")
	var dec_exit = TKTCodec.decode_vehicle_exit_data(exit_data)
	assert(dec_exit["vehicle_id"] == 1001, "Vehicle ID debe ser 1001")
	assert(dec_exit["seat_index"] == 1, "Seat index debe ser 1")
	print("✓ Payload VEHICLE_EXIT verificado.")

	var refuel_data = TKTCodec.encode_vehicle_refuel_data(1001, 65.5)
	assert(refuel_data.size() == 8, "VEHICLE_REFUEL data debe medir 8 bytes")
	var dec_refuel = TKTCodec.decode_vehicle_refuel_data(refuel_data)
	assert(dec_refuel["vehicle_id"] == 1001, "Vehicle ID debe ser 1001")
	assert(is_equal_approx(dec_refuel["fuel_amount"], 65.5), "Fuel amount debe ser 65.5")
	print("✓ Payload VEHICLE_REFUEL verificado.")

	# 9. Prueba de SNAPSHOT con entidad de tipo VEHICLE
	var sp_v = StreamPeerBuffer.new()
	sp_v.big_endian = false
	sp_v.put_u32(60)   # server_tick
	sp_v.put_u32(3000) # server_time
	sp_v.put_u16(1)    # count = 1
	sp_v.put_u32(1002) # entity_id
	sp_v.put_u8(TKTCodec.EntityType.VEHICLE) # entity_type = 2
	sp_v.put_u8(TKTCodec.VehicleFlags.ROUTE_VEHICLE) # flags
	sp_v.put_float(50.0) # pos.x
	sp_v.put_float(400.0) # pos.y
	sp_v.put_float(-20.0) # pos.z
	sp_v.put_float(180.0) # yaw
	sp_v.put_float(-4.0) # pitch
	sp_v.put_float(10.0) # vel.x
	sp_v.put_float(0.0) # vel.y
	sp_v.put_float(0.0) # vel.z

	var snap_v = TKTCodec.decode_snapshot(sp_v.data_array)
	assert(snap_v["entities"].size() == 1, "Snapshot debe contener 1 entidad")
	var v_rec: TKTCodec.EntityRecord = snap_v["entities"][0]
	assert(v_rec.entity_id == 1002, "Entity ID debe ser 1002")
	assert(v_rec.entity_type == TKTCodec.EntityType.VEHICLE, "Entity type debe ser VEHICLE")
	assert((v_rec.flags & TKTCodec.VehicleFlags.ROUTE_VEHICLE) != 0, "Debe tener flag ROUTE_VEHICLE")
	assert(is_equal_approx(v_rec.pitch, -4.0), "Pitch topográfico debe ser -4.0")
	print("✓ Payload SNAPSHOT con EntityType.VEHICLE verificado.")

	print("=== TODAS LAS PRUEBAS DE TKT_CODEC EN GODOT COMPLETADAS EXITOSAMENTE ===")
	quit(0)

