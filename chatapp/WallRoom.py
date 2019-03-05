""""""
from .SSNRoom import SSNRoom
import json


class WallRoom(SSNRoom):
    def __init__(self, room):
        super().__init__(room)
        # self._load()
        self.wall_store = None

    def _load(self):
        self.wall_store = json.loads(self.room.topic)
        print("hi")
        # room_events = self.room.get_events()
        # events_ct = len(room_events)
        # for i in range(0, events_ct):
        #     event = room_events.pop()
        #     if event['type'] == "m.room.message":
        #         text = event["content"]["body"]
        #         if "time_of_update" in text:
        #             wse = json.loads(event["content"]["body"])
        #             self.wall_store = wse

    def get_wall_store(self):
        return self.wall_store
