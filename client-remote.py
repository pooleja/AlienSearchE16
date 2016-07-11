#!/usr/bin/python3

import hashlib
import time
import os
import os.path
import random
import string
from speedE16 import SpeedE16

from two1.commands.util import config
from two1.wallet import Wallet
from two1.bitrequests import BitTransferRequests
from two1.bitrequests import BitRequestsError
requests = BitTransferRequests(Wallet(), config.Config().username)

mb = 1024 * 1024

def outputResult(file, result):

    if os.path.exists(file):
        os.remove(file)

    with open(file, 'wb') as f:
        f.write(json.dumps(result, indent=4, sort_keys=True))


def testClientServer(clientHost, serverHost, output):
    try:

        # Figure out the base paths
        dataDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'client-data')
        clientBaseUrl = "http://" + clientHost + ":8016"
        serverBaseUrl = "http://" + serverHost + ":8016"

        # Create the speed testing client
        clientSpeed = SpeedE16(dataDir, clientBaseUrl)
        serverSpeed = SpeedE16(dataDir, serverBaseUrl)

        # Generate a 1 MB file with random data in it with a random name
        filename = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
        fullFilePath = os.path.join(dataDir, filename)
        with open(fullFilePath, 'wb') as fout:
            fout.write(os.urandom(mb))

        print("Created temp file: " + fullFilePath)

        uploadData = serverSpeed.upload(requests, fullFilePath)

        # Delete the file uploaded file since we don't need it anymore
        os.remove(fullFilePath)
        print("Deleted the temp uploaded file: " + fullFilePath)

        # If the upload succeeded, now test download
        if uploadData['success'] == True:

            print("Upload shows success")

            downloadData = clientSpeed.remote(requests, uploadData['upload_filename'], '10.244.119.122')

            if downloadData['success'] == True:

                print("Remote request shows success")

                # Compare the hashes to make sure no funny business happened
                if uploadData['digest'] != downloadData['digest']:
                    print("Error: File digests to not match.")
                    print("Uploaded File Digest: " + uploadData['digest'])
                    print("Downloaded File Digest: " + downloadData['digest'])
                    outputResult(output, {'success' : False, 'message': 'Hashes do not match.'})
                    return

                # Calculate Mbps - assume 1 MB file
                uploadMbps = 8 / uploadData['time']
                downloadMpbs = 8 / downloadData['time']

                print('Upload Speed: ' + str(uploadMbps) + ' Mbps')
                print('Download Speed: ' + str(downloadMpbs) + ' Mbps')

                outputResult(output, {'success' : True, "uploadMbps": uploadMbps, 'downloadMpbs': downloadMpbs})
            else:
                print("Download Failed.")
                outputResult(output, {'success' : False, 'message': 'Download Failed.'})
        else:
            print("Upload Failed.")
            outputResult(output, {'success' : False, 'message': 'Upload Failed.'})

    except Exception as err:
        print('Client test failed')
        print("Failure: {0}".format(err))
        outputResult(output, {'success' : False, 'message': "Failure: {0}".format(err)})



if __name__ == '__main__':
    import click

    @click.command()
    @click.option("-c", "--client", default="0.0.0.0", help="Host that will try and download a file from the Server.")
    @click.option("-s", "--server", default="0.0.0.0", help="Host where the file will be uploaded to.")
    @click.option("-o", "--output", default="output.json", help="File where JSON output data will be written.")
    def run(client, server, output):

        if client == server:
            print("Client and Server must be specified and different than the default")
            return

        print("Running upload/download test against client: " + client + " and server: " + server)
        testClientServer(client, server, output)

    run()
