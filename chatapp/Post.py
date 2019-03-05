class Post(object):
    def __init__(self, post_room_id, msg, post_id, room_name):
        """
        :param room_id:
        :param msg:
        :param post_id:
        :param client:

        The post comment room is not joined until someone wants to post a comment in that room.
        After a room is joined it is added to the loaded rooms list.
        """
        self.message = msg
        # post rooms need to be set asynchronously
        self.post_room = None
        self.post_id = post_id
        self.room_id = post_room_id
        self.room_name = room_name
        self.user_id = None
        self.comments = []

    def get_room_name(self):
        if self.post_room:
            return self.room_name

    def set_room_name(self, name):
        return self.post_room.set_room_name(name)

    def print(self, user_id):
        print("id={0}: {1}: {2}".format(self.post_id, user_id, self.message))

