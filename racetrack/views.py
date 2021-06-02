from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.db import IntegrityError
from django.views import generic
# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Race, Car, Track


class IndexView(generic.ListView):
    template_name = 'racetrack/index.html'
    context_object_name = 'latest_race_list'

    def get_queryset(self):
        """Return the last five races."""
        return Race.objects.order_by('-date')[:5]


# class DetailView(LoginRequiredMixin, generic.DetailView):
class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Race
    # login_url = '/admin/login'
    template_name = 'racetrack/detail.html'


# class ResultsView(generic.DetailView):
#     model = Race
#     template_name = 'racetrack/results.html'


def speeds(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    context = {
        'race': race,
    }
    return render(request, 'racetrack/speeds.html', context)


# def manage(request, race_id):
#     race = get_object_or_404(Race, pk=race_id)
#     try:
#         car_name = request.POST['name']
#         car_number = request.POST['number']
#         new_car = Car(race=race, name=car_name, number=car_number)
#         new_car.save()
#     except IntegrityError as e:
#         # Redisplay the race detail form.
#         return render(request, 'racetrack/race.html', {
#             'race': race,
#             'error_message': e,
#         })
#     else:
#
#         # Always return an HttpResponseRedirect after successfully dealing
#         # with POST data. This prevents data from being posted twice if a
#         # user hits the Back button.
#         return HttpResponseRedirect(reverse('racetrack:results', args=[race.id]))


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


def add_run(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    try:
        track_data = []
        for track in race.track_set.all():
            track_id = track.id
            car_id = int(request.POST.get(f'{track_id}[car_id]', 0))
            if car_id:
                track_data.append({"track_id": track_id, "car_id": car_id})
        run_num = race.run_set.all().aggregate(Max('number')).get('number__max', 0) + 1
        new_run = race.run_set.create(number=run_num, tracks=track_data)
        new_run.save()
    except IntegrityError as e:
        print("error")
        print(e)
        return render(request, 'racetrack/detail.html', {
            'race': race,
            'car_error': e,
        })
    else:
        return JsonResponse({"run_num": new_run.number})
        # return render(request, 'racetrack/detail.html', {
        #     'race': race,
        # })


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

# def results(request, race_id):
#     race = get_object_or_404(Race, pk=race_id)
#     return render(request, 'racetrack/race.html', {'race': race})
