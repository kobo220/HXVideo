# HXVideo

> [!CAUTION]
This is still a work in progress. Not all features are built out at this time. Minimal debugging and error handling have been tested.

## Introduction
This Python script converts proprietary .265 file extension video files from certain IP surveillance cameras to a useable format that can be played in common video players such as VLC media player or PotPlayer. Playback in Windows Media Player may be possible
if your system was the proper HEVC codecs installed. The video data is not transcoded and is copied as it into a new container. This can be verified using [FFmpeg's framemd5](https://trac.ffmpeg.org/wiki/framemd5%20Intro%20and%20HowTo). Audio data is transcoded from a-law to pcm_s16le to be compatible with modern video containers, however this is a lossless process. 

>[!NOTE]
>Support for the .264 file extension (HXVS) is planned.

## Usage

```
usage: HXVideo.py [-h] [-i I] [-o O] [-fmt FMT] [-indir INDIR] [-outdir OUTDIR] [-r] [-v]

Utility to convert HX IPCam video files to something useful

options:
  -h, --help       show this help message and exit
  -i I, -input I   Input file: The HX file you want to convert.
  -o O, -output O  Output file: The output file you want to create.
  -fmt FMT         Output format: The format you want to convert to.
  -indir INDIR     Input directory: The directory containing the HX files you want to convert.
  -outdir OUTDIR   Output directory: The directory where you want to save the converted files.
  -r               Recursive mode: Process subdirectories and their contents.
  -v               Verbose mode: Print debug information.

  ```


## File Details
The files contain a 16 byte header. The header consists of a magic word which designates the file type (HXVT - HEVC h265 or HXVS - H265). The header also contains the widthxheight of the video in pixels.
After the header the file contains the below data blocks which can parsed to rebuild the respective data streams. These blocks contain timestamp information which is measured in milliseconds. Further reasearch is needed to see if these timestamps can be traced across sequential files. If they are, this would aid in the concatenation of clips into longer files. In the files I examined (HXVT), the video streams had both a variable bit rate and variable frame rate. Audio is a constant bit rate, with each audio data block containing 160 8-bit samples of A-law data representing 20-milliseconds of audio.

### File Structure
|   Offset      |    Length     |  Data                     |  Description              |
|---------      |--------       |---------------            |---                        |
|   0x00 - 00   |  4 bytes      |   `0x48 58 56 54` - HXVT    |   Magic Word <br> HXVT - HEVC h265                    |
|   0x04 - 04   |  4 bytes      |   32-bit int              |   Video width in pixels   |
|   0x08 - 08   |  4 bytes      |   32-bit int              |   Video height in pixels  |
|   0x10 - 16   |  -            |                           |   Data blocks start. See below       |

### Video Data Block
| Relative offset   |   Length              |   Data                            |   Description             |
|---                |---                    |---                                |---                        |
|   0x00            |   4 bytes             |  `0x48 58 56 46` - HXVF             |   Magic word              |
|   0x04            |   4 bytes             |   32-bit int                      |   Data size               |
|   0x08            |   4 bytes             |   32-bit int                      |   Timestamp               |
|   0x0C            |   4 bytes             |   Unknown                         |   Possibly related to frame type.  |   
|   0x10            |   (data size) bytes   |   Start prefix + Binary NAL unit  |   Start prefix `0x00 00 00 01` + NAL unit data  |

### Audio Data Block
| Relative offset   |   Length              |   Data                            |   Description             |
|---                |---                    |---                                |---                        |
|   0x00            |   4 bytes             |  `0x48 58 41 46` - HXAF             |   Magic word              |
|   0x04            |   4 bytes             |   32-bit int                      |   Data size - 164 bytes   |
|   0x08            |   4 bytes             |   32-bit int                      |   Timestamp               |
|   0x0C            |   4 bytes             |   Unknown                         |   Unknown padding of `0x00 00 00 00`  |   
|   0x10            |   (data size) bytes   |   Unknown prefix + Audio data     |   Start prefix `0x00 01 50 00` + 1 byte alaw audio samples (160 total)  |

### Unknown Data Block
| Relative offset   |   Length              |   Data                            |   Description             |
|---                |---                    |---                                |---                        |
|   0x00            |   4 bytes             |  `0x48 58 46 49` - HXFI                    |   Magic word              |
|   0x04            |   4 bytes             |   32-bit int                      |   Data size - 200,000 bytes   |
|   0x08            |   (data size) bytes   |   Unknown                         |   Unknown data. Mostly 0x00   |


## TODO
- [ ] Finish building out functionality described above and in software.
- [ ] Add support for .264 files
- [ ] Make code more robust. Currently makes some assumptions about data based on the files I've examined.
- [ ] Corrupt/incomplete file handling.

## Sources
- **Third-Party Libraries Used:**
  - [FFmpeg](https://ffmpeg.org/)
  - [PyAV](https://github.com/PyAV-Org/PyAV)
  - [Flask](https://flask.palletsprojects.com)
  - [pywebview](https://pywebview.flowrl.com/)

- **External References:**
  - [francescovannini's ipcam26Xconvert](https://github.com/francescovannini/ipcam26Xconvert) - A tool written in C which basically does the same thing as this tool.
  - [Spitzner's research of KKmoon ipcam](https://spitzner.org/kkmoon.html) - Research into decoding the proprietary files used in these flavors of IP surveillance cameras.