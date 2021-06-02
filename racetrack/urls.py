from django.urls import path

from . import views
app_name = 'racetrack'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='race'),
    path('<int:race_id>/speeds/', views.speeds, name='speeds'),
    # path('<int:race_id>/manage/', views.manage, name='manage'),
    path('<int:race_id>/car/', views.add_car, name='add_car'),
    path('<int:race_id>/run/', views.add_run, name='add_run'),
    # path('<int:race_id>/track/', views.add_track, name='add_track'),
    # path('<int:race_id>/results/', views.results, name='results'),
]