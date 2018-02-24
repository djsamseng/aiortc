import asyncio
import logging
from unittest import TestCase

from aiowebrtc import RTCPeerConnection


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def track_states(pc):
    states = {
        'iceConnectionState': [pc.iceConnectionState],
        'iceGatheringState': [pc.iceGatheringState],
    }

    @pc.on('iceconnectionstatechange')
    def iceconnectionstatechange():
        states['iceConnectionState'].append(pc.iceConnectionState)

    @pc.on('icegatheringstatechange')
    def icegatheringstatechange():
        states['iceGatheringState'].append(pc.iceGatheringState)

    return states


class RTCPeerConnectionTest(TestCase):
    def test_connect(self):
        pc1 = RTCPeerConnection()
        pc1_states = track_states(pc1)

        pc2 = RTCPeerConnection()
        pc2_states = track_states(pc2)

        self.assertEqual(pc1.iceConnectionState, 'new')
        self.assertEqual(pc1.iceGatheringState, 'new')
        self.assertEqual(pc2.iceConnectionState, 'new')
        self.assertEqual(pc2.iceGatheringState, 'new')

        # create offer
        offer = run(pc1.createOffer())
        run(pc1.setLocalDescription(offer))
        self.assertEqual(pc1.iceConnectionState, 'new')
        self.assertEqual(pc1.iceGatheringState, 'complete')
        self.assertEqual(offer['type'], 'offer')

        # create answer
        run(pc2.setRemoteDescription(offer))
        answer = run(pc2.createAnswer())
        run(pc2.setLocalDescription(answer))
        self.assertEqual(pc2.iceConnectionState, 'checking')
        self.assertEqual(pc2.iceGatheringState, 'complete')
        self.assertEqual(answer['type'], 'answer')

        # handle answer
        run(pc1.setRemoteDescription(answer))
        self.assertEqual(pc1.iceConnectionState, 'checking')

        # check outcome
        run(asyncio.sleep(1))
        self.assertEqual(pc1.iceConnectionState, 'completed')
        self.assertEqual(pc2.iceConnectionState, 'completed')

        # check state changes
        self.assertEqual(pc1_states['iceConnectionState'], ['new', 'checking', 'completed'])
        self.assertEqual(pc1_states['iceGatheringState'], ['new', 'gathering', 'complete'])
        self.assertEqual(pc2_states['iceConnectionState'], ['new', 'checking', 'completed'])
        self.assertEqual(pc2_states['iceGatheringState'], ['new', 'gathering', 'complete'])


logging.basicConfig(level=logging.DEBUG)