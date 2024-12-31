import argparse
import hxutil

class HXVideo:
    class Block:
        def __init__(self, type, offset, size, timestamp):
            self.type = type
            self.timestamp = timestamp
            self.offset = offset
            self.size = size
    def __init__(self):
        # Gotta decide if I want to use this class or not
        pass



def main():
    parser = argparse.ArgumentParser(prog='HXVideo.py', description='Utility to convert HX IPCam video files to something useful')
    input_group = parser.add_mutually_exclusive_group(required=True)
    output_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('-i', '-input', help='Input file: The HX file you want to convert.')
    output_group.add_argument('-o', '-output', help='Output file: The output file you want to create.')
    parser.add_argument('-fmt', help='Output format: The format you want to convert to.')
    input_group.add_argument('-indir', help='Input directory: The directory containing the HX files you want to convert.')
    output_group.add_argument('-outdir', help='Output directory: The directory where you want to save the converted files.')
    parser.add_argument('-r', action="store_true", help='Recursive mode: Process subdirectories and their contents.')
    parser.add_argument('-v', action="store_true", help='Verbose mode: Print debug information.')
    args = parser.parse_args()

    if hxutil.rewrap_file(args.i, args.o, args.fmt, debug=False, overwrite=True):
        print('Success')


if __name__ == '__main__':
    main()