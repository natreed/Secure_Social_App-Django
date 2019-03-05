from matrix_client.errors import MatrixRequestError

from .SSNWall import SSNWall
import json
from .PostRoom import PostRoom



class ClientWall(SSNWall):
    def __init__(self, client, landing_room):
        super().__init__(client, landing_room)

    def on_message(self, room, event):
        if not self.initialized:
            return
        if event['type'] == "m.room.member":
            if event['content']['membership'] == "join":
                if self.rendered and self.is_room_setup \
                        and self.current_room.get_room_id() not in self.loaded_rooms:
                    print("{0} joined".format(event['content']['displayname']))
        elif event['type'] == "m.room.message":
            msg_body = event['content']['body']
            if msg_body == 'show_wall':
                self.render()
                return
            # Wall handler passes a json formatted dictionary
            elif msg_body.startswith('{') and msg_body.endswith('}') and self.rendered:
                """message is a json string"""
                msg_dict = json.loads(msg_body)
                msg_dict['sender'] = event['sender']
                if "add_post" in msg_dict.keys():
                    self.post_msg(msg_dict)
                elif "comment_post" in msg_dict.keys():
                    self.post_comment(msg_dict)
                elif "remove_post" in msg_dict.keys():
                    if msg_dict['remove_post'] == 'a':
                        self.remove_all_posts()
                    else:
                        self.remove_post(msg_dict['remove_post'])
            else:
                self.send_room_message(room, event)
        self.rendered = True

    def post_msg(self, msg_dict):
        msg = msg_dict['add_post']
        room = self.m_client.create_room(is_public=True)
        room.add_listener(self.on_message)
        room.name = self.parse_room_name_or_id(room.room_id)
        pst_room = PostRoom(room, self.init_msg_hist_for_room)
        self.loaded_rooms[pst_room.get_room_id()] = pst_room
        self.room_table[room.name] = pst_room.get_room_id()
        self.add_post(msg, pst_room.get_room_id(), self.post_id, room.name)
        self.render()
        self.post_id += 1
        self.update_wall_store()

    def update_wall_store(self):
        """write current state to a file when finished. Can be brought back when
        Client starts again."""
        state_string = self.wall_state_to_json()
        with open('./{}'.format(self.wall_store_file), 'w') as outfile:
            outfile.write(state_string)
        return

    def remove_post(self, post_id):
        post = self.posts[post_id]
        try:
            self.m_client.api.leave_room(post.room_id)
        except MatrixRequestError as e:
            if e.code == 404: # not a known room
                print("not a known room")
            else:
                print(e)
        print("Post {} removed.".format(post_id))
        self.update_wall_store()

    def remove_all_posts(self):
        """for when shit hits the fan"""
        for key, post in self.posts.items():
            self.remove_post(post.post_id)
        self.posts = {}
        self.update_wall_store()
        self.update_wall_state()


