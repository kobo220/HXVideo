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
    
    # Check if the input path is a directory and ask if we should recurse into it.
    # If we recurse, we'll get a list of all files in the directory and its subdirectories.
    # If we don't recurse, we'll only get the files in the directory. 
    # If the input path is a file, we'll just use that file.
    if input_path.is_dir():
        recurse = Confirm.ask("[magenta]Recurse into subdirectories?[magenta]")
        if recurse:
            all_files = recurse_path(input_path, max_depth=6)
        else:
            all_files = recurse_path(input_path, max_depth=0)
    elif input_path.is_file():
        all_files = [input_path]
    else:
        console.print(f"[red]Error: {input_path.resolve()} is not a file or directory.[/red]")
        return

    # Filter the list of files to only include files with the extensions we want.
    # We'll also check for the supported magic words in the file to ensure it's a valid HX file
    allowed_files = [f for f in all_files if f.suffix in ['.264', '.265']]
    allowed_files = [f for f in allowed_files if hxutil.valid_file(f)]
    if len(allowed_files) == 0:
        console.print(f"[red]Error: No valid files found: {input_path.resolve()}[/red]")
        return
    console.print(f"[italic orange1]Found {len(allowed_files)} file(s) to convert.[/italic orange1]")

    # Ask for the output directory and create it if it doesn't exist
    while True:
        output_path = prompt_path(console, "Output directory")
        if output_path.exists() and output_path.is_dir():
            break   # The directory exists, continue to the next step
        output_path_create = Confirm.ask(f"[red]{output_path.resolve()} does not exist. Create it?[/red]")
        if output_path_create:
            try:
                log.debug(f"Output path does not exist, creating: {output_path.resolve()}")
                output_path.mkdir(parents=True, exist_ok=True)

                # Double-check if the directory was created successfully
                if output_path.exists() and output_path.is_dir():
                    break
                else:
                    console.print(f"[bold red]Failed to create the directory: {output_path.resolve()}[/bold red]")
            except Exception as e:  
                console.print(f"[bold red]Error: {e}[/bold red]")
        else:
            console.print("[orange1]Please provide a new output directory.[/orange1]")


    file_format = Prompt.ask("[magenta]Output format (mkv or mp4)[/magenta]", default="mkv", choices=["mkv", "mp4"])
    file_rename = Confirm.ask("[magenta]Rename output files to allow chronological sort?[/magenta]")
    file_verify = Confirm.ask("[magenta]Verify output files with framehash?[/magenta]")    



    progress = Progress(rich.progress.SpinnerColumn(), rich.progress.MofNCompleteColumn(), rich.progress.TimeRemainingColumn(), *Progress.get_default_columns())

    with progress:
        task = progress.add_task("[orange1]Converting files...[/orange1]", total=len(allowed_files))

        for file in allowed_files:
            # Check if we should rename the output file
            if file_rename:
                file_rename = hxutil.get_newname(file)
                output_filename = file_rename.with_suffix(f".{file_format}").name
            else:
                output_filename = file.with_suffix(f".{file_format}").name

            output_file_path = output_path / output_filename

            # TODO: Need to rework this and the hxutil.rewrap_file function to better handle errors and check for success. Right now, I'm raising errors in some places and returning False in others. - Not good. 
            if hxutil.rewrap_file(file, output_file_path, file_format, debug=False, overwrite=False):
                #progress.console.print(f"[green]Success: {file.name} converted to {output_filename}[/green]")
                if file_verify:
                    if hxutil.verify(file, output_file_path):
                        progress.console.print(f"[green]Success: {file.name} converted to {output_filename}[/green]")
                    else:
                        # Should probably delete the output file here if verification failed
                        progress.console.print(f"[red]Error: Verification of {file.name} / {output_filename} failed![/red]")
            else:
                progress.console.print(f"[red]Error: {file.name} failed to convert to {output_filename}[/red]")
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