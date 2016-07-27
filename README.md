# TranscodeE16

## Overview
TranscodeE16 is a bitcoin payable web app designed for the 21 Marketplace to provide video transcoding as a service.  Clients can perform the following actions with the service:

* View the current processing status of the service.  This tells the client if the service is working on another job and how many jobs are queued up.
* Get a price quote for a specified video.  This tells the client a price in Satoshis for a video.  Prices are determined by the length of the video that is being quoted.  The default price is 1500 Satoshis per minute of video, but any server running TranscodeE16 can modify this.  Partial minutes are rounded up.
* Start a transcoding job.  The client can request the service to download and transcode a video with the specified transcoding options.
* View the status of a job.  This will tell the client whether the job is queued/running/complete and also give stats about % complete and time.
* Download a completed job.  For a completed job, the client can download the output file.

## Installation
TranscodeE16 requires a few 3rd party libraries and python packages in order to run.  Support has been verified on Raspberry Pi and Ubuntu using the setup script.  To get things up and running:

```
$ git clone https://github.com/pooleja/TranscodeE16.git
$ cd TranscodeE16
$ ./setup.sh
```

Next, start up the server:
```
$ python3 transcodeE16-server.py -d
Connecting to DB.
Checking to see if any files need to be cleaned up in 'server-data' folder.
Sleeping for an hour befor cleaning up folder again.
Server running...
```

Next, verify it works by checking the server status url:
```
$ 21 buy http://localhost:9016/server-status
{
    "numQueudJobs": 0,
    "numRunningJobs": 0,
    "success": true
}
```
## Make Sure it Stays Running
To ensure the server stays running across reboots, you can create a reboot cron job.  This will ensure TranscodeE16 will be restarted any time the device comes back online.

To open the cron file:
```
$ crontab -e
```

Edit the file and add a reboot line (replace the path):
```
@reboot cd /your/path/to/TranscodeE16/ && python3 transcodeE16-server.py -d
```

Now you can reboot the device and ensure it is running:
```
$ ps aux | grep python3
twenty     545  2.2  2.5  39928 25884 ?        Sl   17:35   0:07 python3 transcodeE16-server.py
```
