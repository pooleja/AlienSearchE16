#!/usr/bin/python3

import hashlib
import time
import os
import random
import string
from speedE16 import SpeedE16

from two1.commands.util import config
from two1.wallet import Wallet
from two1.bitrequests import BitTransferRequests
from two1.bitrequests import BitRequestsError
requests = BitTransferRequests(Wallet(), config.Config().username)

mb = 1024 * 1024
def testClient(target)
    try:

        # Figure out the base paths
        dataDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'client-data')
        baseUrl = 'http://' + target + ':8016'

        # Create the speed testing client
        speed = SpeedE16(dataDir, baseUrl)

        # Generate a 1 MB file with random data in it with a random name
        filename = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
        fullFilePath = os.path.join(dataDir, filename)
        with open(fullFilePath, 'wb') as fout:
            fout.write(os.urandom(mb))

        print("Created temp file: " + fullFilePath)

        uploadData = speed.upload(requests, fullFilePath)

        # Delete the file uploaded file since we don't need it anymore
        os.remove(fullFilePath)
        print("Deleted the temp uploaded file: " + fullFilePath)

        # If the upload succeeded, now test download
        if uploadData['success'] == True:

            print("Upload shows success")

            downloadData = speed.download(requests, uploadData['upload_filename'])

            if downloadData['success'] == True:

                print("Download shows success")

                # Delete the file downloaded file since we don't need it anymore
                os.remove(downloadData['download_path'])
                print("Deleted the temp downloaded file: " + fullFilePath)

                # Compare the hashes to make sure no funny business happened
                if uploadData['digest'] != downloadData['digest']:
                    print("Error: File digests to not match.")
                    print("Uploaded File Digest: " + uploadData['digest'])
                    print("Downloaded File Digest: " + downloadData['digest'])

                # Calculate Mbps - assume 1 MB file
                uploadMbps = 8 / uploadData['time']
                downloadMpbs = 8 / downloadData['time']

                print('Upload Speed: ' + str(uploadMbps) + ' Mbps')
                print('Download Speed: ' + str(downloadMpbs) + ' Mbps')
            else:
                print("Download Failed.")
        else:
            print("Upload Failed.")

    except Exception as err:
        print('Client test failed')
        print("Failure: {0}".format(err))

if __name__ == '__main__':
    import click

    @click.command()
    @click.option("-t", "--target", default="0.0.0.0", help="Target host to run against.")
    def run(target):
        testClient(target)

    run()
