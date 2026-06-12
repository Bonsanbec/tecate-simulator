import struct
import io
import gzip
import zlib

# NBT Tag Types
TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12

class NBT:
    def __init__(self, tag_type, name=None, value=None):
        self.type = tag_type
        self.name = name
        self.value = value

    def __repr__(self):
        return f"NBT(type={self.type}, name={self.name}, value={self.value})"

def write_string(name, stream):
    b = name.encode('utf-8')
    stream.write(struct.pack('>H', len(b)))
    stream.write(b)

def read_string(stream):
    length = struct.unpack('>H', stream.read(2))[0]
    return stream.read(length).decode('utf-8')

def write_tag(tag, stream, write_header=True):
    if write_header:
        stream.write(struct.pack('>B', tag.type))
        if tag.name is not None:
            write_string(tag.name, stream)
            
    t = tag.type
    val = tag.value
    
    if t == TAG_END:
        pass
    elif t == TAG_BYTE:
        stream.write(struct.pack('>b', val))
    elif t == TAG_SHORT:
        stream.write(struct.pack('>h', val))
    elif t == TAG_INT:
        stream.write(struct.pack('>i', val))
    elif t == TAG_LONG:
        stream.write(struct.pack('>q', val))
    elif t == TAG_FLOAT:
        stream.write(struct.pack('>f', val))
    elif t == TAG_DOUBLE:
        stream.write(struct.pack('>d', val))
    elif t == TAG_BYTE_ARRAY:
        stream.write(struct.pack('>i', len(val)))
        stream.write(val)
    elif t == TAG_STRING:
        write_string(val, stream)
    elif t == TAG_LIST:
        item_type, items = val
        stream.write(struct.pack('>B', item_type))
        stream.write(struct.pack('>i', len(items)))
        for item in items:
            if isinstance(item, NBT):
                write_tag(item, stream, write_header=False)
            else:
                write_tag(NBT(item_type, value=item), stream, write_header=False)
    elif t == TAG_COMPOUND:
        for member in val:
            write_tag(member, stream, write_header=True)
        stream.write(struct.pack('>B', TAG_END))
    elif t == TAG_INT_ARRAY:
        stream.write(struct.pack('>i', len(val)))
        for x in val:
            stream.write(struct.pack('>i', x))
    elif t == TAG_LONG_ARRAY:
        stream.write(struct.pack('>i', len(val)))
        for x in val:
            stream.write(struct.pack('>q', x))
    else:
        raise ValueError(f"Unknown tag type {t}")

def read_tag(stream, expected_type=None, read_header=True):
    if read_header:
        t_byte = stream.read(1)
        if not t_byte:
            return None
        t = struct.unpack('>B', t_byte)[0]
        if t == TAG_END:
            return NBT(TAG_END)
        name = read_string(stream)
    else:
        t = expected_type
        name = None
        
    if t == TAG_END:
        return NBT(TAG_END)
        
    val = None
    if t == TAG_BYTE:
        val = struct.unpack('>b', stream.read(1))[0]
    elif t == TAG_SHORT:
        val = struct.unpack('>h', stream.read(2))[0]
    elif t == TAG_INT:
        val = struct.unpack('>i', stream.read(4))[0]
    elif t == TAG_LONG:
        val = struct.unpack('>q', stream.read(8))[0]
    elif t == TAG_FLOAT:
        val = struct.unpack('>f', stream.read(4))[0]
    elif t == TAG_DOUBLE:
        val = struct.unpack('>d', stream.read(8))[0]
    elif t == TAG_BYTE_ARRAY:
        length = struct.unpack('>i', stream.read(4))[0]
        val = stream.read(length)
    elif t == TAG_STRING:
        val = read_string(stream)
    elif t == TAG_LIST:
        item_type = struct.unpack('>B', stream.read(1))[0]
        length = struct.unpack('>i', stream.read(4))[0]
        items = []
        for _ in range(length):
            items.append(read_tag(stream, expected_type=item_type, read_header=False))
        val = (item_type, items)
    elif t == TAG_COMPOUND:
        members = []
        while True:
            member = read_tag(stream, read_header=True)
            if member is None or member.type == TAG_END:
                break
            members.append(member)
        val = members
    elif t == TAG_INT_ARRAY:
        length = struct.unpack('>i', stream.read(4))[0]
        val = []
        for _ in range(length):
            val.append(struct.unpack('>i', stream.read(4))[0])
    elif t == TAG_LONG_ARRAY:
        length = struct.unpack('>i', stream.read(4))[0]
        val = []
        for _ in range(length):
            val.append(struct.unpack('>q', stream.read(8))[0])
    else:
        raise ValueError(f"Unknown tag type {t}")
        
    return NBT(t, name, val)

# Gzip/Zlib Compression Helpers
def load_gzip(filepath):
    """Loads a Gzip-compressed NBT file (like level.dat)."""
    with gzip.open(filepath, 'rb') as f:
        return read_tag(f)

def save_gzip(tag, filepath):
    """Saves a Gzip-compressed NBT file (like level.dat)."""
    with gzip.open(filepath, 'wb') as f:
        write_tag(tag, f)

def load_zlib(data):
    """Decompresses Zlib-compressed NBT chunk data."""
    decompressed = zlib.decompress(data)
    buf = io.BytesIO(decompressed)
    return read_tag(buf)

def save_zlib(tag):
    """Serializes NBT and compresses using Zlib for chunk storage."""
    buf = io.BytesIO()
    write_tag(tag, buf)
    return zlib.compress(buf.getvalue())
