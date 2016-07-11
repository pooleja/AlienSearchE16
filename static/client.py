#!/usr/bin/python3

import hashlib
import time
import os
import random
import string

from two1.commands.util import config
from two1.wallet import Wallet
from two1.bitrequests import BitTransferRequests
from two1.bitrequests import BitRequestsError
requests = BitTransferRequests(Wallet(), config.Config().username)

baseUrl = 'http://0.0.0.0:8016'
baseDownloadUrl = baseUrl + '/download?file='
uploadUrl = baseUrl + '/upload'

mb = 1024 * 1024

try:
    print("Testing upload and download speed against: " + baseUrl)

    # Generate a 1 MB file with random data in it with a random name
    dataDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
    filename = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
    fullFilePath = os.path.join(dataDir, filename)
    with open(fullFilePath, 'wb') as fout:
        fout.write(os.urandom(mb))

    print("Created temp file: " + fullFilePath)

    # Get the sha256 hash of the file
    with open(fullFilePath, 'rb') as afile:
        beforeDigest = hashlib.sha256(afile.read()).hexdigest()

    print("Generated a hash of the temp file: " + beforeDigest)

    # Upload the file and time it
    with open(fullFilePath, 'rb') as f:
        startTime = time.time()
        r = requests.post(uploadUrl, files={ 'file': (filename, f)}, max_price=5)
        endTime = time.time()
        uploadElapsedTime = endTime - startTime

    print("Uploaded the file.  Elapsed time: " + str(uploadElapsedTime))

    # Delete the file
    os.remove(fullFilePath)

    print("Deleted the temp file")
    print("Result from upload: " + r.text)


    # Verify the upload was successful
    if r.json()['success'] != True :
        print("Upload Failed: " + r.text)

    print("Upload shows success")
    
    # Get the download url to use from the upload request
    downloadFileName = r.json()['filename']
    downloadUrl = baseDownloadUrl + downloadFileName
    print("Download URL: " + downloadUrl)

    # Download the file and time it
    startTime = time.time()
    content = requests.get(downloadUrl, max_price=5).content
    endTime = time.time()
    downloadElapsedTime = endTime - startTime

    print("Downloaded the file.  Elapsed Time: " + str(downloadElapsedTime))

    # Verify sha256 hashes match
    afterDigest = hashlib.sha256(content).hexdigest()
    if beforeDigest != afterDigest:
        print("Error: File digests to not match.")
        print("Before Digest: " + beforeDigest)
        print("After Digest: " + afterDigest)

    print("Verified the sha256 hashes match.")

    # Calculate Mbps - assume 1 MB file
    uploadMbps = 8 / downloadElapsedTime
    downloadMpbs = 8 / downloadElapsedTime

    print('Upload Speed: ' + str(uploadMbps) + ' Mbps')
    print('Download Speed: ' + str(downloadMpbs) + ' Mbps')

except Exception as err:
    print('Client test failed')
    print("Failure: {0}".format(err))
