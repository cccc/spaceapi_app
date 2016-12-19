#!/usr/bin/env python2.7
# -*- coding: utf8 -*-

"""
A simple forwarder to display the C4's open state on our webserver.

Send a POST request to the '/newstate' endpoint to update state information.

The 'message' field may be an empty string, in which case it will not be
included in the final json.

Request is only accepted if the correct password (shared secret) is supplied.
The password is loaded from a file called 'local_creds.py'. You need to create
this file with a contents of 'pw = "sharedsecret"'.

EXAMPLE UPDATE CODE:
    >>> from urllib import request
    >>> request.urlopen('http://localhost:5000/newstate', data=b'password=sharedsecret&state=open&message=Hello World!').read()
    >>> request.urlopen('http://localhost:5000/newstate', data=b'password=sharedsecret&state=closed&message=').read()

DB SETUP:
    >>> from spaceapi_app import db
    >>> db.create_all()
"""

from flask import Flask, request, redirect, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
import calendar
import time
import sys

try:
    import local_creds
except:
    print('ERROR: local_creds.py not found.\n')
    print(__doc__)
    sys.exit(1)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
app.config.from_object(__name__)
db = SQLAlchemy(app)

if not app.debug:
    import logging
    from logging import FileHandler
    file_handler = FileHandler("production.log")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)


class ClubState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    open = db.Column(db.Boolean)
    message = db.Column(db.String)

    def __init__(self, open, message=''):
        self.open = open
        # utc timestamp
        self.time = calendar.timegm(time.gmtime()) # python2
        #self.time = int(datetime.now(tz=datetime.timezone.utc).timestamp())
        self.message = message

    def __repr__(self):
        if self.open:
            s = 'open'
        else:
            s = 'closed'
        return '<State %s / %s from %d>' % (s, repr(self.message), self.time)

def make_space_json(state):
    d = {
            'api': '0.13,',
            'space': 'CCC Cologne',
            'logo': 'https://koeln.ccc.de/images/C4-logo_transparent_black.svg',
            'url': 'https://koeln.ccc.de/',
            'ext_ccc': "erfa",
            'location': {
                    'address': 'Chaos Computer Club Cologne (c4) e.V., Heliosstr. 6a, 50825 Köln, Germany',
                    'lat': 50.9504142,
                    'lon': -6.9129647,
                },
            'state': {
                    'open': None,
                    'lastchange': None,
#                'icon': {'open':'url','closed':'url'},
                },
            'contact': {
                    'irc': 'irc://irc.freenode.org/#cccc',
                    'email': 'mail@koeln.ccc.de',
                    'twitter': '@ccc_koeln',
                    'phone': '+49 221-49 24 119',
                },
            'issue_report_channels': ['twitter'], #XXX
            'feeds': {
                'blog': { 'type': 'rss', 'url': 'https://koeln.ccc.de/backend/updates.rdf' },
#                'wiki': { 'type': '', 'url': '' },
#                'calendar': { 'type': '', 'url': '' },
                },
            'projects': [
                    'https://github.com/cccc',
                ],
        }
    if state is not None:
        d['state']['open'] = state.open
        d['state']['lastchange'] = state.time
        if state.message:
            d['state']['message'] = state.message
    return d

@app.route("/")
def state():
    current_state = ClubState.query.order_by("-id").first()

    d = make_space_json(current_state)
    return jsonify(**d)


@app.route("/newstate", methods=["POST", ])
def save():
    if request.method == "GET" or request.form["password"] != local_creds.pw:
        return "FAil", 500
    try:
        newstate = ClubState(request.form['state'] == 'open',
                             request.form['message'])
        db.session.add(newstate)
        db.session.commit()
    except:
        return "Faiil.", 500
    return redirect("/done")


@app.route("/done")
def done():
    return "Success"

if __name__ == "__main__":
    app.run(debug=True)
