from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.utils.safestring import mark_safe
from .forms import CheckStatusTaskForm, UploadDateForm

from .tasks import task_find_image
from celery.result import AsyncResult


def main_menu(request):
    return render(request, 'find_in_instagram/main.html', {})


def find_image(request):
    print('------------------begin:find_image--------------------')
    if request.method == 'POST':
        date_form = UploadDateForm(request.POST)
        if date_form.is_valid():
            try:
                date = request.POST.get('date_obj')
                tag = request.POST.get('tags_obj')
                lat = request.POST.get('lat_obj')
                lng = request.POST.get('lng_obj')
                data_for_search = {'date': date,
                                   'tag': tag,
                                   'lat': lat,
                                   'lng': lng}
                print(type(date), date)
                print(type(tag), tag)
                print(type(lat), lat)
                print(type(lng), lng)
                task = task_find_image.apply_async(args=[data_for_search])
                print('------------------end:find_image--------------------')
                return render(request, 'find_in_instagram/find_image.html',
                              {'upload_form': UploadDateForm(),
                               'task_id': task.id})
            except Exception as e:
                print(e)
                return render(request, 'find_in_instagram/find_image.html',
                              {'upload_form': UploadDateForm(),
                               'task_id': ''})
        else:
            print('Invalid data')
            return render(request, 'find_in_instagram/error_data.html', {})
    else:
        date_form = UploadDateForm()
    return render(request, 'find_in_instagram/find_image.html',
                  {'date_form': date_form,
                   'task_id': ''})


def check_status_view(request):
    if request.method == 'POST':
        check_status_form = CheckStatusTaskForm(request.POST)
        if check_status_form.is_valid():
            try:
                text_obj = request.POST.get('text_obj')
                task = AsyncResult(text_obj)
                if task.result:
                    task_id = task.id
                    status = task.status
                    if status == 'SUCCESS':
                        task_result = task.result[0]
                        href = settings.BASE_URL_FOR_INSTA + task_result['code']
                        download_url = mark_safe('<a href="' + href + '">Открыть изображение в Instagram</a>')
                        return render(request, 'find_in_instagram/check_status.html',
                                      {'check_status_form': CheckStatusTaskForm(),
                                       'status': status,
                                       'task_id': task_id,
                                       'download_url': download_url})
                    return render(request, 'find_in_instagram/check_status.html',
                                  {'check_status_form': CheckStatusTaskForm(),
                                   'status': status,
                                   'task_id': task_id,
                                   'download_url': ''})
                else:
                    return render(request, 'find_in_instagram/error_index_check.html')
            except:
                print('Ошибка в получении данных')
                return render(request, 'find_in_instagram/check_status.html',
                              {'check_status_form': CheckStatusTaskForm(),
                               'status': '',
                               'task_id': '',
                               'download_url': ''})

        else:
            return HttpResponse('Invalid data')
    else:
        check_status_form = CheckStatusTaskForm()
        return render(request, 'find_in_instagram/check_status.html',
                      {'check_status_form': check_status_form,
                       'status': '',
                       'task_id': '',
                       'download_url': ''})