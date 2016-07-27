# TranscodeE16

## Overview
TranscodeE16 is a bitcoin payable web app designed for the 21 Marketplace to provide video transcoding as a service.  Clients can perform the following actions with the service:

* View the current processing status of the service.  This tells the client if the service is working on another job and how many jobs are queued up.
* Get a price quote for a specified video.  This tells the client a price in Satoshis for a video.  Prices are determined by the length of the video that is being quoted.  The default price is 1500 Satoshis per minute of video, but any server running TranscodeE16 can modify this.  Partial minutes are rounded up.
* Start a transcoding job.  The client can request the service to download and transcode a video with the specified transcoding options.
* View the status of a job.  This will tell the client whether the job is queued/running/complete and also give stats about % complete and time.
* Download a completed job.  For a completed job, the client can download the output file.

## Installation
### Run the setup script
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
### Make Sure it Stays Running
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

## How it works
Behind the scenes, TranscodeE16 uses avconv/ffmpeg to convert a video for the client.  Only one transcoding job is allowed to run at a time and any other jobs get queued up.  To keep track of job status it uses a SQLite database named "jobs.db" that is created by the setup script.

On startup it will see if there were any previously queued or running jobs and restart them to guard against an app crash or server reboot.

When the client submits a job, they can specify among 3 video sizes:
* 1080p
* 720p
* 480p

The transcoding size specified will determine the height of the output video and the width will be automatically determined to ensure the aspect ratio of the original video is maintained. 

All transcoded videos will use an MP4 container, use the H.264 video codec with the 'baseline" profile, and use the AAC encoder for audio.


## Example
The client can check to see if the service is ready to process jobs:
```
$ 21 buy url 'http://localhost:9016/server-status'
{
    "numQueudJobs": 0,
    "numRunningJobs": 0,
    "success": true
}
```
No jobs are running, so the client can get a price quote for a video:
```
$ 21 buy url 'http://localhost:9016/price?url=https://www.esixteen.co/video/sample.mp4'
{
    "minutes": 4,
    "price": 6000,
    "pricePerMin": 1500,
    "success": true
}
```
Note that the client specified a video url where the service can grab the video from.  Also note that the pricing scheme is explained.  It will cost 6000 Satoshis to transcode this video.

Next, request the transcoding job to run against this video:
```
$ 21 buy url 'http://10.244.119.122:9016/transcode?url=http://www.esixteen.co/video/sample.mp4&scale=480p'
{
    "jobId": "UGD2HYU4CTPE6DVCCJB3",
    "message": "Transcoding job has started.",
    "success": true
}
```
Note that the client has pointed the service at a video URL and also specified that the output should be 480 pixels tall.  If this 'scale' parameter is not specified, it will default to 1080p.

Since the job has started, the client can request status about the job using the jobId returned from the previous request:
```
$ 21 buy url 'http://localhost:9016/job-status?jobId=UGD2HYU4CTPE6DVCCJB3'
{
    "JobCompletionTime": 34.0,
    "Message": "Transcoding job is running and has completed 20%",
    "PercentComplete": 20.0,
    "Status": "STATUS_TRANSCODING",
    "jobId": "UGD2HYU4CTPE6DVCCJB3",
    "success": true
}
```
Here we can see that the job is 20% complete.  When the job is complete, the job status call will return STATUS_COMPLETE:
```
$ 21 buy url 'http://localhost:9016/job-status?jobId=UGD2HYU4CTPE6DVCCJB3'
{
    "JobCompletionTime": 158.0,
    "Message": "Transcoding job finished.",
    "PercentComplete": 100.0,
    "Status": "STATUS_COMPLETE",
    "jobId": "UGD2HYU4CTPE6DVCCJB3",
    "success": true
}
```
Since the job has completed, the client can now download the transcoded file and save it locally:
```
$ 21 buy url 'http://localhost:9016/download?jobId=UGD2HYU4CTPE6DVCCJB3' -o ./sample.mp4
```
