from flask import Flask, render_template, url_for, request
import webview
import os
from pathlib import Path
import hxutil

number = 100
output = 'Processing ...'
progress = 0

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

def index_files(dir):
    try:
        files = []
        for file in os.scandir(dir):
            if (file.name.endswith('.264') or file.name.endswith('.265')) and file.is_file(follow_symlinks=False):
                if hxutil.valid_file(file):
                    files.append(file)
        return files
    except FileNotFoundError:
        print('Directory not found')
    except PermissionError:
        print('Permission denied')
    except OSError:
        print('OS Error')




server = Flask(__name__, static_folder='./assets', template_folder='./templates')

@server.route("/")
def hello_world():
    return render_template('index.html')

@server.route("/convert", methods=['POST'])
def convert():
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
    return render_template('convert.html', input_dir=input_dir, output_dir=output_dir, found_files=found_files)

@server.route("/status/<string:jobid>")
def status(jobid):
    global progress
    global output
    global number
    progress += 1
    status = 'running'
    if progress >= number:
        status = 'complete'
    pct = (progress // number) * 100
    output = output + f'\nProcessing file {progress} of 1000'
    status = {'status': status, 'progress': progress, 'output': output}
    return status
if __name__ == '__main__':
    window = webview.create_window('HXVideo', server)
    window.expose(get_dir, get_file)
    webview.start(debug=True)