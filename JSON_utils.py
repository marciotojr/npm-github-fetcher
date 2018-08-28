import json
from bson.objectid import ObjectId
from Errors import InvalidJSONConversion


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def trim_json(document, keys_to_keep):
    if isinstance(document, str):
        document = json.loads(document)
    value = {}
    for key in document:
        if key in keys_to_keep:
            value[key] = document[key]
    return value


def parse(document):
    if isinstance(document, dict):
        return document
    elif isinstance(document, str):
        return json.loads(document)
    raise InvalidJSONConversion('This is not in a format able to be converted into JSON')