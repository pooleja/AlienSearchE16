import subprocess
import logging
import re

log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)

class TranscodeE16:

    def __init__(self, data_dir):
        self.data_dir = data_dir


    def transcoder(self, videoUrl):

        log.info("Checking for video duration with url: {}".format(videoUrl))

        durationOutput = subprocess.check_output(['avconv', '-i', videoUrl, '2>&1'])
        p = re.compile('/Duration: (.*?),/')
        durationSearch = p.search(durationOutput)

        if durationSearch:
            group1 = durationSearch.group(1)
            log.info("Found duration: {}".format(group1))

            # Split out the duration time and return duration in minutes (in format HH:MM:SS.MS)
            msSplit = group1.split('.')[0]
            durationSplit = msSplit.split(':')
            hours = int(durationSplit[0])
            minutes = int(durationSplit[1])
            seconds = int(durationSplit[2])

            retMins = hours * 60
            retMins += minutes
            if seconds > 0:
                retMins += 1

            log.info("Calculated {} minutes for video.".format(retMins))

            return retMins
        else:
            return 0
