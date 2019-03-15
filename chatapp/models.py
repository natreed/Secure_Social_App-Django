from django.db import models
from django.template.backends import django
from django.utils import timezone
import datetime


# TODO: Do I have to make this Global?
ssn = []

class Room(models.Model):
    room_name = models.CharField(max_length=60)
    room_id = models.CharField(max_length=80, unique=True)
    is_post_room = models.BooleanField(default=True)
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
        return {
            'room': self.room.room_name,
            'message': self.msg_text,
            'sender': self.sender,
            'background_color': self.background_color,
            'date_time': self.date_time.strftime('%Y-%m-%d %H:%M')
        }


class Wall(models.Model):
    owner = models.CharField(max_length=100, default="")
    """Wall room is landing room for wall. Only friends have access to posts."""
    wall_room = models.OneToOneField(Room, on_delete=models.CASCADE, primary_key=True)
    """friends list is a space separated string of user_ids"""
    friends_list = models.CharField(default="", max_length=100000)


class Post(models.Model):
    wall = models.ForeignKey(Wall, on_delete=models.CASCADE)
    post_message = models.CharField(max_length=1000)
    room = models.OneToOneField(Room, on_delete=models.CASCADE, primary_key=True)
    post_id = models.IntegerField(unique=True, default=0)
    date_time_created = models.DateTimeField('date published', default=timezone.now)
    date_time_last_read = models.DateTimeField("Date", default=timezone.now)

    def get_data(self):
        return {
            'room': self.room.room_name,
            'message': self.post_message,
            'date_time': self.date_time_created.strftime('%Y-%m-%d %H:%M'),
            'last_read_at': self.date_time_last_read.strftime('%Y-%m-%d %H:%M')
        }






