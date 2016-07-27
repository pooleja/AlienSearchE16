# TranscodeE16

## Overview
TranscodeE16 is a bitcoin payable web app designed for the 21 Marketplace to provide video transcoding as a service.  
Clients can request perform the following actions with the service:

* View the current processing status of the service.  This tells the client if the service is working on another job and how many jobs are queued up.
* Get a price quote for a specified video.  This tells the client a price in Satoshis for a video.  Prices are determined by the length of the video that is being quoted.  The default price is 1500 Satoshis per minute of video, but any server running TranscodeE16 can modify this.  Partial minutes are rounded up.
* Start a transcoding job.  The client can request the service to download and transcode a video with the specified transcoding options.
* View the status of a job.  This will tell the client whether the job is queued/running/complete and also give stats about % complete and time.
* Download a completed job.  For a completed job, the client can download the output file.
