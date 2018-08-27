from operator import concat

from MongoConnection import MongoConnection
# from NPMFetcher import get_npm_repos
import json
from bson.objectid import ObjectId
import requests
import time
from datetime import datetime, timedelta
from GithubUsers import get_user
from JSON_utils import trim_json, JSONEncoder

auth_token = 'token 7ef69b2368773c233c5f7d29039eadf9cb55c05c'
user_agent = 'Mozilla/5.0'
payload = {'Authorization': auth_token, 'User-Agent': user_agent}
repo_keys_to_keep = ['id', 'name', 'full_name', 'owner', 'description', 'homepage', 'stargazers_count', 'has_wiki'
    , 'watchers_count', 'forks_count', 'watchers', 'organization', 'network_count', 'subscribers_count']


def update_repos():
    connection = MongoConnection()
    collection = connection.get_collection('npm_repos')
    total = collection.find({'updated': 'npm_json'}).count()
    currentRepo = collection.find_one({'updated': 'npm_json'}, sort=[('numeric_version', -1)])
    count = 0
    t0 = time.time()
    error = False
    connection.client.close()
    while currentRepo is not None:
        print(get_github_user_repo(currentRepo))
        parsed = {'updated': 'github_fail'}
        try:
            res = requests.get('https://registry.npmjs.org/' + currentRepo['id'])

            if res.status_code == 200:  # check that the request went through
                parsed = json.loads(res.content.decode())
                del parsed['_id']
                parsed['numeric_version'] = currentRepo['numeric_version']
                parsed['updated'] = 'npm_json'
                print('updating repo: ' + currentRepo['id'], end=' ')
            else:
                print('failed to update: ', currentRepo['id'])
                pass
            if error:
                print('removing dollar sign from:', currentRepo['id'])
                error = False
            # collection.update_one({'_id': currentRepo['_id']}, {"$set": parsed})
            count += 1
            t1 = time.time()
            print((count / total) * 100, end='')
            print('%')
            currentRepo = collection.find_one({'updated': 'npm_json'}, sort=[('numeric_version', -1)])
            total_time = (t1 - t0)
            total_time = total_time * total / count
            total_time = timedelta(seconds=int(total_time))
            d = datetime(1, 1, 1) + total_time
            print("%d days %d hours %d minutes %d seconds left" % (d.day - 1, d.hour, d.minute, d.second))
            if count % 200 == 0:
                print('reopening connection')
                connection.client.close()
                connection = MongoConnection()
                collection = connection.get_collection('npm_repos')
        except KeyboardInterrupt:
            break
        except Exception as e:
            error = True
            print('Error at project id: ', currentRepo['id'])
            print(e)
            print(type(e))
        # except:
        # print('error')di
        # break


def get_github_user_repo(document):  # returns a tuple with user and repo
    if isinstance(document, dict):
        if 'repository' in document:
            if 'url' in document['repository'] and 'type' in document['repository'] and document['repository'][
                'type'] == 'git':
                url = document['repository']['url']
                url = url[0: url.rfind('.git')]
                repo = url[url.rfind('/') + 1:]
                url = url[:url.rfind('/')]
                user = url[url.rfind('/') + 1:]
                return user, repo
            else:
                return None  # TODO return error for non-github repositories and log if possible
        else:
            if 'versions' in document:
                return get_github_user_repo(document['versions'])
    elif isinstance(document, list):
        for version in document:
            for keys in version:
                value = version[keys]
                if value is not None:
                    return value
        return None  # TODO verify in the list of versions
    else:
        return None  # TODO return no repository found error and log if possible


def fetch_github_info(path_or_owner, repo=None):
    owner, repo = solve_owner_repo_names(path_or_owner, repo)
    content, limit, headers = get_request('repos/' + owner + '/' + repo)
    document = trim_json(content, repo_keys_to_keep)
    user = get_user(document['owner'])


def solve_owner_repo_names(path_or_owner, repo=None):
    if repo is not None:
        owner = path_or_owner
    else:
        owner = path_or_owner[:path_or_owner.find('/')]
        repo = path_or_owner[path_or_owner.find('/') + 1:]
    return owner, repo


def get_request(path):
    r = requests.get('https://api.github.com/' + path, headers=payload)
    return r.text, r.headers.get('X-RateLimit-Remaining'), r.headers





# update_repos()
fetch_github_info('expressjs/express')
