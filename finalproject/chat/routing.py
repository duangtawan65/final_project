from django.urls import path , include
from chat.consumers import ChatConsumer
from django.urls import re_path
from . import consumers

# Here, "" is routing to the URL ChatConsumer which
# will handle the chat functionality.
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]