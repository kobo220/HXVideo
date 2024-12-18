import struct
import csv

NAL_UNIT_TYPES = {
    0: "TRAIL_N",
    1: "TRAIL_R",
    19: "IDR_W_RADL",
    20: "IDR_N_LP",
    21: "CRA_NUT",
    32: "VPS_NUT",
    33: "SPS_NUT",
    34: "PPS_NUT",
    35: "AUD_NUT",
    36: "EOS_NUT",
    37: "EOB_NUT",
    38: "FD_NUT",
    39: "SEI_NUT"
}

def find_blocks_streaming(f, magic_words, chunk_size=4*1024*1024):
    """
    Scan an already opened file handle `f` in chunks to identify all block occurrences.
    Returns a list of tuples: (offset, magic_word, block_type).
    The file position will be at the end of the file after completion.
    """
    max_magic_len = 4
    leftover_length = max_magic_len - 1

    found_blocks = []
    leftover = b''
    total_offset = 0

    # Ensure we're starting at the beginning of the file
    f.seek(0)

    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            break

        data = leftover + chunk
        start_of_data_in_file = total_offset - len(leftover)

        for magic, block_type in magic_words.items():
            search_start = 0
            while True:
                pos = data.find(magic, search_start)
                if pos == -1:
                    break
                file_offset = start_of_data_in_file + pos
                found_blocks.append((file_offset, magic, block_type))
                search_start = pos + 1

        total_offset += len(chunk)
        leftover = data[-leftover_length:] if len(data) >= leftover_length else data

    found_blocks.sort(key=lambda x: x[0])
    return found_blocks

def parse_block_type_hxvt(f, offset, magic):
    """
    Parse a HeaderBlock. Example layout:
    - After magic, 4-byte version
    - 8-byte timestamp
    """
    f.seek(offset + len(magic))
    frame_width_bytes = f.read(4)
    if len(frame_width_bytes) < 4:
        raise IOError("Unexpected end of file reading header version.")
    frame_height_bytes = f.read(4)
    if len(frame_height_bytes) < 4:
        raise IOError("Unexpected end of file reading header timestamp.")
    
    frame_width = struct.unpack('<I', frame_width_bytes)[0]
    frame_height = struct.unpack('<I', frame_height_bytes)[0]
    
    return {"width": frame_width, "height": frame_height}

def parse_block_type_hxvf(f, offset, magic):
    """
    Parse a BlockTypeA block, for example:
    - After the 4-byte magic, read 4 bytes for length
    - Read length bytes of data
    """
    f.seek(offset + len(magic))
    length_bytes = f.read(4)
    if len(length_bytes) < 4:
        raise IOError("Unexpected end of file while reading BlockTypeA length.")
    ts_bytes = f.read(4)
    if len(ts_bytes) < 4:
        raise IOError("Unexpected end of file while reading BlockTypeA timestamp.")
    unknown_bytes = f.read(4)
    if len(unknown_bytes) < 4:
        raise IOError("Unexpected end of file while reading BlockTypeA unknown field.")
    #block_length = int.from_bytes(length_bytes, 'big')
    data_length = struct.unpack('<I', length_bytes)[0]
    block_ts = struct.unpack('<I', ts_bytes)[0]
    block_data = f.read(data_length)
    if len(block_data) < data_length:
        raise IOError("Unexpected end of file while reading BlockTypeA data.")
    return {"length": data_length, "timestamp": block_ts, "data": block_data}

def parse_block_type_hxaf(f, offset, magic):
    """
    Parse a DataBlock:
    - After magic, 4-byte length
    - Then read that many bytes of data
    """
    f.seek(offset + len(magic))
    length_bytes = f.read(4)
    if len(length_bytes) < 4:
        raise IOError("Unexpected end of file reading data block length.")
    ts_bytes = f.read(4)
    if len(ts_bytes) < 4:
        raise IOError("Unexpected end of file reading data block timestamp.")
    unknown_bytes = f.read(4)
    if len(unknown_bytes) < 4:
        raise IOError("Unexpected end of file reading data block unknown field.")
    data_length = struct.unpack('<I', length_bytes)[0]
    block_ts = struct.unpack('<I', ts_bytes)[0]
    block_data = f.read(data_length)
    if len(block_data) < data_length:
        raise IOError("Unexpected end of file reading data block.")
    return {"length": data_length, "timestamp": block_ts, "data": block_data}

def parse_block_type_hxfi(f, offset, magic):
    """
    Parse a FooterBlock. Example:
    - After magic, 4-byte checksum
    - Followed by a null-terminated string
    """
    f.seek(offset + len(magic))
    length_bytes = f.read(4)
    if len(length_bytes) < 4:
        raise IOError("Unexpected end of file reading footer checksum.")
    unknown_bytes = f.read(8)
    if len(unknown_bytes) < 8:
        raise IOError("Unexpected end of file reading footer unknown field.")
    data_length = struct.unpack('<I', length_bytes)[0]
    block_data = f.read(data_length)
    return {"length": data_length, "data": block_data}

def h265_nalu_type(data):
    """ 
    Decode H.265 NALU data and return the type as an integer.
    """
    if data[0:3] == b'\x00\x00\x01':
        unit_type = (data[3] >> 1) & 0x3F
        return unit_type
    elif data[0:4] == b'\x00\x00\x00\x01':
        # This seems to be the expected format in the video files I have examined.
        unit_type = (data[4] >> 1) & 0x3F
        return unit_type


if __name__ == "__main__":
    # Define magic words and their corresponding block types
    magic_dict = {
        b'HXVS': "HXVS",
        b'HXVT': "HXVT",
        b'HXVF': "HXVF",
        b'HXAF': "HXAF",
        b'HXFI': "HXFI"
    }

    # Dispatch table: maps block_type to the appropriate parser function
    block_parsers = {
        "HXVS": parse_block_type_hxvt,
        "HXVT": parse_block_type_hxvt,
        "HXVF": parse_block_type_hxvf,
        "HXAF": parse_block_type_hxaf,
        "HXFI": parse_block_type_hxfi
    }

    filename = "P241117_000000_000340.265"
    # Open the file once
    with open(filename, 'rb') as f:
        with open('csv_data.csv', mode='w') as csv_file:
            # First pass: find all blocks
            blocks = find_blocks_streaming(f, magic_dict)

            # Now we can parse each block with the same file handle
            for offset, magic, btype in blocks:
                parser = block_parsers.get(btype)
                if parser is not None:
                    block_info = parser(f, offset, magic)
                    print(f"Parsed {btype} at offset {offset}: {block_info}")
                    #if btype == "HXVF" or btype == "HXAF":
                    if btype == "HXVF":
                        csv_file.write(f"{offset},{btype},{block_info['timestamp']}, {block_info['length']}, {h265_nalu_type(block_info['data'])}\n")
                        with open(f'frames/{offset}.265', mode='wb') as frame_file:
                            frame_file.write(block_info['data'])
                else:
                    print(f"No parser available for block type {btype}")
