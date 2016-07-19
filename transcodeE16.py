import subprocess
import logging
import re

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

class TranscodeE16:

    def __init__(self, data_dir):
        self.data_dir = data_dir


    def transcoder(self, videoUrl):

        print("Checking for video duration with url: {}".format(videoUrl))
        
        status = subprocess.run('avconv -i ' + videoUrl, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        
        print(status.stdout)
        p = re.compile('Duration: (.*?),')
        durationSearch = p.search(str(status.stdout))

        if durationSearch:
            group1 = durationSearch.group(1)
            print("Found duration: {}".format(group1))

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

            print("Calculated {} minutes for video.".format(retMins))

            return retMins
        else:
            print("Failed to match regex for Duration")
            return 0
