from django.db import models
from django.utils import timezone


# TODO: Do I have to make this Global?
ssn = []


class Room(models.Model):
    room_name = models.CharField(max_length=60, unique=True)
    room_id = models.CharField(max_length=80, unique=True)
    joined = models.BooleanField(default=False)


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    msg_text = models.CharField(max_length=600)
    time_stamp = models.IntegerField(default=0)
    sender = models.CharField(max_length=100)
    background_color = models.CharField(max_length=100, default="blue")
    date_time = models.DateTimeField('date published', default=None)

    class Meta:
        get_latest_by = 'time_stamp'

    def __str__(self):
        return self.msg_text

    def get_data(self):
        return a_message(self.room, self.msg_text, self.sender, self.background_color, self.date_time)


class a_message():
    def __init__(self, _room, _msg,  _sender, _background_color, _date_time):
        self.room = _room
        self.message = _msg
        self.sender = _sender
        self.background_color = _background_color
        self.date_time = _date_time
