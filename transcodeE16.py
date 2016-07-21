"""TranscodeE16 handles the interactions with ffmpeg/avconv."""

import subprocess
import logging
import re
import os
import pexpect
import time

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

    def parseTimeToSeconds(self, timeString):
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

            retSeconds = hours * 60 * 60
            retSeconds += minutes * 60
            retSeconds += seconds

            return retSeconds

        else:
            # Format is SS.ms
            secondSplit = timeString.split('.')
            return int(secondSplit[0])

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

    def getDurationSeconds(self, videoUrl):
        """Get the seconds for the video."""
        log.info("Checking for video duration with url: {}".format(videoUrl))

        status = subprocess.run('avconv -i ' + videoUrl, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        log.info(status.stdout)
        p = re.compile('Duration: (.*?),')
        durationSearch = p.search(str(status.stdout))

        if durationSearch:
            group1 = durationSearch.group(1)
            log.info("Found duration: {}".format(group1))

            secs = self.parseTimeToSeconds(group1)

            log.info("Calculated {} seconds for video.".format(secs))

            return secs
        else:
            log.info("Failed to match regex for Duration")
            return 0

    def processFile(self, sourceUrl, jobId, sql):
        """Transcode the file."""
        log.info("Job has started for {} and jobId {}".format(sourceUrl, jobId))

        # Transcode the file
        targetFile = os.path.join(self.data_dir, jobId + ".mp4")

        videoDuration = self.getDurationSeconds(sourceUrl)

        try:

            # Trigger new thread to monitor status
            cmd = "avconv -i " + sourceUrl + " -c:v libx264 -vf scale=1024:768 -strict -2 -profile:v baseline " + targetFile

            startTime = time.time()
            thread = pexpect.spawn(cmd)

            # Update the job status to let the user know it is being transcoded
            sql.update_job_status(jobId, sql.STATUS_TRANSCODING)
            sql.update_job_message(jobId, "Started Transcoding file.")

            # Create a counter to only update the status every 10 attempts
            counter = 0

            cpl = thread.compile_pattern_list([pexpect.EOF, 'time=(.*?) '])
            while True:
                i = thread.expect_list(cpl, timeout=None)
                if i == 0:  # EOF
                    print("Transcoding job finished.")
                    sql.update_job_status(jobId, sql.STATUS_COMPLETE)
                    sql.update_job_percent_complete(jobId, 100)
                    sql.update_job_message(jobId, "Transcoding job finished.")
                    break
                elif i == 1:

                    # Incerement the counter
                    counter = counter + 1

                    # Only update the db on every 10th status
                    if counter == 10:

                        # Reset the counter back to 0
                        counter = 0

                        timeString = thread.match.group(1)
                        print("timeString: {}".format(timeString.decode("utf-8")))
                        currentProcessTime = self.parseTimeToSeconds(timeString.decode("utf-8"))

                        # Calculate percentage
                        percentage = int((currentProcessTime / videoDuration) * 100)
                        print("Current percent complete: {}%".format(percentage))

                        # Update the job status in the DB
                        sql.update_job_percent_complete(jobId, percentage)
                        sql.update_job_message(jobId, "Transcoding job is running and has completed {}%".format(percentage))

                        # Update the processing time in the DB
                        endTime = time.time()
                        uploadElapsedTime = endTime - startTime
                        sql.update_elapsed_time(jobId, int(uploadElapsedTime))

            thread.close()

        except subprocess.CalledProcessError as err:
            log.error("Failed to transcode video: {}".format(err))
            sql.update_job_status(jobId, sql.STATUS_ERROR)
            sql.update_job_message(jobId, "Failed to transcode video: {}".format(err))
