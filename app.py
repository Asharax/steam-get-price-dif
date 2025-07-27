#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template, jsonify, Response
import SteamApiService
import time
from threading import Thread

# Support for gomix's 'front-end' and 'back-end' UI.
app = Flask(__name__, static_folder='public', template_folder='views')

# Set the app secret key from the secret environment variables.
app.secret = os.environ.get('SECRET')

progress = {'percent': 0}
result_data = None
steam_id_for_progress = None

def calculate_with_progress(steam_id):
    global progress, result_data
    progress['percent'] = 0
    wishlisted = SteamApiService.get_wishlisted_result_from_user(steam_id, "tr", progress_callback=progress_callback)
    result_data = wishlisted
    progress['percent'] = 100

def progress_callback(percent):
    global progress
    progress['percent'] = percent

@app.route('/')
def homepage():
    """Displays the homepage."""
    return render_template('index.html')

@app.route('/progress')
def progress_stream():
    def generate():
        last_percent = -1
        while True:
            if progress['percent'] != last_percent:
                last_percent = progress['percent']
                yield f"data: {last_percent}\n\n"
            if last_percent >= 100:
                break
            time.sleep(0.2)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/', methods=['POST'])
def submit():
    global result_data
    data = request.get_json()
    steam_id = data.get('steam_id', 76561198174491595)
    thread = Thread(target=calculate_with_progress, args=(steam_id,))
    thread.start()
    thread.join()  # For simplicity, wait for the thread to finish
    if isinstance(result_data, dict) and result_data.get('error'):
        return jsonify({'error': result_data['error']}), 400
    return jsonify(result_data)


if __name__ == '__main__':
    app.run()
