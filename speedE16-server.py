#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import psutil
import subprocess
import os
import yaml
import ipaddress

from flask import Flask
from flask import request

from two1.wallet.two1_wallet import Wallet
from two1.bitserv.flask import Payment

from statsE16 import statsE16

app = Flask(__name__)

# setup wallet
wallet = Wallet()
payment = Payment(app, wallet)

# hide logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route('/manifest')
def manifest():
    """Provide the app manifest to the 21 crawler.
    """
    with open('./manifest.yaml', 'r') as f:
        manifest = yaml.load(f)
    return json.dumps(manifest)


@app.route('/download')
@payment.required(5)
def measurement():
    """ Downloads the file requested by the query param

    Returns: HTTPResponse 200 the file payload.
    HTTP Response 404 if the file is not found.
    """

    # Build the path to the file from the current dir + data dir + requested file name
    dataDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
    requestedFile = request.args.get('file')
    filePath = os.path.join(dataDir, requestedFile)

    if os.path.isfile(filePath) != True :
        return 'HTTP Status 404: Requested file not found', 404

    return send_from_directory(dataDir, requestedFile)


if __name__ == '__main__':
    import click

    @click.command()
    @click.option("-d", "--daemon", default=False, is_flag=True,
                  help="Run in daemon mode.")
    def run(daemon):
        if daemon:
            pid_file = './speedE16.pid'
            if os.path.isfile(pid_file):
                pid = int(open(pid_file).read())
                os.remove(pid_file)
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                except:
                    pass
            try:
                p = subprocess.Popen(['python3', 'speedE16-server.py'])
                open(pid_file, 'w').write(str(p.pid))
            except subprocess.CalledProcessError:
                raise ValueError("error starting speedE16-server.py daemon")
        else:
            print("Server running...")
            app.run(host='0.0.0.0', port=8016)

    run()
