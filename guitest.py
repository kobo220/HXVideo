from flask import Flask, render_template, url_for, request
import webview
import os
from pathlib import Path
import uuid
import hxutil
import threading

number = 100
output = 'Processing ...'
progress = 0
task_list = {}

class Api():
    def get_dir(self):
        print('get_dir')

def get_dir():
    result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG, allow_multiple=False)
    print(result)
    return result
def get_file():
    file_types = ('Video Files (*.264;*.265)', 'All files (*.*)')

    result = webview.windows[0].create_file_dialog(
        webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types
    )
    print(result)
    return result

def convert_files(task_id, files, output_dir, format='mkv', overwrite=False):
    print(f'Thread started?')
    global task_list
    output = ''
    num_files = len(files)
    count = 1
    task_list[task_id] = {'status': 'running', 'progress': 0, 'output': output}
    for file in files:
        pct = (count / num_files) * 100
        output = output + f'{count}/{num_files} - Processing {file}\n'
        task_list[task_id] = {'status': 'running', 'progress': pct, 'output': output}
        #output_file = os.path.join(output_dir, f'{os.path.basename(file)}.{format}')
        output_file = output_dir / f'{file.stem}.{format}'
        print(f'Converted {output_file}')
        hxutil.rewrap_file(file, output_file, format, overwrite)
        count += 1
        output = output + f'Converted {output_file}\n'
        pct = (count / num_files) * 100
        task_list[task_id] = {'status': 'running', 'progress': pct, 'output': output}
        print(task_list)
        print(f'Converted {file} to {output_file}')
    task_list[task_id] = {'status': 'complete', 'progress': 100, 'output': output}

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
        #with os.scandir(path) as entries:
        #    for entry in entries:
        #        if entry.is_dir(follow_symlinks=False):
        #            # If it's a directory, add it and recurse into it
        #            contents.append(entry)
        #            contents.extend(recurse_path(entry.path, max_depth, current_depth + 1))
        #        else:
        #            # If it's a file, add it to the list
        #            contents.append(entry)
    except PermissionError:
        print(f"Permission denied: {path}")
    except FileNotFoundError:
        print(f"Directory not found: {path}")
    except Exception as e:
        print(f"Error reading directory {path}: {e}")

    return contents

def index_files(path, recurse=False):
    files = []
    if not recurse:
        recurse_depth = 0
    #try:
        #for file in os.scandir(dir):
    for item in recurse_path(path, recurse_depth):
        if (item.suffix == '.264' or item.suffix == '.265') and item.is_file():
            if hxutil.valid_file(item):
                files.append(item)
    return files
    #except FileNotFoundError:
    #    print('Directory not found')
    #except PermissionError:
    #    print('Permission denied')
    #except OSError:
    #    print('OS Error')
    #except Exception as e:
    #    print(f"Error reading directory : {e}")
    
    #return files




server = Flask(__name__, static_folder='./assets', template_folder='./templates')

@server.route("/")
def hello_world():
    return render_template('index.html')

@server.route("/batch", methods=['GET'])
def batch_convert():
    return render_template('batch.html')

@server.route("/batch_contents", methods=['POST'])
def batch_contents():
    try:
        input_dir = request.form['input_dir']
        output_dir = request.form['output_dir']
    except KeyError:
        return render_template('index.html', error='Please specify both input and output directories.')

    if not input_dir or not output_dir:
        return render_template('index.html', error='Please specify both input and output directories.')
    
    if not os.path.exists(input_dir):
        return render_template('index.html', error='Input directory does not exist.')
    if not os.path.exists(output_dir):
        return render_template('index.html', error='Output directory does not exist.')
    found_files = index_files(input_dir)
    return render_template('batch_contents.html', input_dir=input_dir, output_dir=output_dir, found_files=found_files)
@server.route("/convert", methods=['POST'])
def convert():
    try:
        convert_type = request.form['convert_type']
        if convert_type == 'single':
            input_file = request.form['input_file']
            output_dir = request.form['output_dir']
            filename = request.form['filename']
            format = request.form['format']
        elif convert_type == 'batch':
            input_dir = request.form['input_dir']
            output_dir = request.form['output_dir']
            overwrite = request.form.get('overwrite') == 1
            recurse = request.form.get('recurse')
            concat = request.form.get('concat')
            format = request.form.get('format')
    except KeyError:
        return render_template('index.html', error='Please complete required fields.')

    if not input_dir or not output_dir:
        return render_template('index.html', error='Please specify both input and output directories.')
    
    if not os.path.exists(input_dir):
        return render_template('index.html', error='Input directory does not exist.')
    if not os.path.exists(output_dir):
        return render_template('index.html', error='Output directory does not exist.')
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    found_files = index_files(input_path, recurse is not None)

    task_id = str(uuid.uuid4())
    # Maybe create thread or track differently so it can be controlled/stopped if needed?
    print(f'Creating task {task_id}')
    task = threading.Thread(target=convert_files, args=(task_id, found_files, output_path, format, overwrite))
    task.start()
    print(found_files)

    return render_template('convert.html', input_dir=input_dir, output_dir=output_dir, found_files=found_files, task_id=task_id)

@server.route("/status/<string:jobid>")
def status(jobid):

    global task_list
    #return {'status': 'running', 'progress': '20', 'output': 'Some text'}
    return task_list[jobid]
    #global progress
    #global output
    #global number
    #progress += 1
    #status = 'running'
    #if progress >= number:
    #    status = 'complete'
    #pct = (progress // number) * 100
    #output = output + f'\nProcessing file {progress} of 1000'
    #status = {'status': status, 'progress': progress, 'output': output}
    #return status
if __name__ == '__main__':
    window = webview.create_window('HXVideo', server)
    window.expose(get_dir, get_file)
    webview.start(debug=True)