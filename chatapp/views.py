from apscheduler.schedulers.background import BackgroundScheduler
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.views import View
from django.urls import reverse
from .forms import AuthenticationForm, AddToChatForm
from .models import Message, ssn
from .SSN import SSN
from django.db.models.signals import post_save
import json

app_name = 'chat_app'


current_messages = []
current_rooms = []


ChatWindowRequest = None


class ChatWindow(View):
    def __init__(self):
        super().__init__()
        form = AddToChatForm()
        self.context = {'form': form, 'messages': current_messages, 'rooms': current_rooms, 'user_id': ''}
        self.message_update_scheduler = BackgroundScheduler()
        post_save.connect(receiver=self.Message_Event_Handler,
                          sender=Message,
                          dispatch_uid='msg_saved')

    context = {'rooms': []}

    def get(self, request):
        chat_manager = ssn[0]
        global current_messages
        global current_rooms

        current_messages = chat_manager.get_messages()
        current_rooms = chat_manager.get_rooms()
        self.context['messages'] = current_messages
        self.context['user_id'] = chat_manager.get_user_id()
        self.context['rooms'] = current_rooms
        if request.is_ajax():
            if request.GET['element'] == 'roomsList':
                return self.change_rooms_ajax(chat_manager, request)
            # else:
            #     return HttpResponse(json.dumps({'messages': self.context['messages']}),
            #                         content_type='application/json')
        else:
            return render(request, 'matrix/chat_window.html', self.context)

    def post(self, request):
        form = AddToChatForm(request.POST, )
        if form.is_valid():
            msg = form.cleaned_data['typedtext']
            chat_manager = ssn[0]
            global current_messages
            chat_manager.current_interface.current_room.send_text(msg)
            chat_manager.current_interface.m_client._sync()
            current_messages = chat_manager.get_messages()
            self.context['messages'] = current_messages
        return render(request, 'matrix/chat_window.html', self.context)

    def change_rooms_ajax(self, chat_manager, request):
        global current_messages
        chat_manager.change_rooms(request.GET['room_name'])
        # Sync should call should trigger Message Event handler and update current messages
        chat_manager.current_interface.m_client._sync()
        current_messages = chat_manager.get_messages()
        self.context['messages'] = current_messages
        # TODO: For some reason this does not render. Requires a post to render new chat messages.
        return render(request, 'matrix/chat_window.html', self.context)

    # fires on database save
    # TODO: Unable to update messages on received message.
    def Message_Event_Handler(self, sender, instance, **kwargs):
        msg_data = instance.get_data()
        self.context['messages'].append(msg_data)


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
                b=True;
            except Exception as e:
                return render(request, 'matrix/login_form.html',
                              {'form': form, 'error_message': "error: bad login credentials"})
            else:

                ssn.append(client)

            return HttpResponseRedirect(reverse('chat_window'))  # Redirect after POST
    else:
        form = AuthenticationForm()  # An unbound form

    return render(request, 'matrix/login_form.html', {'form': form, })


