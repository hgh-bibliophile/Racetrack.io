import pprint
import re
import datetime

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
        print(track_def)
        print(track_id)
        print(track_def.get('track_id'))
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
    print(track_data)
    for track in race.track_set.all():
        track_id = track.id
        track_number = track.number
        car_id = int(track_data_json.get(str(track_number), {}).get('car_id', 0))
        if car_id:
            track_data.append({"track_id": track_id, "track_number": track_number, "car_id": car_id})
    return track_data


def get_leaderboard_data(race):
    results = {}
    trials = race.trial_set.all().order_by('-mph')
    num_trials = len(trials)
    offset = 0
    ids = []
    for d in range(10):
        i = d + offset
        print(i)
        if i < num_trials:
            trial = trials[i]
            print(ids)
            print(trial.car.id)
            end = False
            while trial.car.id in ids:
                offset += 1
                if (d + offset) < num_trials:
                    trial = trials[d + offset]
                    end = False
                else:
                    end = True
                    break
            if not end:
                ids.append(trial.car.id)
                print(d+1)
                results[str(d + 1)] = {
                    'car_num': trial.car.number,
                    'car': trial.car.name,
                    'track': trial.track.number,
                    'speed': round(trial.mph, 2),
                }
            else:
                results[str(d + 1)] = {
                    'car_num': None,
                    'car': None,
                    'track': None,
                    'speed': None,
                }
        else:
            results[str(d + 1)] = {
                'car_num': None,
                'car': None,
                'track': None,
                'speed': None,
            }
    print(results)
    return results


def checkTrackBits(bit_data, masks):
    times = []
    timeDiff = None
    i = 0
    for change in bit_data:
        [bit, micro_time] = change.split(',')
        # print(bit)
        # print("i < 2:", i < 2)
        # print("masks[i]:", int(masks[i], 16))
        # print("int(bit):", int(bit, 2))
        # print("(masks[i] & int(bit)):", (int(masks[i], 16) & int(bit, 2)))
        if i < 2 and (int(masks[i], 16) & int(bit, 2)) > 0:
            times.append(int(micro_time))
            print(f'Change {i + 1} at {micro_time}')
            i += 1
        if len(times) == 2:
            t1 = times[0]
            t2 = times[1]
            tDiff = t2 - t1
            timeDiff = datetime.timedelta(microseconds=tDiff).total_seconds()
            break
    return timeDiff


@shared_task
def race_addRun(race_id, track_data_json):
    race = Race.objects.get(pk=race_id)
    results = {}
    new_run = None
    try:
        track_data = get_track_data(race, track_data_json)
        # print(track_data_json)
        # print(track_data)
        if race.run_set.all():
            run_num = race.run_set.all().aggregate(Max('number')).get('number__max', 0) + 1
        else:
            run_num = 1
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
    leaderboard = {}
    results = None
    try:
        track_data = run.tracks
        for track_def in track_data:
            track_id = track_def.get('track_id')
            car_num = track_def.get('car_id')
            track = race.track_set.get(pk=track_id)
            track_num = track.number
            car = race.car_set.get(number=car_num)
            track_run = run_results.get(str(track_num), {})
            print(track_run)
            mph = track_run.get('mph', 0)
            fps = track_run.get('fps', 0)
            mps = track_run.get('mps', 0)
            run.trial_set.create(race=race, track=track, car=car, mph=mph, fps=fps, mps=mps)
        leaderboard = get_leaderboard_data(race)
    except IntegrityError as e:
        print("Integrity Error")
        print(e)
        results = {'error': e}
    except Error as e:
        print("error")
        print(e)
        results = {'error': e}
    finally:
        if not results:
            results = {'run_results': run_results, "leaderboard": leaderboard}
        return {'msg': results}


@shared_task
def arduinoReadData(channel_name, race_id):
    print("Connecting to COM Port")
    channel_layer = None
    error_data = None
    run_results_data = {}
    arduinoData = ""
    ad_chunks = []
    try:
        arduino = serial.Serial('COM6', 9600, timeout=5)
        time.sleep(1.5)
        arduino.write(bytes('START RACE' + '\n', 'ascii'))
        b_data = arduino.readline()
        data = bytes.decode(b_data)
        if "ACK" in data:
            print("Listening for USB COM Arduino data")
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(channel_name, {'type': 'send_msg', 'data': {'arduino_ready': True}})
            arduino.timeout = 300
            data = bytes.decode(arduino.readline())
            if "START DATA" in data:
                print("Received data")
                loop = True
                while loop:
                    data = bytes.decode(arduino.readline())
                    if "END DATA" in data:
                        loop = False
                    else:
                        arduinoData += data
                ad_chunks = re.split(r'[\n\r]+', arduinoData)
                arduino.close()
        else:
            print("Did not receive response from Arduino")
            error_data = "Did not receive response from Arduino"
    except serial.SerialTimeoutException as e:
        print("Serial Write Timeout")
        print(e)
        error_data = e
    except serial.SerialException as e:
        print("Serial Exception")
        print(e)
        error_data = e
    else:
        race = Race.objects.get(pk=race_id)
        run = race.run_set.latest('id')
        track_data = run.tracks
        print(track_data)
        if ad_chunks:
            print("Arduino data received")
            channel_layer = get_channel_layer()
            try:
                bitmasks = [
                    [b'0x01', b'0x02'],
                    [b'0x04', b'0x08'],
                    [b'0x10', b'0x20'],
                    [b'0x40', b'0x80']
                ]
                dec = 2
                nascar = 24.444444444444444444
                while '' in ad_chunks:
                    ad_chunks.remove('')
                for track in race.track_set.all():
                    track_number = track.number
                    track_id = track.id
                    print(track_number)
                    print(track_id)
                    bm_list = bitmasks[track_number - 1]
                    sec = checkTrackBits(ad_chunks, bm_list)
                    inches = track.distance
                    feet = inches / 12
                    miles = feet / 5280
                    meters = inches / 39.37007874015748
                    if sec:
                        print("In sec")
                        hours = sec / 3600
                        mps = float(f"{(meters / sec):.{dec}f}")
                        mph = float(f"{(miles / hours * nascar):.{dec}f}")
                        fps = float(f"{(feet / sec):.{dec}f}")
                        print(sec, mph, fps, mps)
                        print(car_number(track_data, track_id))
                        if car_number(track_data, track_id):
                            print("Trying to assign to results")
                            run_results_data[str(track_number)] = {
                                "name": car_name(race, track_data,  track_id),
                                "number": car_number(track_data,  track_id),
                                "mph": mph,
                                "fps": fps,
                                "mps": mps,
                            }
                    else:
                        if car_number(track_data,  track_id):
                            run_results_data[str(track_number)] = {
                                "name": car_name(race, track_data,  track_id),
                                "number": car_number(track_data,  track_id),
                                "mph": 0,
                                "fps": 0,
                                "mps": 0,
                            }
                    print(run_results_data)
            except Error as e:
                print("Error while working with results:")
                print(e)
                error_data = e
        else:
            for track in race.track_set.all():
                track_number = track.number
                track_id = track.id
                if car_number(track_data,  track_id):
                    run_results_data[str(track_number)] = {
                        "name": car_name(race, track_data,  track_id),
                        "number": car_number(track_data,  track_id),
                        "mph": 0,
                        "fps": 0,
                        "mps": 0,
                    }
    finally:
        results = {}
        if error_data:
            results["type"] = "send_error"
            results["data"] = error_data
        else:
            results["type"] = "end_run"
            results["data"] = {'run_results': run_results_data}
        print(results)
        async_to_sync(channel_layer.send)(channel_name, results)


# def old2_arduinoReadData(channel_name):
#     print("Listening for USB COM Arduino data")
#     channel_layer = None
#     error_data = None
#     run_results_data = {}
#     ad_chunks = []
#     try:
#         arduino = serial.Serial('COM6', 9600, timeout=5)
#         arduino.write(bytes('START RACE\r\n'))
#         b_data = arduino.readline()
#         data = bytes.decode(b_data)
#         if "ACK" in data:
#             arduinoData = ""
#             arduino.timeout = 300
#             b_data = arduino.readline()
#             data = bytes.decode(b_data)
#             if "START DATA" in data:
#                 loop = True
#                 while loop:
#                     b_data = arduino.readline()
#                     data = bytes.decode(b_data)
#                     if "END DATA" in data:
#                         loop = False
#                     else:
#                         arduinoData += data
#                 ad_chunks = arduinoData.split(',')
#     except serial.SerialTimeoutException as e:
#         print("Serial Timeout")
#         print(e)
#         error_data = e
#     except serial.SerialException as e:
#         print("Serial Exception: Could not read port")
#         print(e)
#         error_data = e
#     else:
#         print("Arduino data received")
#         channel_layer = get_channel_layer()
#         try:
#             race = Race.objects.get(pk=1)
#             run = race.run_set.latest('id')
#             track_data = run.tracks
#             mph = 0
#             fps = 5
#             mps = 10
#             for track in race.track_set.all():
#                 index = track.id
#                 run_results_data[str(index)] = {
#                     "name": car_name(race, track_data, index),
#                     "number": car_number(track_data, index),
#                     "mph": ad_chunks[mph + index],
#                     "fps": ad_chunks[fps + index],
#                     "mps": ad_chunks[mps + index],
#                 }
#         except Error as e:  # Error Handling
#             print("Results Manipulation error:")
#             print(e)
#             error_data = e
#     finally:
#         results = {}
#         if error_data:
#             results["type"] = "send_error"
#             results["data"] = error_data
#         else:
#             results["type"] = "end_run"
#             results["data"] = {'run_results': run_results_data}
#         async_to_sync(channel_layer.send)(channel_name, results)
#
#
# def old_arduinoReadData(channel_name):
#     print("Listening for USB COM Arduino data")
#     channel_layer = None
#     run_results_data = {}
#     error_data = None
#     try:
#         arduino = serial.Serial('COM6', 9600)
#         b_data = arduino.readline()
#         data = bytes.decode(b_data)
#         trackData = ""
#         td_chunks = []
#         if "Start" in data:
#             loop = True
#             while loop:
#                 b_data = arduino.readline()
#                 data = bytes.decode(b_data)
#                 if "Stop" in data:
#                     loop = False
#                 else:
#                     trackData += data
#             td_chunks = trackData.split(',')
#     except serial.SerialException as e:
#         print("Serial Exception: Could not read port")
#         print(e)
#         error_data = e
#     else:
#         print("Arduino data received")
#         channel_layer = get_channel_layer()
#         try:
#             race = Race.objects.get(pk=1)
#             run = race.run_set.latest('id')
#             track_data = run.tracks
#             mph = 0
#             fps = 5
#             mps = 10
#             for track in race.track_set.all():
#                 index = track.id
#                 run_results_data[str(index)] = {
#                     "name": car_name(race, track_data, index),
#                     "number": car_number(track_data, index),
#                     "mph": td_chunks[mph + index],
#                     "fps": td_chunks[fps + index],
#                     "mps": td_chunks[mps + index],
#                 }
#         except Error as e:  # Error Handling
#             print("Results Manipulation error:")
#             print(e)
#             error_data = e
#     finally:
#         results = {}
#         if error_data:
#             results["type"] = "send_error"
#             results["data"] = error_data
#         else:
#             results["type"] = "end_run"
#             results["data"] = {'run_results': run_results_data}
#         async_to_sync(channel_layer.send)(channel_name, results)


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
                "mph": 400.000,
                "fps": 3.344,
                "mps": 53.469,
            }
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
