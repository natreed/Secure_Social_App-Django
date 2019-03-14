from datetime import datetime
from .SSNElement import SSNElement
from matrix_client.errors import MatrixRequestError
from .Post import Post
from .models import Room, Wall, Post, Message
import pytz
from django.utils import timezone
from django.db import IntegrityError



class SSNWall(SSNElement):
    def __init__(self, client, landing_room):
        super().__init__(client, landing_room)
        # friends who have access to my wall
        self.user_name = self.parse_room_name_or_id(self.user_id)
        self.wall_room_name = self.parse_room_name_or_id(self.landing_room)
        # The database object
        self.wall_db_model = None
        self.load()
        self.post_ct = 0

    def load(self):
        wall_query = list(Room.objects.filter(room_name=self.wall_room_name))
        if len(wall_query) == 1:
            self.current_room = self.join_room(self.landing_room)
            """Create Wall"""
            wall_query = list(Wall.objects.filter(owner=self.user_name))
            if len(wall_query) == 0:
                self.wall_db_model = self.create_and_save_wall()
            else:
                self.wall_db_model = wall_query[0]

        elif len(wall_query) == 0:
            client_rooms = []
            for room in self.m_client.rooms.values():
                room_name = room.display_name.split(':')[0].lstrip('#')
                client_rooms.append(room_name)
            """Create a new room"""
            if self.wall_room_name not in client_rooms:
                self.try_create_wall(self.wall_room_name)
            self.current_room = self.join_room(self.landing_room)
            """Create Wall"""
            self.wall_db_model = self.create_and_save_wall()

    def try_create_wall(self, wall_name):
        try:
            self.m_client.create_room(wall_name)
        except MatrixRequestError as e:
            try:
                self.m_client.remove_room_alias('#' + wall_name + ':matrix.org')
            except MatrixRequestError as e:
                wall_name += '1'

            self.try_create_wall(wall_name)

    def create_and_save_wall(self):
        """
        :param room_query:
        :return:
        """
        """Save room to database"""
        room_entry = Room(
            room_name=self.wall_room_name,
            room_id=self.current_room.room_id,
            joined=True
        )
        try:
            room_entry.save()
        except IntegrityError as e:
            room_entry = list(Room.objects.filter(room_id=self.current_room.room_id))[0]

        wall = Wall(
            owner=self.user_name,
            wall_room=room_entry,
            # TODO: need a way to add friends
            friends_list="nat-reed"
        )
        wall.save()
        return wall

    def get_posts(self):
        """
        list of wall posts
        :return:
        """
        post_info = []
        db_posts = list(Post.objects.all())
        for post in db_posts:
            post_info.append(post.get_data())
        self.post_ct = len(db_posts)
        return post_info

    def add_post(self, msg):
        """Create the post room"""
        room = self.m_client.create_room()

        """First make sure room is in not in Database"""
        room.name = self.user_name.lstrip('@') + "_post" + str(self.post_ct + 1)

        """If not create a db_room: Try catch block. (may already exist"""
        post_room = Room(
            room_name=room.name,
            room_id=room.room_id,
            joined=True
        )
        try:
            post_room.save()
        except IntegrityError as e:
            post_room = list(Room.objects.filter(room_id=room.room_id))[0]

        post = Post(
            wall=self.wall_db_model,
            post_message=msg,
            room=post_room,
            post_id=self.post_ct,
            date_time_created=timezone.now()
        )
        post.save()
        self.post_ct += 1
        return post

    def on_message(self, room, event):
        """
        Listens and updates Message Model on message events.
        :param room:
        :param event:
        :return:
        """
        db_room = Room.objects.get(room_id=room.room_id)
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

