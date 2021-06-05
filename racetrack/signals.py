from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from racetrack.models import Run, Trial


from racetrack.tasks import get_leaderboard_data


@receiver(post_delete, sender=Trial, dispatch_uid="racetrack.signals.updateLeaderboard")
def updateLeaderboard(sender, instance, **kwargs):
    print("updating leaderboard")
    leaderboard = get_leaderboard_data(instance.race)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)(f'race_{instance.race.id}', {'type': 'send_msg', 'data': {'leaderboard': leaderboard}})