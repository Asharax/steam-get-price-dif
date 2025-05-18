#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template, jsonify
import SteamApiService

# Support for gomix's 'front-end' and 'back-end' UI.
app = Flask(__name__, static_folder='public', template_folder='views')

# Set the app secret key from the secret environment variables.
app.secret = os.environ.get('SECRET')

@app.route('/')
def homepage():
    """Displays the homepage."""
    return render_template('index.html')


@app.route('/', methods=['POST'])
def submit():
    """returns the price difference.
    """
    data = SteamApiService.price_dif()
    # Return the list of remembered dreams.
    return jsonify(data)


if __name__ == '__main__':
    app.run()
