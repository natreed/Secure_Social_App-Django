from apscheduler.schedulers.background import BackgroundScheduler
from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixRequestError
from requests.exceptions import MissingSchema
from .models import Room, Message, Post
from django.db.models import Q
from django.db import IntegrityError
from background_task import background
from datetime import datetime
from datetime import timedelta




from chatapp.SSNChat import SSNChat
from chatapp.SSNWall import SSNWall

# interval for syncing
INTERVAL = 5


class SSN:
    def __init__(self, server_url, username, password):
        try:
            self.server_url = server_url
            self.username = username
            self.m_client = MatrixClient('https://' + server_url)
            matrix_id = "@" + username + ":" + server_url
            self.m_client.login(matrix_id, password, limit=100, sync=True)
            self.rooms = []
        except MatrixRequestError as e:
            print(e)
            raise e

        except MissingSchema as e:
            print(e)
            raise e

        except Exception as e:
            raise e

        # Todo: hard coded landing room and wall for now
        self.chat_landing_room = '#' + self.username + 's_chat' + ':' + self.server_url
        self.wall_landing_room = '#' + self.username + 's_wall' + ':' + self.server_url
        # create wall and\or chat rooms if they don't already exist

        self.load_rooms()

        self.chat_client = self.start_ssn_client()
        self.wall_client = self.start_wall_client()
        self.friend_wall = None
        """Current interface is the context/interface of the current 'ssn_element'.
        The chat client is the base context. To access any other context element
        The user will first have to return to the base context. This is to keep context
        switching programmatically simple. Once the complexity increases with more element_types
        a stack will be used to keep an ordering. So that when the user leaves one context
        the previous context will be loaded."""
        self.current_interface = self.chat_client


    #     # Syncs with home server every 5 seconds
    #     self.sync_with_matrix(repeat=INTERVAL, repeat_until=datetime.now() + timedelta(days=1))
    #
    # #TODO: This still doesn't work
    # @background(schedule=INTERVAL)
    # def sync_with_matrix(self):
    #     self.m_client._sync()
    #     return

    def get_user_id(self):
        return self.username

    def load_rooms(self):
        self.clean_db_rooms()
        for room in self.m_client.rooms.values():
            is_post = False
            room_client_user_id = room.client.user_id
            room_owner = room_client_user_id.split(':')[0].lstrip('@')
            room_name = room.display_name.split(':')[0].lstrip('#')
            if 'post' in room_name:
                is_post = True

            room.set_room_name(room_name)
            self.rooms.append(room_name)

            rm = Room(
                owner=room_owner,
                room_name=room_name,
                room_id=room.room_id,
                is_post_room=is_post,
                joined=False
            )
            try:
                rm.save()
            except IntegrityError as e:
                pass


    def clean_db_rooms(self):
        """look for rooms that in the database that don't exist and remove them"""
        mClient_room_ids = []
        db_room_ids = []
        db_rooms = list(Room.objects.only('room_id'))
        for room in db_rooms:
            if room not in self.m_client.rooms.values():
                db_room_ids.append({'id':room.room_id, 'owner': room.owner})

        for room in db_room_ids:
            if room['id'] not in mClient_room_ids and room['owner'] is self.username:
                Room.objects.filter(room_id__contains=id).delete()

    def get_current_room_messages(self):
        """
        get list of messages for current room from db
        :return:
        """
        msg_list = []

        room_id = self.current_interface.current_room.room_id
        msgs = Room.objects.get(room_id=room_id).message_set.order_by('time_stamp')
        for msg in msgs:
            msg_list.append(msg.get_data())

        return msg_list

    def get_chat_rooms(self):
        rooms = []
        db_rooms = list(Room.objects.all().filter(~Q(room_name__contains='Empty'),
                                                  ~Q(room_name__contains='post'),
                                                  )
                        )

        for room in db_rooms:
            if room.room_name in self.rooms:
                rooms.append(room.room_name)

        return rooms

    def change_rooms(self, room_name):
        if room_name.startswith('!') or room_name.startswith('#'):
            room_id = room_name
        else:
            room_id = '#' + room_name + ":" + self.server_url
        try:
            new_room = self.current_interface.join_room(room_id)
            new_room.add_listener(self.current_interface.on_message)
        except MatrixRequestError:
            print("Joining room Unsuccessful")
            return
        self.current_interface.current_room = new_room


    def sync_loop(self):
        self.m_client.join_room(self.current_interface.current_room.room_id)

    def start_ssn_client(self):
        """this function is just for the sake of being explicit"""
        return SSNChat(self.m_client, self.chat_landing_room)

    def start_wall_client(self):
        return SSNWall(self.m_client, self.wall_landing_room)