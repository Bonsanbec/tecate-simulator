"""Prueba de integración end-to-end para el despachador y protocolo TKT/1 en entorno aislado."""

import unittest
from server.config import ServerConfig
from server.core.entity import DynamicEntity
from server.network.udp_server import TKTGameServer
from server.protocol.codec import (
    HelloPayload,
    InputPayload,
    PacketHeader,
    PingPongPayload,
    SnapshotPayload,
    WelcomePayload,
    decode_packet,
    encode_packet,
)
from server.protocol.constants import MessageType, PacketFlags


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

        # 5. Generar SNAPSHOT para un segundo jugador y verificar presencia de la entidad
        client2_addr = ("192.168.1.101", 61235)
        s2 = self.server.session_manager.create_or_renew_session(client2_addr)
        snap = self.server.world.build_snapshot_for_player(s2.player_entity_id, 1, 100)
        self.assertEqual(len(snap.entities), 1)
        self.assertEqual(snap.entities[0].entity_id, player_id)


if __name__ == "__main__":
    unittest.main()
