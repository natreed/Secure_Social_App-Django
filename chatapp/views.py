from django.shortcuts import render
from django.views import generic
from .models import Client

class IndexView(generic.ListView):
    template_name = 'matrix/index.html'
    context_object_name = 'message_list'

    def get_queryset(self):
        msgs = []

# Create your views here.
def index(request):
    client = Client()
    client.current_room.events.clear()
    msgs = client.get_message_list()

    context = {'mclient': client, 'messages': msgs}


    #just a small test
    msgs.append(client.send_messages_test())

    return render(request, 'matrix/index.html', context)

