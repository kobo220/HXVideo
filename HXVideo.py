import argparse
import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.prompt import Confirm
from rich.markdown import Markdown
from rich.theme import Theme
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.layout import Layout
from rich.logging import RichHandler
from rich.progress import Progress, track
import rich
import os
import logging
from pathlib import Path

import hxutil

title = r"""   __ ___  ___   ___    __       
  / // / |/_/ | / (_)__/ /__ ___ 
 / _  />  < | |/ / / _  / -_) _ \
/_//_/_/|_| |___/_/\_,_/\__/\___/"""

def prompt_path(console, prompt_text):
    path = Prompt.ask(f'[magenta]{prompt_text}[/magenta]')
    return Path(path)

def recurse_path(path, max_depth=6, current_depth=0):
    """
    Recursively searches a directory and returns its contents up to a specified depth.

    Args:
        directory (str): The path of the directory to search.
        max_depth (int): The maximum depth to recurse.
        current_depth (int): The current depth of recursion (used internally).

    Returns:
        list: A list of file and directory paths within the given directory.
    """
    if current_depth > max_depth:
        return []

    contents = []

    try:
        for item in path.iterdir():
            if item.is_dir():
                # If it's a directory, add it and recurse into it
                contents.append(item)
                contents.extend(recurse_path(item, max_depth, current_depth + 1))
            else:
                # If it's a file, add it to the list
                contents.append(item)
    except PermissionError:
        print(f"Permission denied: {path}")
    except FileNotFoundError:
        print(f"Directory not found: {path}")
    except Exception as e:
        print(f"Error reading directory {path}: {e}")

    return contents

def show_main(console):
    os.system('cls' if os.name == 'nt' else 'clear')

    header_text = Text.assemble((title, "bold"), (" v0.0.1", "red"))
    header = Panel(header_text, style="bright_green", expand=False)

    console.print(header)

    console.print("Welcome to HXVideo - [link=https://github.com/kobo220/HXVideo]https://github.com/kobo220/HXVideo[/link]")
    console.print("Convert HX IPCam video files to something playable by common players.")
    console.print(":keyboard:  Provide an input file or directory to convert.")
    console.print(":file_folder: If a directory is provided, all files in the directory will be converted.")
    console.print(":repeat: Recursive mode processes subdirectories and their contents.")
    console.print(":pencil: Renaming mode renames the output file to easier sort files chronologically.")
    console.print(":white_heavy_check_mark: Verify mode runs framehash on the input file and compares it to the output file.")
    console.print("")

    while True:
        input_path = prompt_path(console, "Input file or directory")
        if input_path.exists():
            break
        console.print(f"[red]Error: {input_path.resolve()} does not exist.[/red]")
    
    recurse = Confirm.ask("[magenta]Recurse into subdirectories?[magenta]")
    if recurse:
        all_files = recurse_path(input_path, max_depth=6)
    else:
        all_files = recurse_path(input_path, max_depth=0)

    allowed_files = [f for f in all_files if f.suffix in ['.264', '.265']]
    allowed_files = [f for f in allowed_files if hxutil.valid_file(f)]
    console.print(f"Found {len(allowed_files)} files to convert.")

    file_format = Prompt.ask("[magenta]Output format (mkv or mp4)[/magenta]", default="mkv", choices=["mkv", "mp4"])
    file_verify = Confirm.ask("[magenta]Verify output files with framehash?[/magenta]")
    file_rename = Confirm.ask("[magenta]Rename output files to allow chronological sort?[/magenta]")
    
    while True:
        output_path = prompt_path(console, "Output directory")
        if output_path.exists():
            break
        output_path_created = Confirm.ask(f"[red]{output_path.resolve()} does not exist. Create it?[/red]")
        if output_path_created:
            log.debug(f"Output path does not exist, creating: {output_path.resolve()}")
            output_path.mkdir(parents=True, exist_ok=True)
            break

    progress = Progress(rich.progress.SpinnerColumn(), rich.progress.MofNCompleteColumn(), *Progress.get_default_columns())

    with progress:
        task = progress.add_task("[orange1]Converting files...[/orange1]", total=len(allowed_files))

        for file in allowed_files:
            output_filename = file.with_suffix(f".{file_format}").name
            if hxutil.rewrap_file(file, (output_path / output_filename), file_format, debug=False, overwrite=False):
                #progress.console.print(f"[green]Success: {file.name} converted to {output_filename}[/green]")
                pass
            else:
                #progress.console.print(f"[red]Error: {file.name} failed to convert to {output_filename}[/red]")
                pass
            progress.update(task, advance=1)



def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    custom_theme = Theme({
        "bright_green": "green bold",
        "red": "red",
        "magenta": "magenta",
    })

    console = Console(theme=custom_theme, style="bright_green")

    show_main(console)



    #parser = argparse.ArgumentParser(prog='new.py', description='Utility to convert HX IPCam video files to something useful')
    #parser.add_argument('-i', '-input', help='Input file: The HX file you want to convert.')
    
    #args = parser.parse_args()
    #if len(sys.argv) == 1:
    #    console = Console()
    #    console.print('Welcome to your application!')
    #    console.print('Please provide an input file.')
    #    args.i = Prompt.ask('Input file: ')
    #print(args.i)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    log = logging.getLogger('rich')
    main()