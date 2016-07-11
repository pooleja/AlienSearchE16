import hashlib
import time
import os

chunk_size = 1024

class SpeedE16:

    def __init__(self, data_dir, base_url):
        self.data_dir = data_dir
        self.base_url = base_url


    def upload(self, requests, file):

        # Set the source and dest paths
        dest_url = self.base_url + '/upload'
        source_path = os.path.join(self.data_dir, file)

        # Get the sha256 hash of the file
        with open(source_path, 'rb') as afile:
            beforeDigest = hashlib.sha256(afile.read()).hexdigest()

        print("Generated a hash of the temp file: " + beforeDigest)

        # Upload the file and time it
        with open(source_path, 'rb') as f:
            startTime = time.time()
            r = requests.post(dest_url, files={ 'file': (file, f)}, max_price=5)
            endTime = time.time()
            uploadElapsedTime = endTime - startTime

        print("Uploaded the file.  Elapsed time: " + str(uploadElapsedTime))
        print("Result from upload: " + r.text)

        # Verify the upload was successful
        if r.json()['success'] != True :
            return { 'success' : False }

        retVal = {
            'success': True,
            'time' : uploadElapsedTime,
            'digest' : beforeDigest,
            'upload_filename' : r.json()['filename']
        }

        return retVal


    def download(self, requests, file):

        # Set the source and dest paths
        source_url = self.base_url + '/download?file=' + file
        dest_path = os.path.join(self.data_dir, file)
        print("Downloading: " + source_url + " to: " + dest_path)

        startTime = time.time()
        r = requests.get(source_url, max_price=5)
        with open(dest_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size):
                fd.write(chunk)
        endTime = time.time()
        downloadElapsedTime = endTime - startTime

        print("Downloaded the file.  Elapsed Time: " + str(downloadElapsedTime))

        # Get the downloaded file Hash
        with open(dest_path, 'rb') as afile:
            afterDigest = hashlib.sha256(afile.read()).hexdigest()

        retVal = {
            'success': True,
            'time' : downloadElapsedTime,
            'digest' : afterDigest,
            'download_path' : dest_path
        }

        return retVal

    def remote(self, requests, file, remoteHost):

        # Set the source and dest paths
        remote_url = self.base_url + '/remote?file=' + file + "&host=" + remoteHost

        print("Making remote request: " + remote_url)

        r = requests.get(remote_url, max_price=5)

        print("Remote request completed.")
        
        return r.json()
