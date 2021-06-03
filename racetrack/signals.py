from django.db.models.signals import post_save
from django.dispatch import receiver

import core.settings
from racetrack.models import Run, Trial
import serial
import time
import pprint

#print(core.settings.REDIS_URL)
from racetrack.tasks import test_arduinoGetSpeeds


# @receiver(post_save, sender=Run, dispatch_uid="racetrack.signals.startRun")
# def startRun(sender, instance, **kwargs):
#     print("Ran startRun")
#     if not instance.signal_meta:
#         instance.signal_meta = True
#         race_id = instance.race_id
#         tracks_def = instance.tracks
#         print("Listening via USB COM Serial for Arduino data")
#         test_arduinoGetSpeeds.delay()
#         #print(add.delay(5,5))
#         pprint.pprint(tracks_def)
#
#
# @receiver(post_save, sender=Trial, dispatch_uid="racetrack.signals.updateLeaderboard")
# def updateLeaderboard(sender, instance, **kwargs):
#     if not instance.signal_meta:
#         instance.signal_meta = True
#         print("Listening via USB COM Serial for Arduino data")
#         pprint.pprint(instance.tracks)
