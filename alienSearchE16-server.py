"""Flask Server to run AlienSearchE16 Endpoints."""
import json
import logging
import psutil
import subprocess
import os
import yaml
import time

from threading import Thread
from alienSearchE16 import AlienSearchE16

from flask import Flask

from two1.commands.util import config
from two1.wallet.two1_wallet import Wallet
from two1.bitserv.flask import Payment
from two1.bitrequests import BitTransferRequests

requests = BitTransferRequests(Wallet(), config.Config().username)

app = Flask(__name__)
# app.debug = True

# setup wallet
wallet = Wallet()
payment = Payment(app, wallet)

# hide logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create the alien search obj
alienSearch = AlienSearchE16()


@app.route('/manifest')
def manifest():
    """Provide the app manifest to the 21 crawler."""
    with open('./manifest.yaml', 'r') as f:
        manifest = yaml.load(f)
    return json.dumps(manifest)


@app.route('/status')
@payment.required(10)
def status():
    """
    Get the status from boinccmd.
    """
    try:
        return alienSearch.getStatus()

    except Exception as err:
        log.warning("Failure: {0}".format(err))
        return json.dumps({"success": False, "error": "Error: {0}".format(err)}), 500


@app.route('/run')
@payment.required(2000)
def run():
    """
    Add an hour to the time file and start SETI if it is not running.
    """
    # Calculate an hour in the future
    newTime = time.time() + (60 * 60)

    # Get the current time from the file
    existingTime = alienSearch.getTimeFromFile()
    if existingTime > time.time():
        # Found an existing time in the future, add an hour
        newTime = existingTime + (60 * 60)

    # Write the new time
    alienSearch.writeTimeToFile(str(newTime))

    # Start BOINC if it is not already running
    alienSearch.startSeti()

    return {
        'success': True,
        'message': "SETI will run until {}".format(time.ctime(newTime))
    }


def checkSetiTime():
    """
    Check to see if SETI needs to be stopped or started based on the time file.

    Run every hour.
    """
    while True:
        existingTime = alienSearch.getTimeFromFile()
        if existingTime > time.time():
            alienSearch.startSeti()
        else:
            alienSearch.stopSeti()

        time.sleep(60 * 60)


if __name__ == '__main__':
    import click

    @click.command()
    @click.option("-d", "--daemon", default=False, is_flag=True,
                  help="Run in daemon mode.")
    def start(daemon):
        """Run the server."""
        if daemon:
            pid_file = './AlienSearchE16.pid'
            if os.path.isfile(pid_file):
                pid = int(open(pid_file).read())
                os.remove(pid_file)
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                except:
                    pass
            try:
                p = subprocess.Popen(['python3', 'alienSearch-server.py'])
                open(pid_file, 'w').write(str(p.pid))
            except subprocess.CalledProcessError:
                raise ValueError("error starting alienSearch-server.py daemon")
        else:
            # Start the thread to check on SETI running vs time
            setiCmd = Thread(target=checkSetiTime, daemon=True)
            setiCmd.start()

            print("Server running...")
            app.run(host='0.0.0.0', port=10016)

    start()
