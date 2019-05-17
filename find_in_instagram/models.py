from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class CheckStatusTask(models.Model):
    text_obj = models.CharField(verbose_name='Введите идентификатор:', max_length=40)


class UploadDateModel(models.Model):
    date_obj = models.DateField(verbose_name='Введите дату:', blank=False)
    tags_obj = models.CharField(verbose_name='Введите тег:', max_length=100, blank=False)
    lat_obj = models.FloatField(verbose_name='Введите широту:', blank=False)  # , default=str(59.93))
    lng_obj = models.FloatField(verbose_name='Введите долготу:', blank=False)  #, default=str(30.31))
    #latitude longitude