from django.db import models
from django.utils import timezone


# Create your models here. worthyderby_4cjkids
class Race(models.Model):
    name = models.CharField('Race name', max_length=75)
    place = models.CharField('Place race occurred - opt', max_length=200)
    date = models.DateField('Date of race', auto_now_add=True)

    def __str__(self):
        return self.name + ': ' + str(self.date)


class Track(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    number = models.IntegerField('Track number')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['race', 'number'],
                name='unique track per race'
            )
        ]

    def __str__(self):
        return 'Track #' + str(self.number)


class Car(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    name = models.CharField('Car / owner name', max_length=100)
    number = models.IntegerField('Car number')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['race', 'number'],
                name='unique car per race'
            )
        ]

    def __str__(self):
        return self.name + ': ' + str(self.number)


class Run(models.Model):
    timestamp = models.DateTimeField('Timestamp of run', default=timezone.now)
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    number = models.IntegerField('Run number')
    tracks = models.JSONField('Track/car data dict')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['race', 'number'],
                name='unique run number for same race'
            )
        ]

    def __str__(self):
        return "Run #" + str(self.number)


class Trial(models.Model):
    timestamp = models.DateTimeField('Timestamp of trial', default=timezone.now)
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    mph = models.FloatField('Miles per hour')
    fps = models.FloatField('Feet per sec')
    mps = models.FloatField('Meters per sec')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['run', 'track', 'car'],
                name='unique track and car for same run'
            )
        ]

    def __str__(self):
        return "(" + str(self.car) + '): ' + str(self.mph) + ' mph'
