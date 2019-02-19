from apscheduler.schedulers.background import BackgroundScheduler
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.urls import reverse
from .forms import AuthenticationForm, AddToChatForm
from .models import Message, ssn
from .SSN import SSN
from django.db.models.signals import post_save
from django.dispatch import receiver


app_name = 'chat_app'
current_messages = []


# # TODO: I'd like to put the handler inside the View so I can just use context. This results in an error that I
# # haven't figured out yet.
@receiver(post_save, sender=Message)
def Message_Event_Handler(sender, instance, **kwargs):
    msg_data = instance.get_data()
    current_messages.append(msg_data)
    return


class ChatWindow(View):
    def __init__(self):
        super().__init__()
        form = AddToChatForm()
        self.context = {'form': form, 'messages': current_messages}
        self.message_update_scheduler = BackgroundScheduler()

    context = {}

    def get(self, request):
        # connect message event handler
        chat_manager = ssn[0]
        global current_messages
        current_messages = chat_manager.get_messages()
        self.context['messages'] = current_messages
        self.context['user_id'] = chat_manager.get_user_id()
        # self.message_update_scheduler.add_job(lambda: self.update_messages_context(request), 'interval', seconds=1)
        # self.message_update_scheduler.start()
        return render(request, 'matrix/chat_window.html', self.context)

    def post(self, request):
        form = AddToChatForm(request.POST, )
        if form.is_valid():
            msg = form.cleaned_data['typedtext']
            self.context['messages'] = current_messages
            chat_manager = ssn[0]
            chat_manager.current_interface.current_room.send_text(msg)
            chat_manager.current_interface.m_client._sync()

        return render(request, 'matrix/chat_window.html', self.context)

    #
    # def update_messages_context(self, request):
    #     global current_messages
    #     if len(self.context['messages']) == len(current_messages):
    #         return
    #     else:
    #         self.context['messages'] = current_messages
    #         self.chat_manager.current_interface.m_client._sync()
    #         return render(request, 'matrix/chat_window.html', self.context)


def get_login(request):
    if request.method == 'POST':  # If the form has been submitted...
        form = AuthenticationForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass
            # Process the data in form.cleaned_data
            server = form.cleaned_data['matrixServer']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            #TODO: put this in the try block when finished debugging
            client = SSN(server, username, password)
            try:
                b=True
            except Exception as e:
                return render(request, 'matrix/login_form.html',
                              {'form': form, 'error_message': "error: bad login credentials"})
            else:

                ssn.append(client)

            return HttpResponseRedirect(reverse('chat_window'))  # Redirect after POST
    else:
        form = AuthenticationForm()  # An unbound form

    return render(request, 'matrix/login_form.html', {'form': form, })


# class SimpleChat(View):
#     form = AddToChatForm()
#     context = {'form': form, 'messages': []}
#     global current_messages
#
#     def get(self, request):
#         # connect message event handler
#         chat_manager = ssn[0]
#         current_messages = chat_manager.get_messages()
#         self.context['messages'] = current_messages
#         return render(request, 'matrix/simple_chat.html', self.context)
#
#     def post(self, request):
#         form = AddToChatForm(request.POST, )
#         if form.is_valid():
#             msg = form.cleaned_data['typedtext']
#             chat_manager = ssn
#             chat_manager.current_interface.current_room.send_text(msg)
#             chat_manager.current_interface.current_room.get_events()
#
#         return render(request, 'matrix/simple_chat.html', self.context)
#
#     # # TODO: need to make this signal coming from specific room. Needs another handler.
#     # @receiver(post_save, sender=Message)
#     # def Message_Event_Handler(self, sender, instance,  **kwargs):
#     #     msg_data = instance.get_data()
#     #     self.context['messages'].append(msg_data)

