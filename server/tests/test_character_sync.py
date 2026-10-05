"""Pruebas unitarias de sincronización de selección de personajes en TKT/1."""

import asyncio
import unittest
from server.core.entity import DynamicEntity
from server.core.session import ClientSession
from server.network.udp_server import TKTGameServer
from server.config import ServerConfig
from server.protocol.codec import EventPayload, PacketHeader, decode_packet, encode_packet
from server.protocol.constants import EntityType, EventCode, MessageType, PacketFlags


class MockDatagramTransport:
    def __init__(self):
        self.sent_packets = []
        self._closing = False

    def sendto(self, data, addr):
        self.sent_packets.append((data, addr))

    def close(self):
        self._closing = True

    def is_closing(self):
        return self._closing


class TestCharacterSync(unittest.TestCase):
    def setUp(self):
        self.config = ServerConfig()
        self.server = TKTGameServer(self.config)
        self.transport = MockDatagramTransport()
        self.server.transport = self.transport

    def test_codec_character_select_payload(self):
        """Verifica serialización y deserialización del evento CHARACTER_SELECT."""
        payload = EventPayload.create_character_select(
            entity_id=42,
            character_id="axel",
            event_id=101,
            timestamp=123456,
        )
        self.assertEqual(payload.event_code, EventCode.CHARACTER_SELECT)
        self.assertEqual(payload.entity_id, 42)

        packed = payload.pack()
        unpacked = EventPayload.unpack(packed)
        self.assertEqual(unpacked.event_code, EventCode.CHARACTER_SELECT)
        self.assertEqual(unpacked.unpack_character_select(), "axel")

        payload_eli = EventPayload.create_character_select(
            entity_id=99,
            character_id="eli",
            event_id=102,
            timestamp=654321,
        )
        self.assertEqual(payload_eli.unpack_character_select(), "eli")

    def test_server_handles_character_select_and_broadcasts(self):
        """Verifica que el servidor guarde la propiedad y retransmita a otros clientes."""
        c1_addr = ("127.0.0.1", 50001)
        c2_addr = ("127.0.0.1", 50002)

        s1 = self.server.session_manager.create_or_renew_session(c1_addr)
        s2 = self.server.session_manager.create_or_renew_session(c2_addr)

        # Entidad inicial para s1
        e1 = DynamicEntity(entity_id=s1.player_entity_id, entity_type=EntityType.PLAYER)
        self.server.world.upsert_entity(e1)

        # Simular envío de CHARACTER_SELECT de c1
        event = EventPayload.create_character_select(
            entity_id=s1.player_entity_id,
            character_id="eli",
        )
        hdr = PacketHeader(
            message_type=MessageType.EVENT,
            flags=PacketFlags.RELIABLE,
            session_id=s1.session_id,
            sequence=1,
            timestamp=1000,
        )

        self.server.handle_packet(hdr, event.pack(), c1_addr)

        # Verificar que la entidad en el mundo tenga la propiedad actualizada
        updated_e1 = self.server.world.get_entity(s1.player_entity_id)
        self.assertIsNotNone(updated_e1)
        self.assertEqual(updated_e1.properties.get("character_id"), "eli")

        # Verificar que c2 recibió el evento retransmitido
        c2_packets = [p for p in self.transport.sent_packets if p[1] == c2_addr]
        self.assertGreaterEqual(len(c2_packets), 1)

        last_pkt_data, _ = c2_packets[-1]
        out_hdr, out_payload = decode_packet(last_pkt_data)
        self.assertEqual(out_hdr.message_type, MessageType.EVENT)
        out_ev = EventPayload.unpack(out_payload)
        self.assertEqual(out_ev.event_code, EventCode.CHARACTER_SELECT)
        self.assertEqual(out_ev.unpack_character_select(), "eli")
        self.assertEqual(out_ev.entity_id, s1.player_entity_id)

    def test_sync_existing_characters_on_new_connection(self):
        """Verifica que un nuevo cliente reciba los personajes de jugadores ya conectados."""
        c1_addr = ("127.0.0.1", 50001)
        s1 = self.server.session_manager.create_or_renew_session(c1_addr)
        e1 = DynamicEntity(
            entity_id=s1.player_entity_id,
            entity_type=EntityType.PLAYER,
            properties={"character_id": "axel"},
        )
        self.server.world.upsert_entity(e1)

        # Limpiar paquetes previos
        self.transport.sent_packets.clear()

        # Conecta un nuevo cliente c2 mediante HELLO
        from server.protocol.codec import HelloPayload
        c2_addr = ("127.0.0.1", 50002)
        hello_hdr = PacketHeader(
            message_type=MessageType.HELLO,
            flags=PacketFlags.RELIABLE,
            sequence=1,
            timestamp=2000,
        )
        self.server.handle_packet(hello_hdr, HelloPayload().pack(), c2_addr)

        # c2 debe haber recibido WELCOME y luego el evento CHARACTER_SELECT de c1
        c2_packets = [p for p in self.transport.sent_packets if p[1] == c2_addr]
        self.assertGreaterEqual(len(c2_packets), 2)

        # Buscar el evento CHARACTER_SELECT para c1
        char_events = []
        for p_data, _ in c2_packets:
            hdr, payload = decode_packet(p_data)
            if hdr.message_type == MessageType.EVENT:
                ev = EventPayload.unpack(payload)
                if ev.event_code == EventCode.CHARACTER_SELECT:
                    char_events.append(ev)

        self.assertEqual(len(char_events), 1)
        self.assertEqual(char_events[0].entity_id, s1.player_entity_id)
        self.assertEqual(char_events[0].unpack_character_select(), "axel")


if __name__ == "__main__":
    unittest.main()
