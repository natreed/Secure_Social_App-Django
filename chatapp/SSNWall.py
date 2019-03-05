import os
from collections import OrderedDict
from .SSNElement import SSNElement
import json
from .PostRoom import PostRoom
from .WallRoom import WallRoom
from .Post import Post
from .models import Room, Wall, Post
from datetime import datetime
import pytz
from django.utils import timezone


class SSNWall(SSNElement):
    def __init__(self, client, landing_room):
        super().__init__(client, landing_room)
        # friends who have access to my wall
        self.user_name = self.parse_room_name_or_id(self.user_id)
        self.wall_room_name = self.parse_room_name_or_id(self.landing_room)
        self.load()
        # The database object
        self.wall_db_model = None

    @classmethod
    def on_message(cls, room, event):
        return NotImplementedError

    def load(self):
        room_query = list(Room.objects.filter(room_name=self.wall_room_name))
        if len(room_query) == 1:
            self.current_room = self.join_room(self.wall_room_name)
            """Create Wall"""
            wall_query = list(Wall.objects.filter(owner=self.user_name))
            if len(wall_query) == 0:
                self.wall_db_model = self.create_and_save_wall(room_query)
            else:
                self.wall_db_model = wall_query

        elif len(room_query) == 0:
            """Create a new room"""
            room = self.m_client.create_room(self.wall_room_name)
            self.current_room = self.join_room(self.wall_room_name)
            """Save room to database"""
            room_entry = Room(
                room_name=self.wall_room_name,
                room_id=room.room_id,
                joined=True
            )
            room_entry.save()
            """Create Wall"""
            self.create_and_save_wall(room_query)

    def create_and_save_wall(self, room_query):
        """
        :param room_query:
        :return:
        """
        wall = Wall(
            owner=self.user_name,
            wall_room=room_query,
            # TODO: need a way to add friends
            friends_list="nat-reed"
        )
        wall.save()
        return wall

    def add_post(self, msg, post_room_id, post_id, room_name):
        """First make sure room is in not in Database"""
        room_query = list(Room.objects.filter(room_name=room_name))
        """If not create a db_room: Try catch block. (may already exist"""
        if len(room_query) == 0:
            post_room = Room(
                room_name=room_name,
                room_id=post_room_id,
                joined=True
            )
            post_room.save()
        else:
            post_room = room_query[0]
        """Create post entry"""
        local_tz = pytz.timezone("US/Pacific")

        post = Post(
            wall=self.wall_db_model,
            post_message=msg,
            room=post_room,
            date_time=timezone.now()
        )
        post.save()


