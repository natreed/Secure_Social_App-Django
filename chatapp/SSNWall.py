import os
from collections import OrderedDict
from .SSNElement import SSNElement
import json
from .PostRoom import PostRoom
from .WallRoom import WallRoom
from .Post import Post
import time


class SSNWall(SSNElement):
    def __init__(self, client, landing_room):
        super().__init__(client, landing_room)
        # friends who have access to my wall
        self.user_name = self.parse_room_name_or_id(self.user_id)
        self.wall_room_name = self.parse_room_name_or_id(self.landing_room)
        self.load()

    @classmethod
    def on_message(cls, room, event):
        return NotImplementedError

    def load(self):
        if self.wall_room_name in self.room_table:
            room_id = self.get_room_id(self.wall_room_name)
            if room_id in self.loaded_rooms.keys():
                self.current_room = self.loaded_rooms[room_id]
                for msg in self.all_rooms_messages[self.wall_room_name]:
                    print(msg)
            else:
                self.join_wall_room(room_id)
        elif self.owner:
            room = self.m_client.create_room(self.wall_room_name)
            room.set_room_name(self.wall_room_name)
            self.room_table[self.wall_room_name] = {"room_id": room.room_id, "loaded": False}
            self.current_room = WallRoom(room)
            self.loaded_rooms[room.room_id] = self.current_room
        else:
            print("you do not have permission to view this wall. ask your buddy for an invite.")
            return

        self.render()
        self.initialized = True

    def load_wall_state(self):
        """Try loading from room topic. If that doesn't work, load from backup file"""
        try:
            self.wall_state = json.loads(self.current_room.room.topic)
            if self.wall_state["posts"]:
                for post_id, post in self.wall_state["posts"].items():
                    self.add_post(post["msg"], post["room_id"], int(post_id), post["room_name"])
                    self.post_id += 1
        except TypeError:
            if self.owner:
                print("Room topic empty. Loading state from file")
                self.initialize_from_file()

    def initialize_from_file(self):
        if os.stat("./{}".format(self.wall_store_file)).st_size != 0:
            with open(self.wall_store_file, 'r+') as json_file:
                self.wall_state = json.load(json_file)
            self.friends = self.wall_state["friends"]
            for key, post in self.wall_state["posts"].items():
                room_id_alias = post["room_id"]
                self.add_post(post["msg"], room_id_alias, self.post_id, post["room_name"])
                self.post_id += 1
            self.update_wall_state()
            self.initialized = True
            return

    def join_wall_room(self, room_id):
        self.current_room = WallRoom(self.join_room(self.landing_room, event_limit=20))
        self.loaded_rooms[room_id] = self.current_room
        self.load_wall_state()
        self.room_table[self.wall_room_name]["loaded"] = True

    def update_wall_state(self):
        """
        Called on program exit. Sends state to wall_room so that friends can reproduce wall
        right now state is stored in room.topic
        :return:
        """
        state_string = self.wall_state_to_json()
        self.current_room.room.set_room_topic(state_string)
        # print("print statement for testing")

    def wall_state_to_json(self):
        posts_info = {}
        for key, post in self.posts.items():
            posts_info[key] = {"room_id": post.room_id,
                               "msg": post.message,
                               "post_id": int(post.post_id),
                               "room_name": post.get_room_name()}
        state = {"friends": self.friends, "posts": posts_info}
        state_string = json.dumps(state)
        return state_string

    def post_comment(self, msg_dict):
        post_id = msg_dict['comment_post']
        if type(post_id) == str:
            post_id = int(post_id)
        post = self.posts[post_id]
        room_id_alias = post.room_id
        room_name = self.parse_room_name_or_id(room_id_alias)
        if room_id_alias in self.loaded_rooms:
            self.current_room = self.loaded_rooms[room_id_alias]
        else:
            post_room = self.join_room(room_id_alias, print_room=False)
            self.current_room = PostRoom(post_room, self.init_msg_hist_for_room)
            self.loaded_rooms[post.room_id] = self.current_room
            self.room_table[room_name] = post_room.room_id

        if msg_dict['sender'] == self.user_id:
            print("POST MESSAGE: {}".format(post.message))
            for msg in self.all_rooms_messages[room_name]:
                print(msg)

        print("Post comment here ...\n")

    def invite_friend(self, user_name):
        """friends will be able to see the Wall"""
        self.friends[user_name] = ""

    def render(self):
        """prints all the posts"""
        # call('clear')
        for post in self.posts.values():
            post.print(self.m_client.user_id)
        return

    def add_post(self, msg, post_room_id, post_id, room_name):
        self.posts[post_id] = Post(post_room_id, msg, post_id, room_name)
        self.update_wall_state()

