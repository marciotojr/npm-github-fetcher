from MongoConnection import MongoConnection
import pymongo
from NPMFetcher import get_npm_repos
import time
import json, urllib.request
from bson.objectid import ObjectId


valid = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.']

items_to_keep = ['_id', 'keywords', 'repository', 'maintainers', '_npmVersion', 'dependencies', 'author']


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def get_repo(repo):
    repo = repo[:repo.rfind(',')]
    try:
        data = json.loads(repo)
        data = data['value']
        to_delete = []
        for key, value in data.items():
            if not (key in items_to_keep):
                to_delete.append(key)
        for key in to_delete:
            del data[key]
        data['id'] = data['_id']
        del data['_id']
        return data
    except:

        return None


def version_to_float(version_str):
    original =''
    for c in version_str:
        original += c
    for c in version_str:
        if c not in valid:
            version_str = version_str.replace(c, '')
    point = 0
    for c in version_str:
        if c == '.':
            point +=1
    if point > 1:
        pos = version_str.find('.')
    try:
        return float(version_str[:pos+1] + version_str[pos+2:].replace('.', ''))
    except:
        print('------------------------------------------------------- ' + original)
        return 0


def read_repos():
    file = get_npm_repos()
    collection = MongoConnection().get_collection('npm_repos')
    for line in file:
        try:
            repo = get_repo(line)
            if repo is not None:
                repo['id'] = repo['id'][:repo['id'].find('@')]
                try:
                    repo['numeric_version'] = version_to_float(repo['_npmVersion'])
                except:
                    repo['numeric_version'] = 0
                JSONEncoder().encode(repo)
                collection.insert(repo, check_keys=False)
        except:
            print('_id already exists')
        finally:
            print(repo)


read_repos()
#prioritize()
