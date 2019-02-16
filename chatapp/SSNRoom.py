from matrix_client.client import MatrixClient, Room
from enum import Enum


class RoomType(Enum):
    CHAT = 1
    WALL = 2
    POST = 3


class SSNRoom(object):
    """Room wrapper to add extra state."""
    def __init__(self, room):
        """update_parent is a function called when room is first joined.
        this will add the message history to the rooms and will be saved in the wall
        record. The wall record will be a json object stored in a room event in the
        wall point of entry room."""
        self.room = room
        self.msg_store = []

    @classmethod
    def _load(cls, **kwargs):
        raise NotImplementedError

    def parse_room_name_or_id(self, alias_user_id_or_room_id):
        return alias_user_id_or_room_id.split(':')[0].lstrip('#')

    def set_room_name(self, name):
        return self.room.set_room_name(name)

    def get_room_name(self):
        return self.room.name

    def get_room_id(self):
        return self.room.room_id

    def leave_room(self):
        return self.room.leave()




