import json
import pprint

from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import Error
from racetrack.tasks import race_addRun, race_saveRun, arduinoReadData, test_arduinoReadData


class RaceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.race_id = self.scope['url_route']['kwargs']['race_id']
        self.race_group_name = f'race_{self.race_id}'

        await self.channel_layer.group_add(
            self.race_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.race_group_name,
            self.channel_name
        )

    # Receive message from WebSocket -> detail page, add_run data
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        data = text_data_json['data']
        method_type = text_data_json['type']
        print("Websockets Received Msg:", method_type, self.channel_name)
        print(text_data_json)
        if method_type == "start_run":
            await self.start_run(data)
        else:
            return

    async def start_run(self, track_data):
        print("Starting run", self.channel_name)
        msg_data = None
        new_run = None
        try:
            new_run = race_addRun.delay(self.race_id, track_data)
            test_arduinoReadData.delay(self.channel_name)
            # arduinoReadData.delay(self.channel_name)
        except Error as e:
            msg_data = e
        finally:
            if not msg_data:
                msg_data = new_run.get()['msg']
                if msg_data.get('error', False):
                    msg_type = 'send_error'
                    msg_data = msg_data['error']
                else:
                    msg_type = 'send_msg'
            else:
                msg_type = 'send_error'
            results = {
                'type': msg_type,
                'data': msg_data
            }
            await self.channel_layer.group_send(self.race_group_name, results)

    async def end_run(self, event):
        print("Saving run", self.channel_name)
        run_data = event['data']
        error_data = None
        try:
            race_saveRun.delay(self.race_id, run_data)
        except Error as e:
            error_data = e
        finally:
            await self.channel_layer.group_send(self.race_group_name, {
                'type': 'send_msg',
                'data': run_data
            })
            if error_data:
                await self.channel_layer.group_send(self.race_group_name, {
                    'type': 'send_error',
                    'data': error_data
                })

    async def send_msg(self, event):
        msg = event['data']
        # print("Sending msg to", self.channel_name)
        # print(msg)
        await self.send(text_data=json.dumps(msg))

    async def send_error(self, event):
        error = event['data']
        print("Sending error to", self.channel_name)
        print(error)
        await self.send(text_data=json.dumps({
            'error': error
        }))

