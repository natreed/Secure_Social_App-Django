from django.db import models
from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixRequestError
from requests.exceptions import MissingSchema
import sys


"""TODO: I know this is meant for dbmodels."""
class Client:
    def __init__(self):

        self.mclient = MatrixClient('https://www.matrix.org')

        try:
            self.mclient.login("@natreed:matrix.org", "vatloc4evr", limit=100, sync=True)
        except MatrixRequestError as e:
            print(e)
            if e.code == 403:
                print("Bad username or password.")
                sys.exit(4)
            else:
                print("Check your sever details are correct.")
                sys.exit(2)
        except MissingSchema as e:
            print("Bad URL format.")
            print(e)
            sys.exit(3)

        self.current_room = self.mclient.join_room('#my_room:matrix.org')
        self.current_room.backfill_previous_messages()
        self.current_room.add_listener(self.on_message)

    mclient = None
    current_room = None

    def send_messages_test(self):
        self.current_room.send_text('a test for an update')
        return 'a test for an update'


    def get_room_names(self):
        room_names = []
        for room in self.mclient.rooms:
            room_names.append(room)

    def get_message_list(self):
        msgs = []
        for event in self.current_room.events:
            if event['type'] == "m.room.message":
                msgs.append(event['content']['body'])
        return msgs


    def on_message(self, room, event):
        NotImplemented









