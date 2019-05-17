from django.forms import ModelForm
from .models import CheckStatusTask, UploadDateModel


class CheckStatusTaskForm(ModelForm):
    class Meta:
        model = CheckStatusTask
        fields = ['text_obj']


class UploadDateForm(ModelForm):
    class Meta:
        model = UploadDateModel
        fields = ['date_obj', 'tags_obj', 'lat_obj', 'lng_obj']
