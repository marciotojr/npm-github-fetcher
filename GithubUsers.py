
from MongoConnection import MongoConnection
import json
from JSON_utils import trim_json, JSONEncoder
from User_type_manager import get_type_id

user_keys_to_keep = ['id', 'login', 'name', 'company', 'blog', 'email', 'hireable', 'bio', 'followers', 'following', 'type']


def get_user(document, update=True):
    if isinstance(document, str):
        document = json.loads(document)
    document = trim_json(document, user_keys_to_keep)

    connection = MongoConnection()
    collection = connection.get_collection('github_users')
    user = collection.find_one({'id': document['id']})
    if user is None:
        user = document
        user['type'] = get_type_id(document['type'])
        JSONEncoder().encode(user)
        collection.insert(user, check_keys=False)
        user = collection.find_one({'id': document['id']})
    elif update:
        for key in document:
            user[key] = document[key]
        user['type'] = get_type_id(document['type'])
        collection.update_one({'_id': user['_id']}, {"$set": user}, upsert=True)
    return user

