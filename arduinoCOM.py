import re
import time
import datetime

import serial


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


print("Connecting to COM Port")
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
        arduino.timeout = 300
        b_data = arduino.readline()
        data = bytes.decode(b_data)
        if "START DATA" in data:
            print("Received data")
            loop = True
            while loop:
                b_data = arduino.readline()
                data = bytes.decode(b_data)
                if "END DATA" in data:
                    loop = False
                else:
                    arduinoData += data
            ad_chunks = re.split(r'[\n\r]+', arduinoData)
            while '' in ad_chunks:
                ad_chunks.remove('')
            bitmasks = [
                [b'0x01', b'0x02'],
                [b'0x04', b'0x08'],
                [b'0x10', b'0x20'],
                [b'0x40', b'0x80']
            ]
            index = 1
            inches = 24
            feet = inches / 12
            miles = feet / 5280
            meters = inches / 39.37007874015748
            nascar = 24.444444444444444444
            dec = 3
            for bm_list in bitmasks:
                print(f'TRACK {index}')
                time = checkTrackBits(ad_chunks, bm_list)

                if time:
                    hours = time / 3600
                    print("TIME:", time, "s")
                    print(f"MPS: {(meters / time):.{dec}f}")
                    print(f"MPH: {(miles / hours):.{dec}f}")
                    print(f"MPH (NASCAR): {(miles / hours * nascar):.{dec}f}")
                    print(f"FPS: {(feet / time):.{dec}f}")
                else:
                    print("1 or more pins did not change")
                print("-----")
                index += 1
    else:
        print("No data")
except serial.SerialTimeoutException as e:
    print("Serial Write Timeout")
    print(e)
    error_data = e
except serial.SerialException as e:
    print("Serial Exception: Could not read port")
    print(e)
    error_data = e
else:
    print("Arduino data received")
    print(arduinoData)
