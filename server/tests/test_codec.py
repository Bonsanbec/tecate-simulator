"""Pruebas unitarias para el codec binario de TKT/1 basadas en unittest."""

import unittest
from server.protocol.codec import (
    ChatPayload,
    EntityStateRecord,
    GoodbyePayload,
    HelloPayload,
    InputPayload,
    PacketHeader,
    PingPongPayload,
    SnapshotPayload,
    WelcomePayload,
    calculate_checksum,
    decode_packet,
    encode_packet,
)
from server.protocol.constants import HEADER_SIZE, MAGIC_BYTES, MessageType, PacketFlags


class TestTKTCodec(unittest.TestCase):
    def test_packet_header_pack_unpack(self):
        hdr = PacketHeader(
            magic=MAGIC_BYTES,
            protocol_version=1,
            message_type=MessageType.WELCOME,
            flags=PacketFlags.RELIABLE,
            session_id=12345,
            sequence=42,
            ack=41,
            timestamp=99999,
            payload_length=16,
            payload_checksum=500,
        )
        raw = hdr.pack()
        self.assertEqual(len(raw), HEADER_SIZE)
        unpacked = PacketHeader.unpack(raw)
        self.assertEqual(unpacked.magic, MAGIC_BYTES)
        self.assertEqual(unpacked.protocol_version, 1)
        self.assertEqual(unpacked.message_type, MessageType.WELCOME)
        self.assertEqual(unpacked.flags, PacketFlags.RELIABLE)
        self.assertEqual(unpacked.session_id, 12345)
        self.assertEqual(unpacked.sequence, 42)
        self.assertEqual(unpacked.ack, 41)
        self.assertEqual(unpacked.timestamp, 99999)
        self.assertEqual(unpacked.payload_length, 16)
        self.assertEqual(unpacked.payload_checksum, 500)

    def test_hello_roundtrip(self):
        hello = HelloPayload(client_version="1.2.3", auth_token="token_secret_123")
        raw = hello.pack()
        unpacked = HelloPayload.unpack(raw)
        self.assertEqual(unpacked.client_version, "1.2.3")
        self.assertEqual(unpacked.auth_token, "token_secret_123")

    def test_welcome_roundtrip(self):
        welcome = WelcomePayload(session_id=555, player_entity_id=1, server_tick=1000, server_time=50000)
        raw = welcome.pack()
        self.assertEqual(len(raw), 16)
        unpacked = WelcomePayload.unpack(raw)
        self.assertEqual(unpacked.session_id, 555)
        self.assertEqual(unpacked.player_entity_id, 1)
        self.assertEqual(unpacked.server_tick, 1000)
        self.assertEqual(unpacked.server_time, 50000)

    def test_input_roundtrip(self):
        inp = InputPayload(
            tick=120,
            pos_x=-6.684,
            pos_y=400.21,
            pos_z=2.68,
            yaw=180.5,
            pitch=-15.2,
            vel_x=2.5,
            vel_y=-0.5,
            vel_z=1.2,
            flags=5,
        )
        raw = inp.pack()
        self.assertEqual(len(raw), 38)
        unpacked = InputPayload.unpack(raw)
        self.assertEqual(unpacked.tick, 120)
        self.assertAlmostEqual(unpacked.pos_x, -6.684, places=3)
        self.assertAlmostEqual(unpacked.pos_y, 400.21, places=2)
        self.assertAlmostEqual(unpacked.pos_z, 2.68, places=2)
        self.assertAlmostEqual(unpacked.yaw, 180.5, places=1)
        self.assertAlmostEqual(unpacked.pitch, -15.2, places=1)
        self.assertAlmostEqual(unpacked.vel_x, 2.5, places=2)
        self.assertEqual(unpacked.flags, 5)

    def test_snapshot_roundtrip(self):
        e1 = EntityStateRecord(
            entity_id=1,
            entity_type=1,
            flags=1,
            pos_x=10.0,
            pos_y=20.0,
            pos_z=30.0,
            yaw=45.0,
            pitch=0.0,
            vel_x=1.0,
            vel_y=0.0,
            vel_z=-1.0,
        )
        e2 = EntityStateRecord(
            entity_id=2,
            entity_type=1,
            flags=0,
            pos_x=-15.0,
            pos_y=22.0,
            pos_z=-40.0,
            yaw=90.0,
            pitch=5.0,
            vel_x=0.0,
            vel_y=0.0,
            vel_z=0.0,
        )
        snap = SnapshotPayload(server_tick=888, server_time=123456, entities=[e1, e2])
        raw = snap.pack()
        self.assertEqual(len(raw), 10 + 2 * 38)
        unpacked = SnapshotPayload.unpack(raw)
        self.assertEqual(unpacked.server_tick, 888)
        self.assertEqual(unpacked.server_time, 123456)
        self.assertEqual(len(unpacked.entities), 2)
        self.assertEqual(unpacked.entities[0].entity_id, 1)
        self.assertAlmostEqual(unpacked.entities[0].pos_x, 10.0, places=3)
        self.assertEqual(unpacked.entities[1].entity_id, 2)
        self.assertAlmostEqual(unpacked.entities[1].pos_x, -15.0, places=3)

    def test_ping_pong_roundtrip(self):
        p = PingPongPayload(ping_id=77, timestamp=456789)
        raw = p.pack()
        self.assertEqual(len(raw), 8)
        unpacked = PingPongPayload.unpack(raw)
        self.assertEqual(unpacked.ping_id, 77)
        self.assertEqual(unpacked.timestamp, 456789)

    def test_chat_roundtrip(self):
        chat = ChatPayload(channel=0, sender_id=10, message="¡Saludos desde Tecate Pueblo Mágico!")
        raw = chat.pack()
        unpacked = ChatPayload.unpack(raw)
        self.assertEqual(unpacked.channel, 0)
        self.assertEqual(unpacked.sender_id, 10)
        self.assertEqual(unpacked.message, "¡Saludos desde Tecate Pueblo Mágico!")

    def test_encode_decode_packet_full(self):
        hdr = PacketHeader(
            message_type=MessageType.CHAT,
            session_id=99,
            sequence=1,
            ack=0,
            timestamp=1000,
        )
        chat = ChatPayload(channel=1, sender_id=99, message="Hola Mundo")
        encoded = encode_packet(hdr, chat.pack())

        hdr_out, payload_out = decode_packet(encoded)
        self.assertEqual(hdr_out.message_type, MessageType.CHAT)
        self.assertEqual(hdr_out.session_id, 99)
        chat_out = ChatPayload.unpack(payload_out)
        self.assertEqual(chat_out.message, "Hola Mundo")

    def test_decode_corrupted_checksum(self):
        hdr = PacketHeader(message_type=MessageType.PING)
        ping = PingPongPayload(ping_id=1, timestamp=2)
        encoded = bytearray(encode_packet(hdr, ping.pack()))
        encoded[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            decode_packet(bytes(encoded))


if __name__ == "__main__":
    unittest.main()
