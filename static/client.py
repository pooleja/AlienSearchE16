#!/usr/bin/python3

import hashlib
import time

from two1.commands.util import config
from two1.wallet import Wallet
from two1.bitrequests import BitTransferRequests
from two1.bitrequests import BitRequestsError
requests = BitTransferRequests(Wallet(), config.Config().username)


url = "http://0.0.0.0:8016/download/test1234"

mb = 1024 * 1024

try:

    # Download the file and time it
    startTime = time.time()
    content = requests.get(url, max_price=5).content
    endTime = time.time()

    # Calculate Mbps - assume 1 MB file
    elapsedTime = endTime - startTime
    mpbs = 8 / elapsedTime

    digest = hashlib.sha256(content).hexdigest()

    print('Buy call succeeded.')
    print('Digest: ' + digest)
    print('Speed: ' + mpbs + ' Mbps')

except Exception as err:
    print('Buy call failed')
    print("Failure: {0}".format(err))
