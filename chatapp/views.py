from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.urls import reverse
from .forms import AuthenticationForm, AddToChatForm
from .models import Client, Message, CLIENTS, get_objects, a_message
from django.db.models.signals import post_save

from django.dispatch import receiver
from django.core.signals import request_finished


app_name = 'chat_app'


class SimpleChat(View):
    form = AddToChatForm()
    context = {'form': form, 'messages': get_objects()}

    def get(self, request):
        # connect message event handler
        post_save.connect(receiver=self.Message_Event_Handler, sender=Message)
        return render(request, 'matrix/simple_chat.html', self.context)

    def post(self, request):
        form = AddToChatForm(request.POST, )
        if form.is_valid():
            msg = form.cleaned_data['typedtext']
            client = CLIENTS[0]
            client.current_room.send_text(msg)
            # TODO: Save All data Locally. Sync Less
            client.mclient._sync()

            # self.context['messages'] = Message.objects.order_by('time_stamp')

        return render(request, 'matrix/simple_chat.html', self.context)

    @receiver(post_save, sender=Client)
    def Message_Event_Handler(self, sender, instance,  **kwargs):
        msg_data = instance.get_data()
        self.context['messages'].append(msg_data)


class ChatWindow(View):
    form = AddToChatForm()
    context = {'form': form, 'messages': get_objects()}

    def get(self, request):
        # connect message event handler
        client = CLIENTS[0]
        rooms = list(client.mclient.rooms.values())
        dispnm1 = rooms[0].display_name()
        room_names = list(filter(lambda x: x.display_name, rooms))
        post_save.connect(receiver=self.Message_Event_Handler, sender=Message)
        return render(request, 'matrix/simple_chat.html', self.context)

    def post(self, request):
        form = AddToChatForm(request.POST, )
        if form.is_valid():
            msg = form.cleaned_data['typedtext']
            client = CLIENTS[0]
            client.current_room.send_text(msg)
            # TODO: Save All data Locally. Sync Less
            client.mclient._sync()

            # self.context['messages'] = Message.objects.order_by('time_stamp')

        return render(request, 'matrix/simple_chat.html', self.context)

    @receiver(post_save, sender=Client)
    def Message_Event_Handler(self, sender, instance,  **kwargs):
        msg_data = instance.get_data()
        self.context['messages'].append(msg_data)



def get_login(request):
    if request.method == 'POST':  # If the form has been submitted...
        form = AuthenticationForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass
            # Process the data in form.cleaned_data
            server = form.cleaned_data['matrixServer']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            #TODO: put this in the try block when finished debugging
            client = Client(server, username, password)
            try:
                b=True
            except Exception as e:
                return render(request, 'matrix/login_form.html',
                              {'form': form, 'error_message': "error: bad login credentials"})
            else:

                CLIENTS.append(client)

            return HttpResponseRedirect(reverse('chat_window'))  # Redirect after POST
    else:
        form = AuthenticationForm()  # An unbound form

    return render(request, 'matrix/login_form.html', {'form': form, })




