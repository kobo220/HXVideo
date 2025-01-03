# HXVideo

## Introduction
This Python script converts proprietary .265 file extension video files from certain IP surveillance cameras to a useable format that can be played in common video players such as VLC media player or PotPlayer. Playback in Windows Media Player may be possible
if your system was the proper HEVC codecs installed.<p>
[!IMPORTANT]
Support for the .264 file extension (HXVS) is planned.


## File Details
The files contain a 16 byte header. The header consists of a magic word which designates the file type (HXVT - HEVC h265 or HXVS - H265). The header also contains the widthxheight of the video in pixels.
After the header the file contains the below data blocks which can parsed to rebuild the respective data streams. These blocks contain timestamp information which is measured in milliseconds. Further reasearch is needed to see if these timestamps can be traced across sequential files. If they are, this would aid in the concatenation of clips into longer files. In the files I examined (HXVT), the video streams had both a variable bit rate and variable frame rate. Audio is a constant bit rate, with each audio data block containing 160 8-bit samples of A-law data representing 20-milliseconds of audio.

### File Structure
|   Offset      |    Length     |  Data                     |  Description              |
|---------      |--------       |---------------            |---                        |
|   0x00 - 00   |  4 bytes      |   0x48 58 56 54 - HXVT    |   Magic Word <br> HXVT - HEVC h265                    |
|   0x04 - 04   |  4 bytes      |   32-bit int              |   Video width in pixels   |
|   0x08 - 08   |  4 bytes      |   32-bit int              |   Video height in pixels  |
|   0x10 - 16   |  -            |                           |   Data blocks start. See below       |

### Video Data Block
| Relative offset   |   Length              |   Data                            |   Description             |
|---                |---                    |---                                |---                        |
|   0x00            |   4 bytes             |  0x48 58 56 46 - HXVF             |   Magic word              |
|   0x04            |   4 bytes             |   32-bit int                      |   Data size               |
|   0x08            |   4 bytes             |   32-bit int                      |   Timestamp               |
|   0x0C            |   4 bytes             |   Unknown                         |   Possibly related to frame type.  |   
|   0x10            |   (data size) bytes   |   Start prefix + Binary NAL unit  |   Start prefix 0x00 00 00 01 + NAL unit data  |

### Audio Data Block
| Relative offset   |   Length              |   Data                            |   Description             |
|---                |---                    |---                                |---                        |
|   0x00            |   4 bytes             |  0x48 58 41 46 - HXAF             |   Magic word              |
|   0x04            |   4 bytes             |   32-bit int                      |   Data size - 164 bytes   |
|   0x08            |   4 bytes             |   32-bit int                      |   Timestamp               |
|   0x0C            |   4 bytes             |   Unknown                         |   Unknown padding of 0x00 00 00 00  |   
|   0x10            |   (data size) bytes   |   Unknown prefix + Audio data     |   Start prefix 0x00 01 50 00 + 1 byte alaw audio samples (160 total)  |

### Unknown Data Block
| Relative offset   |   Length              |   Data                            |   Description             |
|---                |---                    |---                                |---                        |
|   0x00            |   4 bytes             |  0xHXFI - HXFI                    |   Magic word              |
|   0x04            |   4 bytes             |   32-bit int                      |   Data size - 200,000 bytes   |
|   0x08            |   (data size) bytes   |   Unknown                         |   Unknown data. Mostly 0x00   |

