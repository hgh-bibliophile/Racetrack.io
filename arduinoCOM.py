from serial import Serial
import pprint


arduino = Serial('COM6', 9600)
run = True
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

mph = 0
fps = 5
mps = 10
trackRunDict = {
    1: {
        "mph": td_chunks[mph + 1],
        "fps": td_chunks[fps + 1],
        "mps": td_chunks[mps + 1],
    },
    2: {
        "mph": td_chunks[mph + 2],
        "fps": td_chunks[fps + 2],
        "mps": td_chunks[mps + 2],
    },
    3: {
        "mph": td_chunks[mph + 3],
        "fps": td_chunks[fps + 3],
        "mps": td_chunks[mps + 3],
    },
    4: {
        "mph": td_chunks[mph + 4],
        "fps": td_chunks[fps + 4],
        "mps": td_chunks[mps + 4],
    }
}
pprint.pprint(trackRunDict)