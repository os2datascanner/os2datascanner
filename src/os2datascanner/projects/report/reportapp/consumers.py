import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class ReportWebsocketConsumer(WebsocketConsumer):
    def connect(self):
        self.channel = 'get_updates'
        async_to_sync(self.channel_layer.group_add)(
            self.channel,
            self.channel_name
        )
        self.accept()

    def websocket_disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.channel,
            self.channel_name
        )
        self.disconnect()

    def websocket_receive(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
