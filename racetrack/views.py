from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.db import IntegrityError
from django.views import generic
from django.http import HttpResponseRedirect
from .models import Race, Car, Track


class IndexView(generic.ListView):
    template_name = 'racetrack/index.html'
    context_object_name = 'latest_race_list'

    def get_queryset(self):
        """Return the last five races."""
        return Race.objects.order_by('-date')[:5]


class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Race
    # login_url = '/admin/login'
    template_name = 'racetrack/detail.html'


def speeds(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    context = {
        'race': race,
    }
    return render(request, 'racetrack/speeds.html', context)


def add_car(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    try:
        car_name = request.POST['name']
        car_number = request.POST['number']
        new_car = Car(race=race, name=car_name, number=car_number)
        new_car.save()
    except IntegrityError as e:
        return render(request, 'racetrack/detail.html', {
            'race': race,
            'car_error': e,
        })
    else:
        return HttpResponseRedirect(reverse('racetrack:race', args=[race.id]))


def add_track(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    track_number = None
    try:
        track_number = request.POST['number']
        new_track = Track(race=race, number=track_number)
        new_track.save()
    except IntegrityError as e:
        if "racetrack_track.race_id, racetrack_track.number" in str(e):
            msg = f"There's already a track #{track_number}"
        else:
            msg = e
        return render(request, 'racetrack/detail.html', {
            'race': race,
            'track_error': msg,
        })
    else:
        return HttpResponseRedirect(reverse('racetrack:race', args=[race.id]))

