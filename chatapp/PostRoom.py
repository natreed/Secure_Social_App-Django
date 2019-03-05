""""""
from .SSNRoom import SSNRoom


class PostRoom(SSNRoom):
    def __init__(self, room, update_parent):
        super().__init__(room)
        self._load(update_parent)

    def _load(self, update_parent):
        events = self.room.get_events()
        for index, e in enumerate(events):
            if e['type'] == 'm.room.message' \
                    and len(e['content']['body']) > 0 \
                    and e['content']['body'][0] != '{':
                self.msg_store.append("{0}: {1}".format(
                    e['sender'], e['content']['body']))
            else:
                # we don't need to know non-message events before logon
                self.room.events.pop(index)
                # print(popped)
        room_name = self.parse_room_name_or_id(self.room.room_id)
        update_parent(room_name, self.msg_store)
