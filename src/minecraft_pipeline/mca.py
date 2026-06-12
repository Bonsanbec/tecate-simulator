import os
import struct
import zlib
from .nbt import read_tag, write_tag, load_zlib, save_zlib

def pack_block_states(block_indices, bits_per_block):
    """
    Packs 4096 block indices (integers) into 64-bit signed integers (longs)
    using the non-overlapping packing strategy used in Minecraft 1.16+.
    """
    blocks_per_long = 64 // bits_per_block
    long_count = (4096 + blocks_per_long - 1) // blocks_per_long
    longs = []
    
    for l_idx in range(long_count):
        val = 0
        for b_idx in range(blocks_per_long):
            idx = l_idx * blocks_per_long + b_idx
            if idx < 4096:
                block_val = block_indices[idx]
                val |= (block_val & ((1 << bits_per_block) - 1)) << (b_idx * bits_per_block)
        # Convert to signed 64-bit integer
        if val >= (1 << 63):
            val -= (1 << 64)
        longs.append(val)
    return longs

def unpack_block_states(longs, bits_per_block):
    """
    Unpacks 4096 block indices from 64-bit signed integers (longs).
    """
    blocks_per_long = 64 // bits_per_block
    block_indices = []
    
    for l_val in longs:
        # Convert signed 64-bit integer to unsigned
        if l_val < 0:
            l_val += (1 << 64)
        for b_idx in range(blocks_per_long):
            if len(block_indices) < 4096:
                val = (l_val >> (b_idx * bits_per_block)) & ((1 << bits_per_block) - 1)
                block_indices.append(val)
                
    # pad to 4096 if length is less
    while len(block_indices) < 4096:
        block_indices.append(0)
        
    return block_indices

class MCARegion:
    """
    Represents a Minecraft Region file (r.X.Z.mca) containing 32x32 = 1024 chunks.
    Allows loading existing files, modifying/setting chunks, and saving them.
    """
    def __init__(self, rx, rz):
        self.rx = rx
        self.rz = rz
        # Map: (cx_in_region, cz_in_region) -> compressed_data (bytes)
        self.chunks = {}
        # Timestamps for each chunk
        self.timestamps = {}

    def set_chunk_nbt(self, cx_local, cz_local, chunk_nbt):
        """Compresses NBT chunk data and stores it."""
        compressed = save_zlib(chunk_nbt)
        self.chunks[(cx_local, cz_local)] = compressed
        self.timestamps[(cx_local, cz_local)] = 0 # Default timestamp

    def get_chunk_nbt(self, cx_local, cz_local):
        """Decompresses and returns chunk NBT."""
        compressed = self.chunks.get((cx_local, cz_local))
        if not compressed:
            return None
        return load_zlib(compressed)

    def save(self, filepath):
        """
        Saves the region to an .mca file.
        Format:
          - Locations table: 4096 bytes (1024 entries of 4 bytes: 3-byte sector offset, 1-byte sector count)
          - Timestamps table: 4096 bytes (1024 entries of 4 bytes: unix epoch timestamp)
          - Chunk data sectors: aligned to 4096-byte blocks. Each chunk starts with:
              - 4 bytes: length of following data (1-byte compression type + compressed data)
              - 1 byte: compression type (2 = Zlib)
              - bytes: compressed data
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 1. Prepare chunk sectors and compute locations table
        # Chunks locations starts at sector 2 (after header of 8192 bytes / 2 sectors)
        curr_sector = 2
        locations = {}
        chunk_sectors = []
        
        for cz in range(32):
            for cx in range(32):
                data = self.chunks.get((cx, cz))
                if data:
                    length = len(data) + 1 # +1 for the compression type byte
                    sector_count = (length + 4 + 4095) // 4096
                    locations[(cx, cz)] = (curr_sector, sector_count)
                    
                    # Pad data to sector boundary
                    padding_len = sector_count * 4096 - (length + 4)
                    chunk_sectors.append(struct.pack('>Ib', length, 2) + data + b'\x00' * padding_len)
                    
                    curr_sector += sector_count
                else:
                    locations[(cx, cz)] = (0, 0)

        # 2. Write file
        with open(filepath, 'wb') as f:
            # Write locations table (4096 bytes)
            for cz in range(32):
                for cx in range(32):
                    offset, count = locations[(cx, cz)]
                    # 3-byte offset, 1-byte count
                    entry = (offset << 8) | (count & 0xFF)
                    f.write(struct.pack('>I', entry))
                    
            # Write timestamps table (4096 bytes)
            for cz in range(32):
                for cx in range(32):
                    ts = self.timestamps.get((cx, cz), 0)
                    f.write(struct.pack('>I', ts))
                    
            # Write chunk data sectors
            for sector in chunk_sectors:
                f.write(sector)

    @classmethod
    def load(cls, filepath, rx, rz):
        """Loads a region file from disk."""
        region = cls(rx, rz)
        if not os.path.exists(filepath):
            return region
            
        with open(filepath, 'rb') as f:
            # Read locations
            locations_data = f.read(4096)
            # Read timestamps
            timestamps_data = f.read(4096)
            
            # Read all chunk sectors
            for cz in range(32):
                for cx in range(32):
                    idx = (cz * 32 + cx) * 4
                    entry = struct.unpack('>I', locations_data[idx:idx+4])[0]
                    offset = entry >> 8
                    count = entry & 0xFF
                    
                    if offset > 0 and count > 0:
                        ts = struct.unpack('>I', timestamps_data[idx:idx+4])[0]
                        region.timestamps[(cx, cz)] = ts
                        
                        # Seek to chunk sector
                        f.seek(offset * 4096)
                        length, comp_type = struct.unpack('>Ib', f.read(5))
                        if comp_type != 2:
                            # We only support Zlib (type 2)
                            continue
                        chunk_data = f.read(length - 1)
                        region.chunks[(cx, cz)] = chunk_data
                        
        return region
