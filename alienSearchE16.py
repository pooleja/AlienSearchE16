"""AlienSearchE16 handles the interactions with BOINC."""

import logging
import os
import threading
import subprocess
import re

log = logging.getLogger('werkzeug')

# Job lock for multithreaded use case
file_rlock = threading.RLock()
timeFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'time.txt')


class AlienSearchE16:
    """Class to maintain the SETI process."""

    def __init__(self):
        """Nothing here."""

    def getTimeFromFile(self):
        """
        Read the time file grab the time string.  If the time file does not exist, return 0.
        """
        try:
            with file_rlock:
                with open(timeFile, "r") as myfile:
                    data = myfile.readlines()

                if data:
                    return int(data[0])
                else:
                    return 0
        except Exception:
            return 0

    def writeTimeToFile(self, timeString):
        """
        Write the time to the file.
        """
        with file_rlock:

            # Delete the existing file if it exists
            if os.path.isfile(timeFile):
                os.remove(timeFile)

            # Write the new file
            with open(timeFile, "w") as myfile:
                myfile.write(timeString)

    def startSeti(self):
        """
        Call resume on boinccmd.
        """
        subprocess.call('boinccmd --project http://setiathome.berkeley.edu resume', shell=True)

    def stopSeti(self):
        """
        Call suspend on boinccmd.
        """
        subprocess.call('boinccmd --project http://setiathome.berkeley.edu suspend', shell=True)

    def getStatus(self):
        """
        Call boinccmd --get_simple_gui_info and parse the results.
        """
        try:
            # Run the status cmd
            output = subprocess.check_output('boinccmd --get_simple_gui_info', shell=True, stderr=subprocess.STDOUT)

            # See if the UI shows it as suspended
            state = "RUNNING"
            if str(output).find("suspended via GUI: yes") > 0:
                state = "SUSPENDED"

            nodeCredits = '0'
            p = re.compile('host_total_credit: (\d+\.?\d*)')
            creditSearch = p.search(str(output))
            log.debug(creditSearch)
            if creditSearch:
                nodeCredits = creditSearch.group(1)

            return {
                'success': True,
                'state': state,
                'hostCredits': nodeCredits
            }

        except subprocess.CalledProcessError as err:
            log.error(err)
            return {
                'success': False,
                'message': "Failed to get boinccmd status: {}".format(err)
            }
