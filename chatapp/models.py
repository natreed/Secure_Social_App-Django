import time
from threading import Thread
from .SSNElement import SSNElement

from django.db import models
from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixRequestError
from requests.exceptions import MissingSchema
import django.dispatch
from apscheduler.schedulers.background import BackgroundScheduler


# TODO: Do I have to make this Global?
CLIENTS = []




class Message(models.Model):
    msg_text = models.CharField(max_length=600)
    time_stamp = models.IntegerField(default=0)
    sender = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Meta:
        get_latest_by = 'time_stamp'

    def __str__(self):
        return self.msg_text

    def get_data(self):
        return a_message(self.msg_text, self.sender, self.time_stamp)


class a_message():
    def __init__(self, _msg, _sender, _timestamp):
        self.message = _msg
        self.sender = _sender
        self.timestamp = _timestamp

    message = ""
    sender = ""
    timestamp = ""

def get_objects():
    msg_list = []
    for msg in Message.objects.order_by('time_stamp'):
        msg_list.append(a_message(msg.msg_text, msg.sender, msg.time_stamp))
    return msg_list


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

        self. current_room = self.mclient.join_room('#my_room:matrix.org')
        self.current_room.backfill_previous_messages()
        self.current_room.add_listener(self.on_message)
        self.get_new_messages()
        self.msg_saved = django.dispatch.Signal(providing_args=["message", "username"])
        # Syncs with home server every 30 seconds
        sched = BackgroundScheduler()
        sched.add_job(self.sync_loop, 'interval', seconds=30)
        sched.start()


    mclient = None
    current_room = None

    def sync_loop(self):
        self.mclient.listen_for_events()

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
                # msg_signal(msg.msg_text, msg.sender, msg.time_stamp)
                msg.save()
