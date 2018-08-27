from MongoConnection import MongoConnection
from JSON_utils import JSONEncoder


def get_type_id(type_name):
    connection = MongoConnection()
    collection = connection.get_collection('user_types')
    document = collection.find_one({'type': type_name})
    if document is None:
        max = collection.find_one(sort=[('id', -1)])
        if max is not None:
            max = max['id']
        else:
            max=-1
        document = {'type': type_name, 'id': max+1}
        JSONEncoder().encode(document)
        collection.insert(document, check_keys=False)
        document = collection.find_one({'type': type_name})
    return document['id']


def get_type_name(type_id):
    connection = MongoConnection()
    collection = connection.get_collection('user_types')
    document = collection.find_one({'id': type_id})
    return document['type']
