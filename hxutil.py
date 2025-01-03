import struct
import av
from fractions import Fraction
import os

def enable_debug():
    av.logging.set_libav_level(av.logging.TRACE)
    av.logging.restore_default_callback()

class Block:
    def __init__(self, type, offset, size, timestamp):
        self.type = type
        self.timestamp = timestamp
        self.offset = offset
        self.size = size
        self.duration = -1
        self.relative_ts = -1

def h265_nalu_type(data):
    """ 
    Decode raw H.265 data to find NAL unit type.

    Args:
        data (bytes): The data to decode.

    Returns:
        int: The type of the NALU.
    """
    if data[0:3] == b'\x00\x00\x01':
        unit_type = (data[3] >> 1) & 0x3F
        return unit_type
    elif data[0:4] == b'\x00\x00\x00\x01':
        # This seems to be the expected format in the video files I have examined.
        unit_type = (data[4] >> 1) & 0x3F
        return unit_type
    else:
        # Return -1 or None if valid NALU padding not found.Not sure which is best yet
        return None

def alaw_to_pcm16(alaw_chunk):
    """
    Convert ALAW audio data to PCM16.

    Args:
        alaw_chunk (bytes): The ALAW data to convert.

    Returns:
        bytes: The converted PCM16 data.
    
    References:
        https://en.wikipedia.org/wiki/G.711#A-law_algorithm
        https://web.archive.org/web/20110714000731/http://hazelware.luggle.com/tutorials/mulawcompression.html
    Notes:
        In my video files, audio blocks seem to all be alaw 8000Hz mono, with 160 samples that represent 20ms of audio.
        There is an unknown 4 byte header/padding before the alaw data. 0x00 01 50 00
    """
    ALAW_TO_PCM16 = [
        -5504, -5248, -6016, -5760, -4480, -4224, -4992, -4736,
        -7552, -7296, -8064, -7808, -6528, -6272, -7040, -6784,
        -2752, -2624, -3008, -2880, -2240, -2112, -2496, -2368,
        -3776, -3648, -4032, -3904, -3264, -3136, -3520, -3392,
        -22016, -20992, -24064, -23040, -17920, -16896, -19968, -18944,
        -30208, -29184, -32256, -31232, -26112, -25088, -28160, -27136,
        -11008, -10496, -12032, -11520, -8960, -8448, -9984, -9472,
        -15104, -14592, -16128, -15616, -13056, -12544, -14080, -13568,
        -344, -328, -376, -360, -280, -264, -312, -296,
        -472, -456, -504, -488, -408, -392, -440, -424,
        -88, -72, -120, -104, -24, -8, -56, -40,
        -216, -200, -248, -232, -152, -136, -184, -168,
        -1376, -1312, -1504, -1440, -1120, -1056, -1248, -1184,
        -1888, -1824, -2016, -1952, -1632, -1568, -1760, -1696,
        -688, -656, -752, -720, -560, -528, -624, -592,
        -944, -912, -1008, -976, -816, -784, -880, -848,
        5504, 5248, 6016, 5760, 4480, 4224, 4992, 4736,
        7552, 7296, 8064, 7808, 6528, 6272, 7040, 6784,
        2752, 2624, 3008, 2880, 2240, 2112, 2496, 2368,
        3776, 3648, 4032, 3904, 3264, 3136, 3520, 3392,
        22016, 20992, 24064, 23040, 17920, 16896, 19968, 18944,
        30208, 29184, 32256, 31232, 26112, 25088, 28160, 27136,
        11008, 10496, 12032, 11520, 8960, 8448, 9984, 9472,
        15104, 14592, 16128, 15616, 13056, 12544, 14080, 13568,
        344, 328, 376, 360, 280, 264, 312, 296,
        472, 456, 504, 488, 408, 392, 440, 424,
        88, 72, 120, 104, 24, 8, 56, 40,
        216, 200, 248, 232, 152, 136, 184, 168,
        1376, 1312, 1504, 1440, 1120, 1056, 1248, 1184,
        1888, 1824, 2016, 1952, 1632, 1568, 1760, 1696,
        688, 656, 752, 720, 560, 528, 624, 592,
        944, 912, 1008, 976, 816, 784, 880, 848
    ]
    result = bytearray()
    for byte in alaw_chunk:
        pcm_value = ALAW_TO_PCM16[byte]
        # Convert to little-endian bytes
        result.extend(pcm_value.to_bytes(2, 'little', signed=True))
    return bytes(result)

def valid_file(file_path):
    """
    Check if a file is a valid HX file.
    
    Args:
        file_path (str): The path to the file.
        
    Returns:
        bool: True if valid, False otherwise.

    Notes:
        This is a simple check to see if the file begins with the magic words 'HXVT' or 'HXVS'.
    """
    with open(file_path, 'rb') as f:
        magic = f.read(4)
        if magic == b'HXVT' or magic == b'HXVS':
            return True
        else:
            return False

def file_info(file_path):
    """
    Return basic information about a HX file.
    
    Args:
        file_path (str): The path to the file.

    Returns:
        dict:   A dictionary containing file information.
                Keys: 'type', 'width', 'height', 'size', 'duration'

    Notes:
        Duration is calculated from the timestamps of the first and last block.

    """
    size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        magic = f.read(4)
        if magic == b'HXVT':
            file_type = 'HXVT'
        elif magic == b'HXVS':
            file_type = 'HXVS'
        else:
            file_type = 'Unknown'
        width = struct.unpack('<I', f.read(4))[0]
        height = struct.unpack('<I', f.read(4))[0]


def index_file(file_path):
    """
    Index a HX file.

    Args:
        file_path (str): The path to the file to index.

    Returns:
        list: A list of Block objects, or None if problem.

    Notes:
        Possibly change function to take file path or file object. Could be more flexible that way.
    """
    blocks = []
    # TODO: Figure out if timestamps are universal or specific to block type. Likely useful for audio sync.
    # TODO: Add support for h264 files.
    video_initial_ts = -1
    audio_initial_ts = -1
    initial_ts = -1
    previous_video_block = None # Used to calculate duration of video blocks.

    try:
        with open(file_path, 'rb') as f:
            offset = 0
            magic = f.read(4)
            if not magic or len(magic) < 4 or magic != b'HXVT':
                # File should begin with magic word HXVT.
                # If not, return None
                return None
            
            # Files have a 16 byte header. Specifies file type, height, and width. Skip this.
            f.seek(16)
            while True:
                magic = f.read(4)

                if magic == b'HXAF':
                    offset = f.tell() - 4
                    length = struct.unpack('<I', f.read(4))[0]
                    timestamp = struct.unpack('<I', f.read(4))[0]
                    #unknown_padding = f.read(4)
                    #audio_header = f.read(4)
                    #audio_data = f.read(length - 4)
                    f.seek(4 + length, 1)
                    block = Block('HXAF', offset, length, timestamp)
                    blocks.append(block)
                elif magic == b'HXVF':
                    offset = f.tell() - 4
                    length = struct.unpack('<I', f.read(4))[0]
                    timestamp = struct.unpack('<I', f.read(4))[0]
                    #unknown_padding = f.read(4) - Seems to be related to type of video frame ?
                    f.seek(4 + length, 1)
                    block = Block('HXVF', offset, length, timestamp)
                    blocks.append(block)
                elif magic == b'HXFI':
                    # Unknown how to decode this block yet. Possibly some type of file index?
                    # Most of this block is 0x00
                    # TODO: Figure this out.
                    offset = f.tell() - 4
                    length = struct.unpack('<I', f.read(4))[0] # Always 0x40 0D 03 00 - 200,000 bytes
                    f.seek(length, 1)
                    block = Block('HXFI', offset, length, -1)
                    #blocks.append(block) - Don't add these to the list for now.
                else:
                    # Found unknown block or reached end of file.
                    break
    except Exception as e:
        return None
    
    # Sort blocks by timestamp. Audio blocks trail video blocks. If timestamps are universal, this will order them correctly.
    # If timestamps are not universal this is not needed.
    blocks.sort(key=lambda x: x.timestamp)

    # Calculate the relative timestamp for each block.
    # If timestamps are not universal could probably just do this in the block processing loop.
    for block in blocks:
        if initial_ts == -1:
            initial_ts = block.timestamp
            block.relative_ts = 0
        else:
            block.relative_ts = block.timestamp - initial_ts
        # Alternate code if timestamps are independent.
        # if block.type == 'HXAF':
        #     if audio_initial_ts == -1:
        #         audio_initial_ts = block.timestamp
        #         block.relative_ts = 0
        #     else:
        #         block.relative_ts = block.timestamp - audio_initial_ts
        # elif block.type == 'HXVF':
        #     if video_initial_ts == -1:
        #         video_initial_ts = block.timestamp
        #         block.relative_ts = 0
        #     else:
        #         block.relative_ts = block.timestamp - video_initial_ts
        
        # This is to calculate the duration of video blocks for muxing. Seems setting PTS/DTS might not be enough.
        # This should only be needed for video blocks as audio are constant 20ms blocks.
        if block.type == 'HXVF':
            if previous_video_block:
                previous_video_block.duration = block.timestamp - previous_video_block.timestamp
            else:
                previous_video_block = block
    return blocks

def rewrap_file(input_file, output_file=None, format='mkv', overwrite=False, debug=False):
    """
    Rewrap a HX file to a new container format.

    Args:
        input_file (str): The path to the input file.
        output_file (str): The path to the output file. Default is to keep the same name as input with new extension.
        format (str): The format to rewrap to. Default is 'mkv'.
        overwrite (bool): Overwrite the output file if it exists. Default is False.
        debug (bool): Enable debug logging. Default is False.

    Returns:
        bool: True if successful, False otherwise.

    Raises:
        ValueError: If the output format is invalid.
        FileExistsError: If the output file already exists.

    Notes:
        Build a new playable file. This will not alter original video data. Audio is converted with no loss.
        Turning on debug will output raw FFMPEG trace output.
        TODO: Add support for h264 files.
    """
    # Valid output formats. Add more after testing. Currently represented as file extension. 
    valid_formats = ['mkv', 'mp4', 'ts']
    if format not in valid_formats:
        raise ValueError('Invalid output format. Please use one of the following: ' + ', '.join(valid_formats))
    if debug:
        enable_debug()
    if not output_file:
        output_file = input_file.rsplit('.', 1)[0] + '.' + format
    if not overwrite and os.path.exists(output_file):
        raise FileExistsError(f'Output file already exists: {output_file}')
    blocks = index_file(input_file)
    if not blocks:
        # Should we raise error here instead of returning False?
        return False
    container = av.open(output_file, 'w')
    video_stream = container.add_stream('libx265', rate=15) # Default to 15fps for now. Our samples were VFR so we will use PTS/DTS.
    audio_stream = container.add_stream('pcm_s16le', rate=8000, layout='mono', format='s16')

    with open(input_file, 'rb') as f:
        f.seek(4) # Skip the initial HXVT block.

        # Set video parameters.
        video_stream.time_base = Fraction(1, 1000)
        video_stream.pix_fmt = "yuv420p"
        video_width = struct.unpack('<I', f.read(4))[0]
        video_stream.width = video_width
        video_height = struct.unpack('<I', f.read(4))[0]
        video_stream.height = video_height

        # Set audio parameters.
        audio_stream.time_base = Fraction(1, 1000)
        audio_stream.rate = 8000
        audio_stream.layout = 'mono'
        audio_stream.format = 's16'
        #audio_stream.frame_size = 160 # 20ms of audio at 8000Hz

        # Create a buffer to hold video data until a complete frame is found.
        video_buffer = bytearray()

        for block in blocks:
            #print(f'Processing block: {block.type} - Timestamp: {block.timestamp} - Offset: {block.offset} - Size: {block.size}')
            if block.type == 'HXAF':
                f.seek(block.offset + 20) # Skip 4 byte header, size, offset, and 4 byte data header.
                data = f.read(block.size - 4)
                pcm_audio = alaw_to_pcm16(data)
                packet = av.packet.Packet(pcm_audio)
                packet.time_base = Fraction(1, 1000)
                packet.pts = block.relative_ts
                packet.dts = block.relative_ts
                packet.stream = audio_stream
                container.mux_one(packet)
            elif block.type == 'HXVF':
                f.seek(block.offset + 16) # Skip 4 byte header, size, offset, and 4 byte unknown data (possibly frame type).
                data = f.read(block.size)
                video_buffer.extend(data)
                nalu_type = h265_nalu_type(data)
                #print(f'NALU Type: {nalu_type}')
                if nalu_type not in (1, 19):
                    # Buffer this data. Will be Packetized and muxed later with video frame data.
                    # Video typically has NALU types 32, 33, and 34 that directly proceed type 19. All share the same timestamp.
                    #print(f'Added block to buffer - Offset: {block.offset} NAL type: {nalu_type}')
                    continue
                packet = av.packet.Packet(video_buffer)
                packet.time_base = Fraction(1, 1000)
                packet.pts = block.relative_ts
                packet.dts = block.relative_ts
                packet.stream = video_stream
                container.mux_one(packet)
                video_buffer.clear()
                #print(f'Video packet: {packet} - NALU Type: {nalu_type} - Timestamp: {block.relative_ts} - Offset: {block.offset}')
    container.close()
    return True