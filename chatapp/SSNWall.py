from datetime import datetime
from .SSNElement import SSNElement
from matrix_client.errors import MatrixRequestError
from .Post import Post
from .models import Room, Wall, Post, Message
import pytz
from django.utils import timezone
from django.db import IntegrityError
import json


class SSNWall(SSNElement):
    def __init__(self, client, landing_room):
        super().__init__(client, landing_room)
        # friends who have access to my wall
        self.friends = {"natreed": "natreed_wall", "bob_acosta": "bob_acosta_wall"}
        self.friend_wall_state = []
        self.user_name = self.parse_room_name_or_id(self.user_id)
        self.wall_room_name = self.parse_room_name_or_id(landing_room)
        self.last_message_event_id = None
        self.wall_db_model = None
        self.friend_wall = None
        self.landing_room = landing_room
        self.load()
        self.post_ct = 0

    def get_landing_room(self):
        return self.landing_room.room_id

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
            """Create Wall"""
            self.current_room = self.join_room(self.landing_room)
            self.wall_db_model = self.create_and_save_wall()
        self.landing_room = self.current_room
        self.save_state()

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
            owner=self.user_name,
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

    def get_posts(self, user_name):
        """
        list of wall posts
        :return:
        """
        # TODO: I know this is terrible
        if not user_name.startswith('@'):
            user_name = '@' + user_name
        post_info = []

        db_posts_qset = Post.objects.all()
        if not db_posts_qset:
            return []
        else:
            db_posts = list(db_posts_qset.filter(user_name=user_name))

        for post in db_posts:
            post_data = post.get_data()
            post_info.append(post_data)
        self.post_ct = len(db_posts)

        return post_info

    def add_post(self, msg):
        """Create the post room"""
        invitees = []
        for friend in self.friends:

            # TODO: this needs be set to whichever url is currently in use (i.e hackermath.org). should be using invitees param
            # for now I'm just setting the room to public
            invitees.append('@' + friend + ':matrix.org')
        room = self.m_client.create_room(is_public=True)

        """First make sure room is in not in Database"""
        room.set_room_name(self.user_name.lstrip('@') + "_post" + str(self.post_ct + 1))

        """If not create a db_room: Try catch block. (may already exist"""
        post_room = Room(
            owner=self.user_name,
            room_name=room.name,
            room_id=room.room_id,
            is_post_room=True,
            joined=True
        )
        try:
            post_room.save()
        except IntegrityError as e:
            post_room = list(Room.objects.filter(room_id=room.room_id))[0]

        post = Post(
            wall=self.wall_db_model,
            user_name=self.user_name,
            post_message=msg,
            room=post_room,
            post_id=self.post_ct,
            date_time_created=timezone.now()
        )
        post.save()
        self.save_state()
        self.post_ct += 1
        return post

    def save_state(self):
        """retrieves wall state from database and saves them to wall room 'topic'
        as a json string"""
        wall_data = None
        wall = Wall.objects.filter(owner=self.user_name)
        if wall:
            wall_data = list(wall)[0].get_data()
        db_posts = []
        posts = []
        rooms = []
        post_items = Post.objects.all()
        if post_items:
            db_posts = list(post_items)
        for post in db_posts:
            posts.append(post.get_data())
            rooms.append(post.room.get_data())
        wall_state = {'wall': wall_data, 'posts': posts, 'rooms': rooms}
        self.landing_room.send_text(json.dumps({'wall_state': json.dumps(wall_state)}))

    def on_message(self, room, event):
        """
        Listens and updates Message Model on message events.
        :param room:
        :param event:
        :return:
        """
        if event['event_id'] == self.last_message_event_id:
            return
        self.last_message_event_id = event['event_id']
        db_room = Room.objects.get(room_id=room.room_id)
        if event['type'] == 'm.room.message':

            if event['content']['msgtype'] == 'm.text':
                background_color = "blue"
                # TODO: set up a table with room members and their background colors
                if event['sender'] != self.m_client.user_id:
                    background_color = "red"

                local_tz = pytz.timezone("US/Pacific")
                utc_dt = datetime.fromtimestamp(event['origin_server_ts']/1000.0, local_tz)

                msg = Message(
                              msg_text=event['content']['body'],
                              time_stamp=event['origin_server_ts'],
                              sender=event['sender'],
                              background_color=background_color,
                              room=db_room,
                              date_time=utc_dt
                              )
                msg.save()

    def load_friend_wall(self, f_wall_room):
        """Loads friend wall to database if does not already exist"""
        wall_state = self.get_wall_state(f_wall_room)
        if wall_state == None:
            return
        wall_state_data = json.loads(wall_state['wall_state'])
        wall_room_name = wall_state_data['wall']['wall_room']['room_name']
        user_name = wall_state_data['wall']['owner']

        friend_wall_room = Room (
            owner=user_name,
            room_name=wall_room_name,
            room_id=f_wall_room.room_id,
            joined=True
        )
        try:
            friend_wall_room.save()
        # if the wall exists we can skip the creation step
        except IntegrityError as e:
            t = Room.objects.get(room_id=f_wall_room.room_id)
            t.owner = user_name
            return

        friend_wall = Wall (
            owner=user_name,
            wall_room=friend_wall_room,
            # TODO: need a way to add friends
            friends_list="nat-reed"
        )
        Wall.save()

        for post in wall_state_data['posts']:
            room = post['room']

            post_room = Room (
                owner=room['owner'],
                room_name=room['room_name'],
                room_id=room['room_id'],
                joined=True
            )
            post_room.save()

            new_post = Post (
                wall=friend_wall,
                user_name=user_name,
                post_message=post['message'],
                room=post_room,
                post_id=post['post_id'],
                date_time_created=post['date_time_created'],
                date_time_last_read=post['last_read_at']
            )
            new_post.save()

    def get_wall_state(self, room):
        for event in room.get_events():
            if event['type'] == 'm.room.message':
                wall_state = event['content']['body']
                if wall_state:
                    return json.loads(wall_state)
                else:
                    return {}

