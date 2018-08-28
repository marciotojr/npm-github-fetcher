
from MongoConnection import MongoConnection
import json
from JSON_utils import trim_json, JSONEncoder, parse
from User_type_manager import get_type_id

user_keys_to_keep = ['id', 'login', 'name', 'company', 'blog', 'email', 'hireable', 'bio', 'followers', 'following',
                     'type', 'contributions']
non_persitant_keys = ['contributions']


def get_user(document, update=True):
    document = parse(document)
    document = trim_json(document, user_keys_to_keep)

    connection = MongoConnection()
    collection = connection.get_collection('github_users')
    user = collection.find_one({'id': document['id']})
    if user is None:
        user = {}
        for key in document:
            if key in user_keys_to_keep and key not in non_persitant_keys:
                user[key] = document[key]
        user['type'] = get_type_id(document['type'])
        JSONEncoder().encode(user)
        collection.insert(user, check_keys=False)
        user = collection.find_one({'id': document['id']})
    elif update:
        for key in document:
            user[key] = document[key]
        user['type'] = get_type_id(document['type'])
        collection.update_one({'_id': user['_id']}, {"$set": user}, upsert=True)
    for key in non_persitant_keys:
        if key not in user and key in document:
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

