import pprint
import serial
import time

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task
from django.db import Error
from django.db.models import Max
from racetrack.models import Race
from racetrack.tasks import car_name, car_number


def run_results():
    race = Race.objects.get(pk=1)
    run = race.run_set.latest('id')
    run_results_data = {}
    try:
        track_data = run.tracks
        run_results_data = {
            "1": {
                "name": car_name(race, track_data, 1),
                "number": car_number(track_data, 1),
                "mph": 125.364,
                "fps": 3.344,
                "mps": 53.469,
            },
            "2": {
                "name": car_name(race, track_data, 2),
                "number": car_number(track_data, 2),
                "mph": 128.644,
                "fps": 97.344,
                "mps": 6.464,
            },
            "3": {
                "name": car_name(race, track_data, 3),
                "number": car_number(track_data, 3),
                "mph": 13.564,
                "fps": 94.321,
                "mps": 53.854,
            },
            '4': {
                "name": car_name(race, track_data, 4),
                "number": car_number(track_data, 4),
                "mph": 178.364,
                "fps": 7.697,
                "mps": 11.254,
            }
        }
    finally:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "race_1",
            {
                'type': 'send_msg',
                'data': {
                    'run_results': run_results_data
                }
            }
        )
