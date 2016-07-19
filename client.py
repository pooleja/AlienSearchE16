
import logging
import os
from transcodeE16 import TranscodeE16

from two1.commands.util import config
from two1.wallet import Wallet
from two1.bitrequests import BitTransferRequests
from two1.bitrequests import BitRequestsError
requests = BitTransferRequests(Wallet(), config.Config().username)

log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)

def testDuration():
    try:
        log.warning("In testDuration()")
        dataDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

        # Create the speed testing client
        transcoder = TranscodeE16(dataDir)
        duration = transcoder.getDuration('http://www.esixteen.co/video/sample.mp4')

        log.info("Success!")
        log.info("Duration test completed with duration: {}", duration  )

    except Exception as err:
        log.warning('Client test failed')
        log.warning("Failure: {0}".format(err))

if __name__ == '__main__':
    import click

    @click.command()
    @click.option('--duration', is_flag=True)
    def run(duration):

        if duration:
            testDuration()

    run()
