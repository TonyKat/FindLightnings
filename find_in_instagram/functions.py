import time
import json
import codecs
import datetime
import os.path
import logging
import argparse
from dateutil import parser as datetime_parser
from tqdm import tqdm

try:
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def agruments_parser():
    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description='login callback and save settings demo')
    parser.add_argument('-settings', '--settings', dest='settings_file_path', type=str, required=True)
    parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    parser.add_argument('-p', '--password', dest='password', type=str, required=True)
    parser.add_argument('-debug', '--debug', action='store_true')

    args = parser.parse_args()
    args.username, args.password, args.settings_file_path = '', '', 'test_credentials.json'
    if args.debug:
        logger.setLevel(logging.DEBUG)

    print('Client version: {0!s}'.format(client_version))
    return args


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))


def reload_api(args):
    device_id = None
    try:
        settings_file = args.settings_file_path
        if not os.path.isfile(settings_file):
            # settings file does not exist
            print('Unable to find file: {0!s}'.format(settings_file))

            # login new
            api = Client(
                args.username, args.password,
                on_login=lambda x: onlogin_callback(x, args.settings_file_path))
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            print('Reusing settings: {0!s}'.format(settings_file))

            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(
                args.username, args.password,
                settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

        # Login expired
        # Do relogin but use default ua, keys and such
        api = Client(
            args.username, args.password,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, args.settings_file_path))

    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        exit(9)
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        exit(9)
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        exit(99)

    # Show when login expires
    cookie_expiry = api.cookie_jar.auth_expires
    print('Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))
    return api


def new_write_json(json_file, name):
    with open('json_file_' + str(name) + '_.json', 'w', encoding='utf-8') as write_file:
        json.dump(json_file, write_file, indent=2, sort_keys=True, ensure_ascii=False)


def now_time_in_program(time_begin):
    print('Время исполнения программы:', time.time() - time_begin)


def find_match(medias, data_for_search, dt_correct, location):
    e = 0.01
    found_medias = []
    date = data_for_search['date']
    lat = data_for_search['lat']
    lng = data_for_search['lng']

    for media in medias:
        if media.get('layout_content').get('full_item') is None:
            new_medias = media['layout_content']['medias']
            for m in new_medias:
                dt_for_convert = m['media']['caption']['created_at']
                date_media = datetime.datetime.utcfromtimestamp(float(dt_for_convert))
                if date is not None or date != '':
                    # date_timestamp = time.mktime(datetime.datetime.strptime(date, "%Y/%m/%d").timetuple())
                    if date_media.date() == dt_correct.date():
                        if location['venues'][0]['lat'] - lat < e and \
                                location['venues'][0]['lng'] - lng < e:
                            found_medias.append(m)
                            break
        else:
            dt_for_convert = media['layout_content']['full_item']['channel']['media']['caption']['created_at']
            date_media = datetime.datetime.utcfromtimestamp(float(dt_for_convert))
            if date is not None or date != '':
                # date_timestamp = time.mktime(datetime.datetime.strptime(date, "%Y/%m/%d").timetuple())
                if date_media.date() == dt_correct.date():
                    if location['venues'][0]['lat'] - lat < e and \
                            location['venues'][0]['lng'] - lng < e:
                        found_medias.append(media)
    return found_medias


def main_function(next_max_id_main, data_for_search, found_medias):
    time_begin = time.time()
    args = agruments_parser()
    api = reload_api(args)
    try:
        dt_correct = datetime_parser.parse(data_for_search['date'])
        location = api.location_search(data_for_search['lat'], data_for_search['lng'])

        # ---------- Pagination with max_id ----------
        if next_max_id_main is None:
            results = api.tag_section(data_for_search['tag'])
        else:
            results = api.tag_section(data_for_search['tag'], max_id=next_max_id_main)
        medias = results.get('sections')
        found_medias.extend(find_match(medias, data_for_search, dt_correct, location))
        next_max_id = results.get('next_max_id')

        # за 3 часа ~ 6800-7000 новостей по 20 постов - #гроза
        i = 0
        while next_max_id:
            try:
                results = api.tag_section(data_for_search['tag'], max_id=next_max_id)
                medias = results.get('sections')
                # ищем по данным которые ввели, если подходит, то добавляем в массив
                found_medias.extend(find_match(medias, data_for_search, dt_correct, location))

                next_max_id = results.get('next_max_id')
                print(f'Iteration = {i} \t found_medias = {len(found_medias)}')
            except:
                print(f'except in main_func, len(found_medias) = {len(found_medias)}')

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))
        next_max_id_main = next_max_id or None
        print(len(found_medias))
        now_time_in_program(time_begin)
        return False, next_max_id_main, found_medias
    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        return True, None, []
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        return True, None, []
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        return True, None, []
    return True, None, found_medias
