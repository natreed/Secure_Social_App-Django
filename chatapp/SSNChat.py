from .SSNElement import SSNElement
from .models import Room, Message
from django.utils import timezone
from datetime import datetime
import pytz


class SSNChat(SSNElement):
    """a wrapper class for client to add social network state variables"""
    def __init__(self, client, landing_room):
        super().__init__(client, landing_room)
        self.type = 'C'  # c as in client
        self.user_id = self.m_client.user_id
        self.load(landing_room)

    def load(self, room_id_alias):
        room_name = self.parse_room_name_or_id(room_id_alias)
        room_query = list(Room.objects.filter(room_name=room_name))
        if len(room_query) == 1:
            self.current_room = self.join_room(room_id_alias)

        elif len(room_query) == 0:
            """Create a new room"""
            room = self.m_client.create_room(room_name)
            room.set_room_name(room_name)
            self.current_room = self.join_room(room_id_alias)
            """add that room to the database"""
            room_entry = Room(
                room_name=room_name,
                room_id=room.room_id,
                joined=True
            )
            room_entry.save()


    def on_message(self, room, event):
        """
        Listens and updates Message Model on message events.
        :param room:
        :param event:
        :return:
        """

        db_room = Room.objects.get(room_name=room.name)
        if event['type'] == 'm.room.message':
            if event['content']['msgtype'] == 'm.text':
                background_color = "blue"
                # TODO: set up a table with room members and their background colors
                if event['sender'] != self.m_client.user_id:
                    background_color = "red"

                local_tz = pytz.timezone("US/Pacific")
                utc_dt = datetime.fromtimestamp(event['origin_server_ts']/1000.0, local_tz)

                msg = Message(msg_text=event['content']['body'],
                              time_stamp=event['origin_server_ts'],
                              sender=event['sender'],
                              background_color=background_color,
                              room=db_room,
                              date_time=utc_dt
                              )

                msg.save()







