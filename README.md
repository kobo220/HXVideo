# HXVideo

## Introduction
Does some stuff

## File Details

### File Structure
|   Offset      |    Length     |  Data                     |  Description              |
|---------      |--------       |---------------            |---                        |
|   0x00 - 00   |  4 bytes      |   0x48 58 56 54 - HXVT    |   Magic Word                    |
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
