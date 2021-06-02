# chat/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/race/(?P<race_id>[0-9]+)$', consumers.RaceConsumer.as_asgi()),
]