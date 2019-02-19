from apscheduler.schedulers.background import BackgroundScheduler
from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixRequestError
from requests.exceptions import MissingSchema
from .models import Room, a_message


from chatapp.SSNChat import SSNChat


class SSN:
    def __init__(self, server_url, username, password):
        try:
            self.m_client = MatrixClient('https://' + server_url)
            self.m_client.login("@" + username + ":matrix.org", password, limit=100, sync=True)
        except MatrixRequestError as e:
            print(e)
            raise e

        except MissingSchema as e:
            print(e)
            raise e

        except Exception as e:
            raise e

        # Todo: hard coded my_room
        self.chat_landing_room = '#my_room:matrix.org'
        self.user_id = username.split(':')[0][1:]
        self.wall_landing_room = '#natreed_w:matrix.org'
        for room in self.m_client.rooms.values():
            room_name = room.display_name.split(':')[0].lstrip('#')
            room.set_room_name(room_name)

        self.chat_client = self.start_ssn_client()
        """Current interface is the context/interface of the current 'ssn_element'.
        The chat client is the base context. To access any other context element
        The user will first have to return to the base context. This is to keep context
        switching programmatically simple. Once the complexity increases with more element_types
        a stack will be used to keep an ordering. So that when the user leaves one context
        the previous context will be loaded."""
        self.current_interface = self.chat_client

        # Syncs with home server every 30 seconds
        sched = BackgroundScheduler()
        sched.add_job(self.sync_loop, 'interval', seconds=30)
        sched.start()

    def get_user_id(self):
        return self.user_id

    def get_messages(self):
        """
        get list of messages for current room from db
        :return:
        """
        msg_list = []
        room_name = self.current_interface.current_room.name
        db_rooms = list(Room.objects.all())

        for msg in Room.objects.get(room_name=room_name).message_set.order_by('time_stamp'):
            msg_list.append(a_message(msg.room, msg.msg_text, msg.sender, msg.background_color, msg.date_time))
        return msg_list

    def sync_loop(self):
        self.m_client.listen_for_events()

    def start_ssn_client(self):
        """this function is just for the sake of being explicit"""
        chat_client = SSNChat(self.m_client, self.chat_landing_room)
        chat_client.load(self.chat_landing_room)
        return chat_client