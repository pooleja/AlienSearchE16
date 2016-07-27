"""Flask Server to run TranscodeE16 Endpoints."""
import json
import logging
import psutil
import subprocess
import os
import yaml
import string
import random
import threading
import glob
import time
from transcodeE16 import TranscodeE16
from sqldb import TranscodeJobsSQL
from threading import Thread

from flask import Flask
from flask import request
from flask import send_from_directory

from two1.commands.util import config
from two1.wallet.two1_wallet import Wallet
from two1.bitserv.flask import Payment
from two1.bitrequests import BitTransferRequests
requests = BitTransferRequests(Wallet(), config.Config().username)

app = Flask(__name__)
app.debug = True

# setup wallet
wallet = Wallet()
payment = Payment(app, wallet)

# hide logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

dataDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'server-data')

# Valid scales that the transcoder will support
validScales = ['1080p', '720p', '480p']

# Cost per minute for transcoding jobs - approx 1 cent per min
SATOSHI_PER_MIN_PRICE = 1500

# Create the DB connection
sql = TranscodeJobsSQL()


@app.route('/manifest')
def manifest():
    """Provide the app manifest to the 21 crawler."""
    with open('./manifest.yaml', 'r') as f:
        manifest = yaml.load(f)
    return json.dumps(manifest)


@app.route('/price')
@payment.required(10)
def price():
    """Calculate the price for transcoding the video specified in 'url' query param.

    Returns: HTTPResponse 200 with the details about price.
    HTTP Response 404 if the file is not found.
    HTTP Response 500 if an error is encountered.
    """
    try:

        duration = get_video_duration(request)

        # An error occurred if we could not get a valid duration
        if duration == 0:
            log.warning("Failure: Could not determine the length of the video file")
            return json.dumps({"success": False, "error": "Failure: Could not determine the length of the video file"}), 500

        log.info("Duration query of video completed with duration: {}", duration)

        return json.dumps({
            "success": True,
            "price": duration * SATOSHI_PER_MIN_PRICE,
            "minutes": duration,
            "pricePerMin": SATOSHI_PER_MIN_PRICE
        })

    except Exception as err:
        log.warning("Failure: {0}".format(err))
        return json.dumps({"success": False, "error": "Error: {0}".format(err)}), 404


def get_transcode_price(request):
    """Calculate the price."""
    duration = get_video_duration(request)

    return duration * SATOSHI_PER_MIN_PRICE


def run_job(jobId, sourceUrl, scale):
    """
    Run the transcoding job in a new thread.
    """
    # Create the entry in the job table
    sql.update_job_status(jobId, sql.STATUS_QUEUED)
    sql.update_job_message(jobId, "Job queued for processing.")

    # In the background kick off the download and transcoding
    transcoder = TranscodeE16(dataDir)
    threading.Thread(target=transcoder.processFile,
                     args=(sourceUrl, jobId, sql, scale)
                     ).start()


@app.route('/transcode')
@payment.required(get_transcode_price)
def transcode():
    """
    Transcode the video.

    Transcodes the video specified in the 'url' query param (required).
    Uses the configuration specified in the 'scale' query param [1080p, 720p, 480p] (not required, defaults to 1080p).

    Returns: HTTPResponse 200 with the details about price.
    HTTP Response 404 if the file is not found.
    HTTP Response 500 if an error is encountered.
    """
    # Get the URL to the file being requested
    sourceUrl = request.args.get('url')

    # Get the profile to use
    scale = validScales[0]
    val = request.args.get('scale')
    if val in validScales:
        scale = val

    # Generate a random file name for the output of the transcoding job
    jobId = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))

    # Create the entry in the job table
    sql.insert_new_job((jobId, sourceUrl, sql.STATUS_QUEUED, "Job queued for processing.", 0, 0, scale))

    # Start the job
    run_job(jobId, sourceUrl, scale)

    # Return success of started job and the ID to use to query status
    return json.dumps({
        "success": True,
        "jobId": jobId,
        "message": "Transcoding job has started."
    })


@app.route('/job-status')
@payment.required(10)
def job_status():
    """
    Get the status of the requested job.
    """
    # Get the job ID that is being requested.
    requestedJob = request.args.get('jobId')
    print("Status requested for job {}".format(requestedJob))

    try:

        info = sql.get_job_info(requestedJob)

        return json.dumps({
            "success": True,
            "jobId": info[0],
            "Status": info[2],
            "Message": info[3],
            "PercentComplete": info[4],
            "JobCompletionTime": info[5]
        })

    except Exception as err:
        log.warning("Failure: {0}".format(err))
        return json.dumps({"success": False, "error": "Error: {0}".format(err)}), 500


@app.route('/server-status')
@payment.required(10)
def server_status():
    """
    Get the number of queued and running jobs so the client knows whether it can run immediately or there will be a lag.
    """
    try:

        queuedJobs = sql.get_jobs_with_status(sql.STATUS_QUEUED)
        runningJobs = sql.get_jobs_with_status(sql.STATUS_TRANSCODING)

        return json.dumps({
            "success": True,
            "numQueudJobs": len(queuedJobs),
            "numRunningJobs": len(runningJobs)
        })

    except Exception as err:
        log.warning("Failure: {0}".format(err))
        return json.dumps({"success": False, "error": "Error: {0}".format(err)}), 500


@app.route('/download')
@payment.required(10)
def download():
    """
    Returns the file specified in the jobId param.

    Throws a 404 if the job is not found.
    Throws a 500 if the job is not completed or errored out.
    """
    # Get the job ID that is being requested.
    requestedJob = request.args.get('jobId')
    print("Download requested for job {}".format(requestedJob))

    try:

        # Query for the job info
        info = sql.get_job_info(requestedJob)

        log.debug("Got job info.")

        # Make sure they requested a valid job
        if info:

            # Get the status of the job
            jobStatus = info[2]

            # Check if the job is still running
            if (jobStatus == sql.STATUS_QUEUED) or (info == sql.STATUS_TRANSCODING):
                return json.dumps({"succes": False, "error": "Job has not completed yet"}), 500

            # Check if the job failed
            if jobStatus == sql.STATUS_ERROR:
                return json.dumps({"succes": False, "error": "Transcoding job failed: {}".format(info[3])}), 500

            # Return the file
            return send_from_directory(dataDir, "{}.mp4".format(requestedJob))

        else:
            # Job was not found
            return json.dumps({"succes": False, "error": "JobId {} not found."}.format(requestedJob)), 404

    except Exception as err:
        log.warning("Failure: {0}".format(err))
        return json.dumps({"success": False, "error": "Error: {0}".format(err)}), 500


def get_video_duration(request):
    """
    Get the duration.
    """
    # Get the URL to the file being requested
    requestedFile = request.args.get('url')

    log.info("Getting duration requested for URL: {}.".format(requestedFile))

    # Create the transcoding helper class
    transcoder = TranscodeE16(dataDir)
    duration = transcoder.getDuration(requestedFile)

    log.info("Duration query of video completed with duration: {}", duration)
    return duration


def cleanup_data_dir():
    """
    Cleans up the data dir and removes any files older than 24 hours.
    """
    while True:
        print("Checking to see if any files need to be cleaned up in \'server-data\' folder.")
        # Clear out any old uploaded files that are older than an 24 hours
        delete_before_time = time.time() - (60 * 60 * 24)
        files = glob.glob(os.path.join(dataDir, "*"))
        for file in files:
            if file.endswith(".mp4") is True and os.path.isfile(file) is True:
                if os.path.getmtime(file) < delete_before_time:
                    print("Removing old file: " + file)
                    os.remove(file)

        # Sleep for an hour in this loop
        print("Sleeping for an hour befor cleaning up folder again.")
        time.sleep(60 * 60)


def restart_previously_running_jobs():
    """
    Any jobs that were running or queued up previously should be restarted.
    """
    jobs = sql.get_previously_running_jobs()
    for job in jobs:

        # If there was a previous job running it may have a partial output file. Delete it before restart.
        jobFile = os.path.join(dataDir, "{}.mp4".format(job[0]))
        if os.path.isfile(jobFile):
            print("Removing previous partial job file: {}".format(jobFile))
            os.remove(jobFile)

        # Kick off the transcoding again
        print("Restarting job {}".format(job[0]))
        run_job(job[0], job[1], job[6])


if __name__ == '__main__':
    import click

    @click.command()
    @click.option("-d", "--daemon", default=False, is_flag=True,
                  help="Run in daemon mode.")
    def run(daemon):
        """Run the server."""
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
            # Start cleanup thread
            cleaner = Thread(target=cleanup_data_dir, daemon=True)
            cleaner.start()

            # Restart the threads for any jobs that were queued up or previously running
            restart_previously_running_jobs()

            print("Server running...")
            app.run(host='0.0.0.0', port=9016)

    run()
