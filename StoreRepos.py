from struct import pack

from MongoConnection import MongoConnection
#from NPMFetcher import get_npm_repos
import json
from bson.objectid import ObjectId
import requests
import time
from datetime import datetime, timedelta
from JSON_utils import trim_json, JSONEncoder



valid = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.']

items_to_keep_file = ['_id', '_npmVersion']
items_to_keep_web = ['author']


def get_repo(repo):
    repo = repo[:repo.rfind(',')]
    try:
        data = json.loads(repo)
        data = data['value']
        to_delete = []
        for key, value in data.items():
            if not (key in items_to_keep_file):
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
 #   file = get_npm_repos()
    file = open('npm_repos.json', 'r')
    collection = MongoConnection().get_collection('npm_repos')
    for line in file:
        try:
            repo = get_repo(line)
            if repo is not None:
                repo['id'] = repo['id'][:repo['id'].find('@')]
                try:
                    repo['numeric_version'] = version_to_float(repo['_npmVersion'])
                    del repo['_npmVersion']
                except:
                    repo['numeric_version'] = 0
                JSONEncoder().encode(repo)
                collection.insert(repo, check_keys=False)
        except:
            print('_id already exists')
        finally:
            print(repo)


def update_repos():
    connection = MongoConnection()
    collection = connection.get_collection('npm_repos')
    total = collection.find({'updated': {'$exists': False}}).count()
    currentRepo = collection.find_one({'updated': {'$exists': False}})
    count = 0
    t0 = time.time()
    longest = t0-t0
    error = False
    connection.client.close()
    last = None
    while currentRepo is not None:
        if currentRepo['id'] != last:
            last = currentRepo['id']
        t2 = time.time()
        parsed = {'updated': 'npm_fail'}
        try:
            res = requests.get('https://registry.npmjs.org/'+currentRepo['id'], timeout=5)
            if res.status_code == 200:  # check that the request went through
                parsed = json.loads(res.content.decode())
                del parsed['_id']
                parsed['numeric_version'] = currentRepo['numeric_version']
                parsed['updated'] = 'npm_json'
                print('updating repo: ' + currentRepo['id'], end=' ')
            else:
                print('failed to update: ', currentRepo['id'])
            if error:
                print('removing dollar sign from:', currentRepo['id'])
                parsed = remove_dollar_sign(parsed)
            collection.update_one({'_id': currentRepo['_id']}, {"$set": parsed})
            count += 1
            t1 = time.time()
            print((count/total)*100, end='')
            print('%')
            currentRepo = collection.find_one({'updated': {'$exists': False}})
            error = False
            total_time = (t1-t0)
            if t1-t2 > longest:
                longest = t1-t2
                d = datetime(1, 1, 1) + timedelta(seconds=int(longest))
                print('new longest time "%d:%d:%d.%d"' % (d.hour, d.minute, d.second, d.microsecond))
            total_time = total_time * total / count
            total_time = timedelta(seconds=int(total_time))
            d = datetime(1, 1, 1) + total_time
            print("%d days %d hours %d minutes %d seconds left" % (d.day - 1, d.hour, d.minute, d.second))
            if count % 200 == 0:
                d = datetime(1, 1, 1) + timedelta(seconds=int(longest))
                print('longest time so far "%d:%d:%d.%d"' % (d.hour, d.minute, d.second, d.microsecond))
                print('reopening connection')
                connection.client.close()
                connection = MongoConnection()
                collection = connection.get_collection('npm_repos')
        except KeyboardInterrupt:
            break
        except Exception as e:
            try:
                print('error')
                if error:
                    parsed = {'updated': 'npm_fail'}
                    collection.update_one({'_id': currentRepo['_id']}, {"$set": parsed})
            finally:
                error = True
                print('Error at project id: ', currentRepo['id'])
                print(e)


def fix_repos():
    connection = MongoConnection()
    collection = connection.get_collection('npm_repos')
    total = collection.find({'updated': 'npm_fail'}).count()
    currentRepo = collection.find_one({'updated': 'npm_fail'})
    count = 0
    t0 = time.time()
    longest = t0-t0
    error = False
    connection.client.close()
    last = None
    while currentRepo is not None:
        if currentRepo['id'] != last:
            last = currentRepo['id']
        t2 = time.time()
        parsed = {'updated': 'npm_fail2'}
        try:
            res = requests.get('https://registry.npmjs.org/'+currentRepo['id'], timeout=5)
            if res.status_code == 200:  # check that the request went through
                parsed = json.loads(res.content.decode())
                del parsed['_id']
                parsed['numeric_version'] = currentRepo['numeric_version']
                parsed['updated'] = 'npm_json'
                print('updating repo: ' + currentRepo['id'], end=' ')
            else:
                print('failed to update: ', currentRepo['id'])
            if error:
                print('removing dollar sign from:', currentRepo['id'])
                parsed = remove_dollar_sign(parsed)
            collection.update_one({'_id': currentRepo['_id']}, {"$set": parsed})
            count += 1
            t1 = time.time()
            print((count/total)*100, end='')
            print('%')
            currentRepo = collection.find_one({'updated': 'npm_fail'})
            error = False
            total_time = (t1-t0)
            if t1-t2 > longest:
                longest = t1-t2
                d = datetime(1, 1, 1) + timedelta(seconds=int(longest))
                print('new longest time "%d:%d:%d.%d"' % (d.hour, d.minute, d.second, d.microsecond))
            total_time = total_time * total / count
            total_time = timedelta(seconds=int(total_time))
            d = datetime(1, 1, 1) + total_time
            print("%d days %d hours %d minutes %d seconds left" % (d.day - 1, d.hour, d.minute, d.second))
            if count % 200 == 0:
                d = datetime(1, 1, 1) + timedelta(seconds=int(longest))
                print('longest time so far "%d:%d:%d.%d"' % (d.hour, d.minute, d.second, d.microsecond))
                print('reopening connection')
                connection.client.close()
                connection = MongoConnection()
                collection = connection.get_collection('npm_repos')
        except KeyboardInterrupt:
            break
        except Exception as e:
            try:
                print('error')
                if error:
                    parsed = {'updated': 'npm_fail2'}
                    collection.update_one({'_id': currentRepo['_id']}, {"$set": parsed})
                    error = False
                else:
                    error = True
            finally:
                print('Error at project id: ', currentRepo['id'])
                print(e)


def remove_dollar_sign(original):
    if isinstance(original, dict):
        clone = {}
        for key, value in original.items():
            new_key = key.replace('$', '')
            clone[new_key] = remove_dollar_sign(value)
        return clone
    elif isinstance(original, list):
        clone = []
        for item in original:
            clone.append(remove_dollar_sign(item))
        return clone
    else:
        return original


#read_repos()
update_repos()
fix_repos()
