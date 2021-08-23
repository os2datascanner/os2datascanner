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
        print("#######  CONNECTED  #######")


    def websocket_disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.channel,
            self.channel_name
        )
        self.disconnect()
        print("DISCONNECED CODE: ",code)


    def websocket_receive(self, event):
        print("MESSAGE RECEIVED - SENDING TO FRONTEND")
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))