from FindLightnings.celery import app
from celery.utils.log import get_task_logger
from .functions import reload_api, main_function
from dateutil import parser as datetime_parser


logger = get_task_logger(__name__)


@app.task()
def task_find_image(data_for_search):
    found_medias = []
    logger.info('Task: task_find_image - SUCCESS')
    try:
        flag, next_max_id_main, found_medias = main_function(None, data_for_search, found_medias)
        while not flag:
            flag, next_max_id_main, found_medias = main_function(next_max_id_main, data_for_search, found_medias)
    except Exception as e:
        print('(my) Unexpected Exception: {0!s}'.format(e))
    return found_medias
