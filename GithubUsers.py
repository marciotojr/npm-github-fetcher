
from MongoConnection import MongoConnection
import json
from JSON_utils import trim_json, JSONEncoder, parse
from User_type_manager import get_type_id
import requests
from Errors import NoRepositoryFoundError, GithubAccessLimitReachedError, NoUserUnupdated
import time
from datetime import datetime, timedelta


auth_token = 'token 9c32ed46fe5e4addb495a4c5c84ac56c48182520'
user_agent = 'Mozilla/5.0'
payload = {'Authorization': auth_token, 'User-Agent': user_agent}

persistent_keys = ['id', 'login', 'name', 'company', 'blog', 'email', 'hireable', 'bio', 'followers', 'following',
                     'type']
non_persitent_keys = ['contributions']

connection = MongoConnection()
collection = connection.get_collection('github_users')


def get_user(document, update=True):
    document = parse(document)

    user = collection.find_one({'id': document['id']})
    if user is None:
        user = trim_json(document, persistent_keys)
        user['type'] = get_type_id(document['type'])
        JSONEncoder().encode(user)
        collection.insert(user, check_keys=False)
        user = collection.find_one({'id': document['id']})
    elif update:
        for key in document:
            if key in persistent_keys:
                user[key] = document[key]
        user['type'] = get_type_id(document['type'])
        collection.update_one({'_id': user['_id']}, {"$set": user}, upsert=True)
    for key in non_persitent_keys:
        if key in document:
            user[key] = document[key]
    return user


def format_user_list(document):
    document = parse(document)
    user_list = []
    for user in document:
        user = get_user(user)
        del user['_id']
        user_list.append(user)
    return user_list


def update_users():
    total = collection.find({'followers': {'$exists': False}}).count()

    current_user = next_user()
    count = 0
    t0 = time.time()
    while current_user is not None:
        try:
            print('Analyzing user ', current_user['login'])

            document = get_request('users/' + current_user['login'])

            get_user(document, update=True)

            count += 1
            t1 = time.time()
            print((count / total) * 100, end='')
            print('%')
            total_time = (t1 - t0)
            total_time = total_time * total / count
            total_time = timedelta(seconds=int(total_time))
            d = datetime(1, 1, 1) + total_time
            print("%d days %d hours %d minutes %d seconds left" % (d.day - 1, d.hour, d.minute, d.second))
        except KeyboardInterrupt:
            break
        except requests.exceptions.ConnectionError:
            print('General error, sleeping for 60 secs')
            time.sleep(60)
            continue
        except NoUserUnupdated:
            print('All users are updated')
            time.sleep(900)
        finally:
            current_user = next_user()


def next_user():
    return collection.find_one({'followers': {'$exists': False}})


def get_request(path):
    r = requests.get('https://api.github.com/' + path, headers=payload)
    print(r.headers.get('X-RateLimit-Remaining'), end='\t')
    if '200' not in r.headers.get('status'):
        raise NoRepositoryFoundError
    if r.headers.get('X-RateLimit-Remaining') == 0:
        raise GithubAccessLimitReachedError('Github access limit reached')
    return r.text

update_users()