# AlienSearchE16

## Overview
AlienSearchE16 is a bitcoin payable web app designed for the 21 Marketplace to allow clients to pay for the server to run SETI.  If we do find
aliens, I think they would be intrigued with bitcoin.

## Installation
To install, run:

```
$ git clone https://github.com/pooleja/AlienSearchE16.git
$ cd AlienSearchE16
$ sudo ./setup.sh
```

This will install the prerequisite software and set things up.  By default, it will allow only up to 50% of the CPU to be leveraged to prevent
VPS services from killing it.

## How It Works
A client can pay bitcoin to have the server run SETI.  They can also see the status of the node and how much it has contributed to the SETI project.

To get status:
```
$ 21 buy url 'http://0.0.0.0:10016/status'
{
    "hostCredits": "0.210372",
    "state": "SUSPENDED",
    "success": true
}
```

To start SETI:
```
$ 21 buy url 'http://0.0.0.0:10016/run'
{
    "message": "SETI will run until Wed Aug  3 13:56:36 2016",
    "success": true
}

```

Now you will see it is running:
```
$ 21 buy url 'http://0.0.0.0:10016/status'
{
    "hostCredits": "0.210372",
    "state": "RUNNING",
    "success": true
}
```

## Starting and stopping
The service will poll on an hourly basis and see if the current time is before or after the time specified in time.txt.  Every time someone pays
to run the service, it will add an hour to the time in the file (or to the current time) and save that in the file.  This is how it keeps track of
whether it has been paid to run.
