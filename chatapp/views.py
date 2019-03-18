from apscheduler.schedulers.background import BackgroundScheduler
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.views import View
from django.urls import reverse
from .forms import AuthenticationForm, AddToChatForm, AddPostForm
from .models import Message, ssn, Room, Wall
from .SSN import SSN
from django.db.models.signals import post_save

app_name = 'chat_app'

# current view: this is for re-rendering correct view when
current_messages = []
posts = []
all_rooms = []

ChatWindowRequest = None


class Welcome(View):
    def __init__(self):
        super().__init__()

    context = {}

    def get(self, request):
        return render(request, 'matrix/welcome.html')


"""#################################### WALL #########################################"""


class WallView(View):
    def __init__(self):
        super(WallView, self).__init__()
        form = AddPostForm()
        self.context = {'form': form,
                        'posts': posts,
                        'current_room': None,
                        'is_owner': False,
                        'is_wall': False,
                        'messages': [],
                        'friends': []}

    def get(self, request):
        chat_manager = ssn[0]
        chat_manager.current_interface = chat_manager.wall_client
        self.context['friends'] = chat_manager.wall_client.friends
        global posts
        global current_messages
        current_messages = []
        posts = chat_manager.wall_client.get_posts(chat_manager.wall_client.user_name)
        user_id = chat_manager.get_user_id()
        room_name = chat_manager.wall_client.current_room.name
        if user_id in room_name:
            self.context['is_owner'] = True
        if 'wall' in room_name:
            self.context['is_wall'] = True
        self.context['current_room'] = room_name
        self.context['posts'] = posts
        return render(request, 'matrix/wall_window.html', self.context)

    def post(self, request):
        chat_manager = ssn[0]
        self.context['friends'] = chat_manager.wall_client.friends.keys()
        global current_messages
        if 'render_chat' in request.POST:
            room_id = Room.objects.all().filter(room_name=request.POST['render_chat'])[0].room_id
            chat_manager.change_rooms(room_id)
            chat_manager.wall_client.current_room.name = request.POST['render_chat']
        elif 'chat-input' in request.POST:
            msg = request.POST['chat-input']
            if msg != "":
                chat_manager.wall_client.current_room.send_text(msg)
        else:
            form = AddToChatForm(request.POST, )
            if form.is_valid():
                msg = form.cleaned_data['typedtext']
                if msg != "":
                    post = chat_manager.wall_client.add_post(msg)
                posts.append(post.get_data())
        self.context['posts'] = posts
        chat_manager.wall_client.m_client._sync()
        user_id = chat_manager.get_user_id()
        room_name = chat_manager.wall_client.current_room.name
        if user_id in room_name:
            self.context['is_owner'] = True
        if 'wall' in room_name:
            self.context['is_wall'] = True
        self.context['current_room'] = room_name
        current_messages = chat_manager.get_current_room_messages()
        self.context['messages'] = current_messages

        return render(request, 'matrix/wall_window.html', self.context)

"""############################### FRIEND WALL"""

class FriendWall(View):
    def __init__(self):
        super(FriendWall, self).__init__()
        form = AddPostForm()
        self.context = {'form': form,
                        'posts': posts,
                        'current_room': None,
                        'is_owner': False,
                        'is_wall': False,
                        'messages': [],
                        'friends': []}

    def get(self, request):
        global current_messages
        global posts
        chat_manager = ssn[0]
        chat_manager.current_interface = chat_manager.wall_client
        self.context['friends'] = chat_manager.wall_client.friends.keys()
        friend_user_name = request.GET['render_wall']
        if friend_user_name:
            chat_manager.change_rooms(chat_manager.wall_client.friends[friend_user_name])
            chat_manager.wall_client.load_friend_wall(chat_manager.wall_client.current_room)
            posts = chat_manager.wall_client.get_posts(friend_user_name)
        current_messages = []
        user_id = chat_manager.get_user_id()
        room_name = chat_manager.wall_client.current_room.name
        if user_id in room_name:
            self.context['is_owner'] = True
        if 'wall' in room_name:
            self.context['is_wall'] = True
        self.context['current_room'] = room_name
        self.context['posts'] = posts
        return render(request, 'matrix/wall_window.html', self.context)

    def post(self, request):
        chat_manager = ssn[0]
        self.context['friends'] = chat_manager.wall_client.friends.keys()
        global current_messages
        if 'render_chat' in request.POST:
            room_id = Room.objects.all().filter(room_name=request.POST['render_chat'])[0].room_id
            chat_manager.change_rooms(room_id)
            chat_manager.wall_client.current_room.name = request.POST['render_chat']
        elif 'chat-input' in request.POST:
            msg = request.POST['chat-input']
            if msg != "":
                chat_manager.wall_client.current_room.send_text(msg)
        else:
            form = AddToChatForm(request.POST, )
            if form.is_valid():
                msg = form.cleaned_data['typedtext']
                if msg != "":
                    post = chat_manager.wall_client.add_post(msg)
                posts.append(post.get_data())
        self.context['posts'] = posts
        chat_manager.wall_client.m_client._sync()
        user_id = chat_manager.get_user_id()
        room_name = chat_manager.wall_client.current_room.name
        if user_id in room_name:
            self.context['is_owner'] = True
            self.context['is_wall'] = False
        if 'wall' in room_name:
            self.context['is_wall'] = True
        self.context['current_room'] = room_name
        current_messages = chat_manager.get_current_room_messages()
        self.context['messages'] = current_messages

        return render(request, 'matrix/wall_window.html', self.context)

"""#################################### CHAT #########################################"""


class ChatWindow(View):
    def __init__(self):
        super().__init__()
        form = AddToChatForm()
        self.context = {'form': form, 'messages': current_messages, 'current_room': None, 'rooms': all_rooms, 'user_id': None}
        #TODO : What what is BackgroundScheduler. Not being used
        # self.message_update_scheduler = BackgroundScheduler()
        post_save.connect(receiver=self.Message_Event_Handler,
                          sender=Message,
                          dispatch_uid='msg_saved')

    context = {'rooms': []}
    username = None

    def get(self, request):
        chat_manager = ssn[0]
        self.username = chat_manager.get_user_id()
        chat_manager.current_interface = chat_manager.chat_client
        chat_manager.change_rooms(chat_manager.chat_client.get_landing_room())
        global current_messages
        global all_rooms
        # global current_url
        # current_url = 'chat_window'
        current_messages = chat_manager.get_current_room_messages()
        all_rooms = chat_manager.get_chat_rooms()
        self.context['current_room'] = chat_manager.chat_client.current_room.display_name
        self.context['messages'] = current_messages
        self.context['user_id'] = chat_manager.get_user_id()
        self.context['rooms'] = all_rooms
        return render(request, 'matrix/chat_window.html', self.context)

    def post(self, request):
        chat_manager = ssn[0]
        self.username = chat_manager.get_user_id()
        global current_messages


        if 'render_chat' in request.POST:
            room = Room.objects.all().filter(room_name=request.POST['render_chat'])[0]
            room_id = room.room_id
            chat_manager.change_rooms(room_id)
            chat_manager.chat_client.current_room.name = request.POST['render_chat']
        elif 'chat-input' in request.POST:
            msg = request.POST['chat-input']
            if msg != "":
                chat_manager.chat_client.current_room.send_text(msg)
        chat_manager.chat_client.m_client._sync()
        self.context['current_room'] = chat_manager.chat_client.current_room.display_name
        self.context['messages'] = chat_manager.get_current_room_messages()
        return render(request, 'matrix/chat_window.html', self.context)

    # fires on database save
    # TODO: Unable to update messages on received message.
    def Message_Event_Handler(self, sender, instance, **kwargs):
        if self.username not in instance.sender:
            # return HttpResponseRedirect(reverse('chat_window'))
            pass
        else:
            pass

"""#################################### WALL #########################################"""

def get_login(request):
    """
    :param request:
    :return:
    """
    if request.method == 'POST':  # If the form has been submitted...
        form = AuthenticationForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass
            # Process the data in form.cleaned_data
            server = form.cleaned_data['matrixServer']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            client = SSN(server, username, password)
            try:
                b=True
            except Exception as e:
                return render(request, 'matrix/login_form.html',
                              {'form': form, 'error_message': "error: bad login credentials"})
            else:

                ssn.append(client)

            return HttpResponseRedirect(reverse('welcome'))  # Redirect after POST
    else:
        form = AuthenticationForm()  # An unbound form

    return render(request, 'matrix/login_form.html', {'form': form, })


