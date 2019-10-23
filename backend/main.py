#!/usr/bin/env python
import subprocess
from flask import Flask, make_response, request, current_app
from ConfigParser import SafeConfigParser
from datetime import timedelta, datetime
from functools import update_wrapper, wraps
from entrypoint2 import entrypoint
from pyscreenshot import grab_to_file

app = Flask(__name__, static_url_path='/static')

parser = SafeConfigParser()
parser.read('config.ini')

# Any control origin
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

def auth(user_input=''):  # Check password
    correct_password = parser.get('Server', 'Password')
    if user_input == correct_password:
        return True
    return False

@app.route('/')
@crossdomain(origin='*')
def index():  # index
    index_message = parser.get('Server', 'Name') + '. Version: ' + parser.get('SoftwareProperties', 'Version')
    return index_message

@app.route('/volume')
@crossdomain(origin='*')
def volume():  # volume ctrl
    if auth(request.args.get('password')) is False: return 'authfail'
    if request.args.get('action') == 'up':
        subprocess.check_call(['nircmd', 'changesysvolume', parser.get('Scale', 'Up')])
        return 'Volume up.'
    elif request.args.get('action') == 'down':
        subprocess.check_call(['nircmd', 'changesysvolume', parser.get('Scale', 'Down')])
        return 'Volume down.'
    elif request.args.get('action') == 'mute':
        subprocess.check_call(['nircmd', 'mutesysvolume', '2'])
        return 'Muted / Unmuted.'
    return 'Action not specified.'

@app.route('/brightness')
@crossdomain(origin='*')
def brightness():  # brightness ctrl
    if auth(request.args.get('password')) is False: return 'authfail'
    if request.args.get('action') == 'up':
        subprocess.check_call(['nircmd', 'changebrightness', parser.get('Scale', 'BUp')])
        return 'Brighter.'
    elif request.args.get('action') == 'down':
        subprocess.check_call(['nircmd', 'changebrightness', parser.get('Scale', 'BDown')])
        return 'Darker.'
    elif request.args.get('action') == '0':
        subprocess.check_call(['nircmd', 'setbrightness', '0'])
        return 'Darkest.'
    elif request.args.get('action') == '100':
        subprocess.check_call(['nircmd', 'setbrightness', '100'])
        return 'Brightest.'
    return 'Action not specified.'
 
@app.route('/key')
@crossdomain(origin='*')
def key():  # press keyboard
    import pyautogui
    if auth(request.args.get('password')) is False: return 'authfail'
    try:
        button = str(request.args.get('key'))
    except:
        return 'badparam'
    pyautogui.press(button)
    return str(request.args.get('key')) + ' button pressed'

@app.route('/webcam')
@crossdomain(origin='*')
def webcam():
    if auth(request.args.get('password')) is False: return 'authfail'
    from VideoCapture import Device
    cam = Device()
    cam.saveSnapshot('./static/image.jpg')
    return 'Taken'

@app.route('/screenshot')
@crossdomain(origin='*')
def screenshot(): 
    if auth(request.args.get('password')) is False: return 'authfail'
    @entrypoint
    def show(backend='auto'):
        if backend == 'auto':
            backend = None
        im = grab_to_file(filename='./static/desktop.jpg', backend=backend)
    show()
    return 'Screenshot taken.'

if __name__ == '__main__':
    app.run()
