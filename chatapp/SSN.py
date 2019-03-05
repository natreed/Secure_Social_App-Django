from apscheduler.schedulers.background import BackgroundScheduler
from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixRequestError
from requests.exceptions import MissingSchema
from .models import Room, Message
from django.db.models import Q
from django.db import IntegrityError


from chatapp.SSNChat import SSNChat
from chatapp.SSNWall import SSNWall


class SSN:
    def __init__(self, server_url, username, password):
        try:
            self.server_url = server_url
            self.username = username
            self.m_client = MatrixClient('https://' + server_url)
            matrix_id = "@" + username + ":" + server_url
            self.m_client.login(matrix_id, password, limit=100, sync=True)
        except MatrixRequestError as e:
            print(e)
            raise e

        except MissingSchema as e:
            print(e)
            raise e

        except Exception as e:
            raise e

        # Todo: hard coded landing room and wall for now
        self.chat_landing_room = '#' + self.username + '_chat' + ':' + self.server_url
        self.wall_landing_room = '#' + self.username + '_wall' + ':' + self.server_url
        # create wall and\or chat rooms if they don't already exist

        self.load_rooms()

        self.chat_client = self.start_ssn_client()
        # self.wall_client = self.start_wall_client()
        """Current interface is the context/interface of the current 'ssn_element'.
        The chat client is the base context. To access any other context element
        The user will first have to return to the base context. This is to keep context
        switching programmatically simple. Once the complexity increases with more element_types
        a stack will be used to keep an ordering. So that when the user leaves one context
        the previous context will be loaded."""
        self.current_interface = self.chat_client

        # Syncs with home server every 30 seconds
        sched = BackgroundScheduler()
        sched.add_job(self.sync_loop, 'interval', seconds=1)
        #sched.start()



    def get_user_id(self):
        return self.username

    def load_rooms(self):
        for room in self.m_client.rooms.values():
            room_name = room.display_name.split(':')[0].lstrip('#')
            room.set_room_name(room_name)
            rm = Room(
                room_name=room_name,
                room_id=room.room_id,
                joined=False
            )
            try:
                rm.save()
            except IntegrityError:
                pass


    def get_messages(self):
        """
        get list of messages for current room from db
        :return:
        """
        msg_list = []

        room_name = self.current_interface.current_room.name

        for msg in Room.objects.get(room_name=room_name).message_set.order_by('time_stamp'):
            msg_list.append(msg.get_data())

        return msg_list

    def get_rooms(self):
        rooms = []
        db_rooms = list(Room.objects.all().filter(~Q(room_name__contains='Empty')))

        for room in db_rooms:
            rooms.append(room.room_name)

        return rooms

    def change_rooms(self, room_name, room_type='chat'):
        if room_type == 'chat':
            room_id = '#' + room_name + ":" + self.server_url
            new_room = self.current_interface.join_room(room_id)
            self.current_interface.current_room = new_room
        else: # Wall or friend wall TODO: change when wall feature is added
            pass

    def sync_loop(self):
        self.m_client.join_room(self.current_interface.current_room.room_id)

    def start_ssn_client(self):
        """this function is just for the sake of being explicit"""
        return SSNChat(self.m_client, self.chat_landing_room)


    # def start_wall_client(self):
    #     return SSNWall(self.m_client, self.chat_landing_room)