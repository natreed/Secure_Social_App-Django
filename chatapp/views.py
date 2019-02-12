from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic, View
from django.urls import reverse
from .forms import AuthenticationForm, AddToChatForm
from .models import Client, Message, CLIENTS

app_name = 'chat_app'


class SimpleChat(View):
    form = AddToChatForm()
    context = {'form': form, 'messages': Message.objects.order_by('time_stamp')}

    def get(self, request):
        return render(request, 'matrix/simple_chat.html', self.context)

    def post(self, request):
        form = AddToChatForm(request.POST, )
        if form.is_valid():
            msg = form.cleaned_data['typedtext']
            client = CLIENTS[0]
            self.context['mclient'] = client.mclient
            client.current_room.send_text(msg)
            # TODO: Save All data Locally. Sync Less
            client.mclient._sync()
            self.context['messages'] = Message.objects.order_by('time_stamp')

        return render(request, 'matrix/simple_chat.html', self.context)


def get_login(request):
    if request.method == 'POST':  # If the form has been submitted...
        form = AuthenticationForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass
            # Process the data in form.cleaned_data
            server = form.cleaned_data['matrixServer']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            client = Client(server, username, password)
            try:
                b = True
            except Exception as e:
                return render(request, 'matrix/login_form.html',
                              {'form': form, 'error_message': "error: bad login credentials"})
            else:
                CLIENTS.append(client)

            return HttpResponseRedirect(reverse('simple_chat'))  # Redirect after POST
    else:
        form = AuthenticationForm()  # An unbound form

    return render(request, 'matrix/login_form.html', {'form': form, })




