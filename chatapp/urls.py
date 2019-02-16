from django.urls import path
from . import views


urlpatterns = [
    path('simple_chat', views.SimpleChat.as_view(), name='simple_chat'),
    path('chat_window', views.ChatWindow.as_view(), name='chat_window'),
    path('', views.get_login, name='get_login')
]

