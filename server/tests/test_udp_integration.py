"""Prueba de integración end-to-end para el despachador y protocolo TKT/1 en entorno aislado."""

import unittest
from server.config import ServerConfig
from server.core.entity import DynamicEntity
from server.network.udp_server import TKTGameServer
from server.protocol.codec import (
    EventPayload,
    HelloPayload,
    InputPayload,
    PacketHeader,
    PingPongPayload,
    SnapshotPayload,
    WelcomePayload,
    decode_packet,
    encode_packet,
)
from server.protocol.constants import EntityType, EventCode, MessageType, PacketFlags, PlayerFlags, VehicleFlags



class MockDatagramTransport:
    """Transporte simulado en memoria para pruebas sin requerir sockets de red del SO."""

    def __init__(self) -> None:
        self.sent_packets: list[tuple[bytes, tuple[str, int]]] = []
        self._closing = False

    def sendto(self, data: bytes, addr: tuple[str, int]) -> None:
        self.sent_packets.append((data, addr))

    def is_closing(self) -> bool:
        return self._closing

    def close(self) -> None:
        self._closing = True


class TestUDPProtocolIntegration(unittest.TestCase):
    def setUp(self):
        self.config = ServerConfig({
            "SERVER_BIND_HOST": "127.0.0.1",
            "SERVER_PORT": "52665",
            "TICK_RATE": "30",
        })
        self.server = TKTGameServer(self.config)
        self.mock_transport = MockDatagramTransport()
        self.server.transport = self.mock_transport  # type: ignore[assignment]
        self.client_addr = ("192.168.1.100", 61234)

    def test_full_client_lifecycle_simulated(self):
        # 1. Simular datagrama HELLO
        hello = HelloPayload(client_version="1.0.0", auth_token="tok_123")
        hello_hdr = PacketHeader(message_type=MessageType.HELLO, sequence=1)
        hello_bytes = encode_packet(hello_hdr, hello.pack())

        self.server.handle_packet(hello_hdr, hello.pack(), self.client_addr)

        # 2. Verificar que el servidor envió WELCOME
        self.assertEqual(len(self.mock_transport.sent_packets), 1)
        sent_data, dest_addr = self.mock_transport.sent_packets[0]
        self.assertEqual(dest_addr, self.client_addr)

        hdr, payload = decode_packet(sent_data)
        self.assertEqual(hdr.message_type, MessageType.WELCOME)
        welcome = WelcomePayload.unpack(payload)
        self.assertGreater(welcome.session_id, 0)
        self.assertGreater(welcome.player_entity_id, 0)
        session_id = welcome.session_id
        player_id = welcome.player_entity_id

        # 3. Simular INPUT de movimiento
        inp = InputPayload(
            tick=10,
            pos_x=-6.684,
            pos_y=400.21,
            pos_z=2.68,
            yaw=90.0,
            pitch=0.0,
            vel_x=2.0,
            vel_y=0.0,
            vel_z=0.0,
            flags=1,
        )
        inp_hdr = PacketHeader(
            message_type=MessageType.INPUT,
            session_id=session_id,
            sequence=2,
        )
        self.server.handle_packet(inp_hdr, inp.pack(), self.client_addr)

        # Verificar que el estado del jugador se reflejó en el mundo
        entity = self.server.world.get_entity(player_id)
        self.assertIsNotNone(entity)
        self.assertAlmostEqual(entity.pos_x, -6.684, places=2)
        self.assertAlmostEqual(entity.yaw, 90.0, places=1)

        # 4. Simular PING
        ping = PingPongPayload(ping_id=42, timestamp=5000)
        ping_hdr = PacketHeader(
            message_type=MessageType.PING,
            session_id=session_id,
            sequence=3,
        )
        self.server.handle_packet(ping_hdr, ping.pack(), self.client_addr)

        # Verificar que se envió PONG
        self.assertEqual(len(self.mock_transport.sent_packets), 2)
        pong_data, _ = self.mock_transport.sent_packets[1]
        hdr_pong, payload_pong = decode_packet(pong_data)
        self.assertEqual(hdr_pong.message_type, MessageType.PONG)
        pong = PingPongPayload.unpack(payload_pong)
        self.assertEqual(pong.ping_id, 42)

        # 5. Generar SNAPSHOT para un segundo jugador y verificar presencia de la entidad jugador y vehículos
        client2_addr = ("192.168.1.101", 61235)
        s2 = self.server.session_manager.create_or_renew_session(client2_addr)
        snap = self.server.world.build_snapshot_for_player(s2.player_entity_id, 1, 100)
        # Snapshot debe contener el jugador 1 + 2 vehículos por defecto (1001 y 1002)
        self.assertGreaterEqual(len(snap.entities), 3)
        entity_ids = {e.entity_id: e for e in snap.entities}
        self.assertIn(player_id, entity_ids)
        self.assertIn(1001, entity_ids)
        self.assertIn(2001, entity_ids)
        self.assertEqual(entity_ids[1001].entity_type, EntityType.VEHICLE)
        self.assertEqual(entity_ids[2001].entity_type, EntityType.VEHICLE)

        # 6. Simular EVENT de abordaje a vehículo (VEHICLE_ENTER) como conductor
        import struct
        enter_payload = EventPayload(
            event_id=1,
            event_code=EventCode.VEHICLE_ENTER,
            entity_id=player_id,
            timestamp=6000,
            data=struct.pack("<IBB", 1001, 0, 1), # vehicle 1001, seat 0, driver
        )
        enter_hdr = PacketHeader(
            message_type=MessageType.EVENT,
            session_id=session_id,
            sequence=4,
        )
        self.server.handle_packet(enter_hdr, enter_payload.pack(), self.client_addr)

        # Verificar que el vehículo 1001 ahora tiene a player_id como conductor
        v1001 = self.server.world.get_entity(1001)
        self.assertIsNotNone(v1001)
        self.assertEqual(v1001.driver_id, player_id)
        self.assertTrue(v1001.flags & VehicleFlags.HAS_DRIVER)

        # Verificar que el segundo cliente recibió la retransmisión del evento fiable
        # Buscamos paquetes enviados a client2_addr
        c2_packets = [pkt for pkt in self.mock_transport.sent_packets if pkt[1] == client2_addr]
        self.assertGreaterEqual(len(c2_packets), 1)
        c2_hdr, c2_payload = decode_packet(c2_packets[-1][0])
        self.assertEqual(c2_hdr.message_type, MessageType.EVENT)
        c2_event = EventPayload.unpack(c2_payload)
        self.assertEqual(c2_event.event_code, EventCode.VEHICLE_ENTER)
        v_id, seat, role = c2_event.unpack_vehicle_enter()
        self.assertEqual(v_id, 1001)
        self.assertEqual(role, 1)

        # 7. Simular INPUT de conducción y verificar que la cinemática del vehículo se actualiza
        drive_inp = InputPayload(
            tick=20,
            pos_x=15.5,
            pos_y=400.1,
            pos_z=30.0,
            yaw=45.0,
            pitch=-3.5,
            vel_x=12.0,
            vel_y=0.0,
            vel_z=10.0,
            flags=(PlayerFlags.IN_VEHICLE | PlayerFlags.DRIVING_VEHICLE),
        )
        drive_hdr = PacketHeader(
            message_type=MessageType.INPUT,
            session_id=session_id,
            sequence=5,
        )
        self.server.handle_packet(drive_hdr, drive_inp.pack(), self.client_addr)

        # El vehículo 1001 debe haber adoptado la posición y orientación de la cinemática
        self.assertAlmostEqual(v1001.pos_x, 15.5, places=1)
        self.assertAlmostEqual(v1001.yaw, 45.0, places=1)
        self.assertAlmostEqual(v1001.pitch, -3.5, places=1)
        self.assertAlmostEqual(v1001.vel_x, 12.0, places=1)

        # 8. Simular EVENT de descenso (VEHICLE_EXIT)
        exit_payload = EventPayload(
            event_id=2,
            event_code=EventCode.VEHICLE_EXIT,
            entity_id=player_id,
            timestamp=7000,
            data=struct.pack("<IB", 1001, 0),
        )
        exit_hdr = PacketHeader(
            message_type=MessageType.EVENT,
            session_id=session_id,
            sequence=6,
        )
        self.server.handle_packet(exit_hdr, exit_payload.pack(), self.client_addr)
        self.assertIsNone(v1001.driver_id)
        self.assertFalse(v1001.flags & VehicleFlags.HAS_DRIVER)


if __name__ == "__main__":
    unittest.main()

