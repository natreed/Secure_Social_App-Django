import datetime
import sys
from collections import defaultdict
import django.dispatch
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from matrix_client.api import MatrixRequestError
from matrix_client.client import MatrixClient
from requests.exceptions import MissingSchema
from .models import Message, Room


class SSNElement:
    def __init__(self, client, landing_room):

        self.m_client = client
        """Additional state for SSN"""
        self.current_room = None
        self.landing_room = landing_room
        self.friends = {}
        self.user_id = self.m_client.user_id
        # the room table matches the room name to the to the room id
        self.room_table = {}
        self.is_room_setup = False
        # default dict allows appending to lists directly
        # a store for all the messages {room:[list of messages], ...}
        # updates occur in send_room message
        self.all_rooms_messages = defaultdict(list)
        # reference room objects by room_id
        self.loaded_rooms = {}
        # lookup table of room names to room_id's
        self.update_room_table()
        self.rendered = False
        self.type = None

    def get_new_messages(self, db_room):
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
            local_tz = pytz.timezone("US/Pacific")
            utc_dt = datetime.fromtimestamp(event['origin_server_ts'] / 1000.0, local_tz)
            msg = Message(msg_text=event['content']['body'],
                          time_stamp=event['origin_server_ts'],
                          sender=event['sender'],
                          room=db_room,
                          date_time=utc_dt)
            msg.save()

    def db_add_room(self, matrix_room):
        r = Room(room_name=matrix_room.display_name, room_id=matrix_room.room_id)
        r.save()
        self.get_new_messages(r)

    @classmethod
    def on_message(cls, room, event):
        raise NotImplementedError

    @classmethod
    def load(cls, **kwargs):
        raise NotImplementedError

    def init_msg_hist_for_room(self, room_name, msg_store):
        self.all_rooms_messages[room_name] = []
        for msg in msg_store:
            """TODO: making timestamp key should avoid duplicates"""
            """Don't want to print message if it is just updating wall state."""
            self.all_rooms_messages[room_name].append(msg)

    def send_room_message(self, room, event, prepend=None):
        """
        :param room:
        :param event:
        :param prepend:
        :return:

        TODO: Make add time stamp to messages. Turn all rooms messages into dict instead of list. "time:msg
        """
        if event['content']['msgtype'] == "m.text":
            msg = self.format_event_message(event)
            if prepend:
                msg = prepend + msg

            if self.is_room_setup \
                    and room.name == self.current_room.room.name\
                    and self.user_id == event['sender']:
                print(msg)

            if room.name == 'Empty Room':
                room_name = self.parse_room_name_or_id(room.room_id)
            else:
                room_name = room.name

            self.all_rooms_messages[room_name].append(msg)

    def show_rooms(self):
        for room in self.m_client.rooms.values():
            print(room.name)

    def add_friend(self, user_id):
        if user_id not in self.friends.keys():
            self.friends[user_id] = ''
            print("added friend")
        else:
            print(format("{0} is already on the list.", user_id))

    def get_current_room(self):
        return self.current_room

    def update_room_table(self):
        for id, room in self.m_client.rooms.items():
            rm = Room(room_id=id, joined=False, room_name=room.display_name)
            self.room_table[room.name] = {"room_id": id, "joined": False}


    def parse_room_name_or_id(self, allias_user_id_or_room_id):
        return allias_user_id_or_room_id.split(':')[0].lstrip('#')

    def format_event_message(self, event):
        return "{0}: {1}".format(event['sender'], event['content']['body'])

    def get_room_id(self, room_name):
        return self.room_table[room_name]["room_id"]

    def join_room(self, room_id_alias=None, print_room=True, event_limit=10):
        """
        :param room_id_alias:
        :return matrix room object:
        """
        try:
            self.is_room_setup = False
            room_name = self.parse_room_name_or_id(room_id_alias)
            room = self.m_client.join_room(room_id_alias)
            # this sets the user profile for the client that is specific to the room
            room.set_user_profile(displayname=self.parse_room_name_or_id(self.m_client.user_id))
            room.name = room_name
            room.backfill_previous_messages(limit=event_limit)
            print("CURRENT ROOM: {}".format(self.parse_room_name_or_id(room_id_alias)))
            if print_room:
                for msg in self.all_rooms_messages[room.name]:
                    print(msg)

            self.is_room_setup = True

            room.add_listener(self.on_message)

        except MatrixRequestError as e:
            print(e)
            if e.code == 400:
                print("Room ID/Alias in the wrong format")
                sys.exit(11)
            else:
                print("Couldn't find room.")
                sys.exit(12)
        return room

