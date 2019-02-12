from django.db import models
from django.db.models import Max
from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixRequestError
from requests.exceptions import MissingSchema
import sys

# TODO: Do I have to make this Global?
CLIENTS = []


class Message(models.Model):
    msg_text = models.CharField(max_length=600)
    time_stamp = models.IntegerField(default=0)
    sender = models.CharField(max_length=100)

    class Meta:
        get_latest_by = 'time_stamp'

    def __str__(self):
        return self.msg_text

    def get_data(self):
        return {'msg_text': self.msg_text,
                'sender': self.sender}

# TODO: I know this file is meant for dbmodels
class Client:
    def __init__(self, server_url, username, password):
        try:
            self.mclient = MatrixClient('https://' + server_url)
            self.mclient.login("@" + username + ":matrix.org", password, limit=100, sync=True)
        except MatrixRequestError as e:
            print(e)
            raise e

        except MissingSchema as e:
            print(e)
            raise e

        except Exception as e:
            raise e

        self.current_room = self.mclient.join_room('#my_room:matrix.org')
        self.current_room.backfill_previous_messages()
        self.current_room.add_listener(self.on_message)
        self.get_new_messages()

    mclient = None
    current_room = None

    def send_messages_test(self):
        self.current_room.send_text('a test for an update')
        return 'a test for an update'

    def get_room_names(self):
        room_names = []
        for room in self.mclient.rooms:
            room_names.append(room)

    def get_new_messages(self):
        """
        Looks for new messages in current_room events and adds them to db model.
        :return:
        """
        events = self.current_room.get_events()
        most_recent_ts = Message.objects.latest('time_stamp').time_stamp

        # make sure message is later than the last most recent message
        new_msgs = filter(lambda e: e['type'] == 'm.room.message' and
                                    e['origin_server_ts'] > most_recent_ts, events)
        for event in new_msgs:
            msg = Message(msg_text=event['content']['body'],
                          time_stamp=event['origin_server_ts'],
                          sender=event['sender'])
            msg.save()

    def on_message(self, room, event):
        """
        Listens and updates Message Model on message events.
        :param room:
        :param event:
        :return:
        """
        if event['type'] == 'm.room.message':
            if event['content']['msgtype'] == 'm.text':
                msg = Message(msg_text=event['content']['body'],
                              time_stamp=event['origin_server_ts'],
                              sender=event['sender'])
                msg.save()


    # TODO: this global client seems like a bad idea. maybe
    # I could turn this into a base class that all client contexts could share
    def set_client(self, client):
        CLIENT = client
