"""TranscodeE16 handles the interactions with ffmpeg/avconv."""

import subprocess
import logging
import re
import os
import time
import _thread

log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)


class TranscodeE16:
    """Constructor inputs the dir where to store files."""

    def __init__(self, data_dir):
        """Constructor inputs the dir where to store files."""
        self.data_dir = data_dir

    def parseTimeToMins(self, timeString):
        """Parse out the string to return minutes."""
        # Check to see what format it is in
        if timeString.find(":") > 0:
            # format is HH:MM:SS.MS
            # Split out the duration time and return duration in minutes (in format HH:MM:SS.MS)
            msSplit = timeString.split('.')[0]
            durationSplit = msSplit.split(':')
            hours = int(durationSplit[0])
            minutes = int(durationSplit[1])
            seconds = int(durationSplit[2])

            retMins = hours * 60
            retMins += minutes
            if seconds > 0:
                retMins += 1

            return retMins

        else:
            # Format is SS.ms
            secondSplit = timeString.split('.')
            return int(secondSplit[0]) / 60

    def getDuration(self, videoUrl):
        """Get the minutes for the video."""
        log.info("Checking for video duration with url: {}".format(videoUrl))

        status = subprocess.run('avconv -i ' + videoUrl, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        log.info(status.stdout)
        p = re.compile('Duration: (.*?),')
        durationSearch = p.search(str(status.stdout))

        if durationSearch:
            group1 = durationSearch.group(1)
            log.info("Found duration: {}".format(group1))

            retMins = self.parseTimeToMins(group1)

            log.info("Calculated {} minutes for video.".format(retMins))

            return retMins
        else:
            log.info("Failed to match regex for Duration")
            return 0

    def monitorStatus(self, outputFile, duration):
        """Polling background thread that updates the status of the job."""
        # Check status every 5 seconds
        while self.jobRunning:

            time.sleep(5)

            print("Checking current job status")

            # Read the status file
            statusText = ""
            with open(outputFile, 'r') as fd:
                statusText = fd.read()

            # Search for the status of current time -> time=HH:MM:SS.MS OR time=SS.MS
            p = re.compile('time=(.*?) ')
            timeSearch = p.search(statusText)

            # Check to see if we found the time
            if timeSearch:
                timeString = timeSearch.group(1)

                currentProcessTime = self.parseTimeToMins(timeString)

                # Calculate percentage
                percentage = currentProcessTime / duration
                print("Current percent complete: {}".format(percentage))

            else:
                log.warning("Did not find the time status in output file... something may have gone wrong")

        print("Exiting monitorStatus")

    def processFile(self, sourceUrl, jobId):
        """Transcode the file."""
        log.info("Job has started for {} and jobId {}".format(sourceUrl, jobId))

        # Transcode the file
        targetFile = os.path.join(self.data_dir, jobId + ".mp4")
        outputFile = os.path.join(self.data_dir, jobId + ".out")

        videoDuration = self.getDuration(sourceUrl)

        try:
            # Open the output file where status will go
            with open(outputFile, 'w') as fd:

                # Trigger new thread to monitor status
                self.jobRunning = True
                _thread.start_new_thread(self.monitorStatus, (outputFile, videoDuration))

                subprocess.check_call([
                        "avconv",
                        "-i",
                        sourceUrl,
                        "-c:v",
                        "libx264",
                        "-vf",
                        "scale=1024:768",
                        "-strict",
                        "-2",
                        "-profile:v",
                        "baseline",
                        targetFile
                    ],
                    stderr=subprocess.STDOUT,
                    stdout=fd)
        except subprocess.CalledProcessError as err:
            log.error("Failed to transcode video: {}".format(err))

        self.jobRunning = False
