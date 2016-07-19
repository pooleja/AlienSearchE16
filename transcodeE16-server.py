#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import psutil
import subprocess
import os
import yaml
import ipaddress
import string
import random
import glob
import time

from flask import Flask
from flask import request
from flask import send_from_directory

from two1.commands.util import config
from two1.wallet.two1_wallet import Wallet
from two1.bitserv.flask import Payment
from two1.bitrequests import BitTransferRequests
from two1.bitrequests import BitRequestsError
requests = BitTransferRequests(Wallet(), config.Config().username)

from transcodeE16 import TranscodeE16

app = Flask(__name__)

# setup wallet
wallet = Wallet()
payment = Payment(app, wallet)

# hide logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

dataDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'server-data')

# Cost per minute for transcoding jobs - approx 1 cent per min
SATOSHI_PER_MIN_PRICE = 1500

@app.route('/manifest')
def manifest():
    """Provide the app manifest to the 21 crawler.
    """
    with open('./manifest.yaml', 'r') as f:
        manifest = yaml.load(f)
    return json.dumps(manifest)


@app.route('/price')
@payment.required(1)
def price():
    """ Calculates the price for transcoding the video specified in 'url' query param

    Returns: HTTPResponse 200 with the details about price.
    HTTP Response 404 if the file is not found.
    HTTP Response 500 if an error is encountered.
    """

    # Get the URL to the file being requested
    requestedFile = request.args.get('url')

    log.info("Price info requested for URL: {}.".format(requestedFile))

    try:
        # Create the transcoding helper class
        transcoder = TranscodeE16(dataDir)
        duration = transcoder.getDuration(requestedFile)

        # An error occurred if we could not get a valid duration
        if duration == 0:
            log.warning("Failure: Could not determine the length of the video file")
            return json.dumps({ "success": False, "error": "Failure: Could not determine the length of the video file"}), 500

        log.info("Duration query of video completed with duration: {}", duration)
        return json.dumps({
            "success": True,
            "price": duration * SATOSHI_PER_MIN_PRICE,
            "minutes": duration,
            "pricePerMin":  SATOSHI_PER_MIN_PRICE
        })

    except Exception as err:
        log.warning("Failure: {0}".format(err))
        return json.dumps({ "success": False, "error": "Error: {0}".format(err) }), 404



if __name__ == '__main__':
    import click

    @click.command()
    @click.option("-d", "--daemon", default=False, is_flag=True,
                  help="Run in daemon mode.")
    def run(daemon):
        if daemon:
            pid_file = './transcodeE16.pid'
            if os.path.isfile(pid_file):
                pid = int(open(pid_file).read())
                os.remove(pid_file)
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                except:
                    pass
            try:
                p = subprocess.Popen(['python3', 'transcodeE16-server.py'])
                open(pid_file, 'w').write(str(p.pid))
            except subprocess.CalledProcessError:
                raise ValueError("error starting transcodeE16-server.py daemon")
        else:
            print("Server running...")
            app.run(host='0.0.0.0', port=9016)

    run()
