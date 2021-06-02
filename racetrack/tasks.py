import pprint
import serial
import time

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task
from django.db import Error, IntegrityError
from django.db.models import Max

from racetrack.models import Race


def car_number(track_data, track_id):
    for track_def in track_data:
        if track_id == int(track_def.get('track_id')):
            return track_def.get('car_id')
    return ""


def car_name(race, track_data, track_id):
    for track_def in track_data:
        if track_id == int(track_def.get('track_id')):
            return race.car_set.get(number=track_def.get('car_id')).name
    return ""


def get_track_data(race, track_data_json):
    track_data = []
    for track in race.track_set.all():
        track_id = track.id
        car_id = int(track_data_json.get(str(track_id), {}).get('car_id', 0))
        if car_id:
            track_data.append({"track_id": track_id, "car_id": car_id})
    return track_data


@shared_task
def race_addRun(race_id, track_data_json):
    race = Race.objects.get(pk=race_id)
    results = {}
    new_run = None
    try:
        track_data = get_track_data(race, track_data_json)
        # print(track_data_json)
        # print(track_data)
        run_num = race.run_set.all().aggregate(Max('number')).get('number__max', 0) + 1
        new_run = race.run_set.create(number=run_num, tracks=track_data)
    except Error as e:
        print("error")
        print(e)
        results = {'error': e}
    finally:
        if not results:
            results = {"run_num": new_run.number}
        return {'msg': results}


@shared_task
def race_saveRun(race_id, run_results):
    race = Race.objects.get(pk=race_id)
    run = race.run_set.latest('id')
    try:
        track_data = run.tracks
        for track_def in track_data:
            track_id = track_def.get('track_id')
            car_num = track_def.get('car_id')
            track = race.track_set.get(pk=track_id)
            car = race.car_set.get(number=car_num)
            track_run = run_results.get(str(track_id), {})
            mph = track_run.get('mph', 0)
            fps = track_run.get('fps', 0)
            mps = track_run.get('mps', 0)
            run.trial_set.create(track=track, car=car, mph=mph, fps=fps, mps=mps)
    except IntegrityError as e:
        print("Integrity Error")
        print(e)
    except Error as e:
        print("Error")
        print(e)


@shared_task
def arduinoReadData(channel_name):
    print("Listening for USB COM Arduino data")
    channel_layer = None
    run_results_data = {}
    error_data = None
    try:
        arduino = serial.Serial('COM6', 9600)
        b_data = arduino.readline()
        data = bytes.decode(b_data)
        trackData = ""
        td_chunks = []

        if "Start" in data:
            loop = True
            while loop:
                b_data = arduino.readline()
                data = bytes.decode(b_data)
                if "Stop" in data:
                    loop = False
                else:
                    trackData += data
            td_chunks = trackData.split(',')
    except serial.SerialException as e:
        print("Serial Exception: Could not read port")
        print(e)
        error_data = e
    else:
        print("Arduino data received")
        channel_layer = get_channel_layer()
        try:
            race = Race.objects.get(pk=1)
            run = race.run_set.latest('id')
            track_data = run.tracks
            mph = 0
            fps = 5
            mps = 10
            for track in race.track_set.all():
                index = track.id
                run_results_data[str(index)] = {
                    "name": car_name(race, track_data, index),
                    "number": car_number(track_data, index),
                    "mph": td_chunks[mph + index],
                    "fps": td_chunks[fps + index],
                    "mps": td_chunks[mps + index],
                }

            # old_run_results_data = {
            #     "1": {
            #         "name": car_name(race, track_data, 1),
            #         "number": car_number(track_data, 1),
            #         "mph": td_chunks[mph + 1],
            #         "fps": td_chunks[fps + 1],
            #         "mps": td_chunks[mps + 1],
            #     },
            #     "2": {
            #         "name": car_name(race, track_data, 2),
            #         "number": car_number(track_data, 2),
            #         "mph": td_chunks[mph + 2],
            #         "fps": td_chunks[fps + 2],
            #         "mps": td_chunks[mps + 2],
            #     },
            #     "3": {
            #         "name": car_name(race, track_data, 3),
            #         "number": car_number(track_data, 3),
            #         "mph": td_chunks[mph + 3],
            #         "fps": td_chunks[fps + 3],
            #         "mps": td_chunks[mps + 3],
            #     },
            #     '4': {
            #         "name": car_name(race, track_data, 4),
            #         "number": car_number(track_data, 4),
            #         "mph": td_chunks[mph + 4],
            #         "fps": td_chunks[fps + 4],
            #         "mps": td_chunks[mps + 4],
            #     }
            # }
        except Error as e:  # Error Handling
            print("Results Manipulation error:")
            print(e)
            error_data = e
    finally:
        results = {}
        if error_data:
            results["type"] = "send_error"
            results["data"] = error_data
        else:
            results["type"] = "end_run"
            results["data"] = {'run_results': run_results_data}
        async_to_sync(channel_layer.send)(channel_name, results)


@shared_task
def test_arduinoReadData(channel_name):
    print("Listening for USB COM Arduino data")
    time.sleep(5)
    print("Data received")
    channel_layer = get_channel_layer()
    run_results_data = {}
    error_data = None
    try:
        race = Race.objects.get(pk=1)
        run = race.run_set.latest('id')
        track_data = run.tracks
        for track in race.track_set.all():
            index = track.id
            run_results_data[str(index)] = {
                "name": car_name(race, track_data, index),
                "number": car_number(track_data, index),
                "mph": 125.364,
                "fps": 3.344,
                "mps": 53.469,
            }
        # old_run_results_data = {
        #     "1": {
        #         "name": car_name(race, track_data, 1),
        #         "number": car_number(track_data, 1),
        #         "mph": 125.364,
        #         "fps": 3.344,
        #         "mps": 53.469,
        #     },
        #     "2": {
        #         "name": car_name(race, track_data, 2),
        #         "number": car_number(track_data, 2),
        #         "mph": 128.644,
        #         "fps": 97.344,
        #         "mps": 6.464,
        #     },
        #     "3": {
        #         "name": car_name(race, track_data, 3),
        #         "number": car_number(track_data, 3),
        #         "mph": 13.564,
        #         "fps": 94.321,
        #         "mps": 53.854,
        #     },
        #     '4': {
        #         "name": car_name(race, track_data, 4),
        #         "number": car_number(track_data, 4),
        #         "mph": 178.364,
        #         "fps": 7.697,
        #         "mps": 11.254,
        #     }
        # }
    except Error as e:  # Error Handling
        print("readArduinoError:")
        print(e)
        error_data = e
    finally:
        results = {}
        if error_data:
            results["type"] = "send_error"
            results["data"] = error_data
        else:
            results["type"] = "end_run"
            results["data"] = {'run_results': run_results_data}
        async_to_sync(channel_layer.send)(channel_name, results)
