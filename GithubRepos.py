from operator import concat

from MongoConnection import MongoConnection
# from NPMFetcher import get_npm_repos
import json
from bson.objectid import ObjectId
import requests
import time
from datetime import datetime, timedelta
from GithubUsers import get_user, format_user_list
from JSON_utils import trim_json, JSONEncoder, parse
from Errors import NonGitRepoError, NoRepositoryFoundError, NonGithubRepoError, GithubAccessLimitReachedError
import string
import time

auth_token = 'token 7ef69b2368773c233c5f7d29039eadf9cb55c05c'
user_agent = 'Mozilla/5.0'
payload = {'Authorization': auth_token, 'User-Agent': user_agent}
repo_keys_to_keep = ['id', 'name', 'full_name', 'owner', 'description', 'homepage', 'stargazers_count', 'has_wiki'
    , 'watchers_count', 'forks_count', 'watchers', 'organization', 'network_count', 'subscribers_count']
user_keys_to_keep = ['id', 'contributions']

connection = MongoConnection()


def next_npm_project():
    collection = connection.get_collection('npm_repos')
    return collection.find_one({'updated': 'npm_json'}, sort=[('numeric_version', -1)])


def update_repos():
    connection = MongoConnection()
    npm_collection = connection.get_collection('npm_repos')
    total = npm_collection.find({'updated': 'npm_json'}).count()
    collection = connection.get_collection('github_repos')

    current_repo = next_npm_project()
    count = 0
    t0 = time.time()
    error = False
    while current_repo is not None:
        try:
            print('Analyzing project ', current_repo['id'])

            owner, repo = get_github_user_repo(current_repo)

            repo_info = fetch_github_info(owner, repo)

            count += 1
            t1 = time.time()
            print((count / total) * 100, end='')
            print('%')
            total_time = (t1 - t0)
            total_time = total_time * total / count
            total_time = timedelta(seconds=int(total_time))
            d = datetime(1, 1, 1) + total_time
            print("%d days %d hours %d minutes %d seconds left" % (d.day - 1, d.hour, d.minute, d.second))
            repo_info['_id'] = current_repo['_id']
            collection.insert(repo_info, check_keys=False)
            npm_collection.update_one({'_id': current_repo['_id']}, {"$set": {'updated': 'github_updated'}})
        except KeyboardInterrupt:
            break
        except GithubAccessLimitReachedError:
            print('Access limit reached')
            time.sleep(900)
            continue
        except NonGitRepoError:
            print('No git repo found')
            npm_collection.update_one({'_id': current_repo['_id']}, {"$set": {'updated': 'github_fail_non_git'}})
        except NoRepositoryFoundError:
            print('No repo found')
            npm_collection.update_one({'_id': current_repo['_id']}, {"$set": {'updated': 'github_fail_no_repo'}})
        except NonGithubRepoError:
            print('No github repo found')
            npm_collection.update_one({'_id': current_repo['_id']}, {"$set": {'updated': 'github_non_github'}})
        except requests.exceptions.ConnectionError:
            print('General error, sleeping for 60 secs')
            time.sleep(60)
            continue
        finally:
            current_repo = next_npm_project()


def get_github_user_repo(document):  # returns a tuple with user and repo
    document = parse(document)
    if isinstance(document, dict):
        if 'repository' in document:
            if 'url' in document['repository'] and 'type' in document['repository'] and\
                    'git' in document['repository']['type']:
                try:
                    url = document['repository']['url']
                    url = url[0: url.rfind('.git')]
                    repo = url[url.rfind('/') + 1:]
                    url = url[:url.rfind('/')]
                    user = url[url.rfind('/') + 1:]
                    if user == '' or repo == '' or user is None or repo is None \
                            or user[0] not in string.ascii_letters \
                            or len(([c for c in user if c not in (string.ascii_letters + string.digits + '-')]))>0\
                            or len(([c for c in repo if c not in (string.ascii_letters + string.digits + '-')]))>0:
                        raise NonGithubRepoError('This repository is not in a github format')
                    return user, repo
                except Exception:
                    raise NonGithubRepoError('This repository is not in a github format')
            else:
                raise NonGitRepoError('The repository is not a Git repository')
        else:
            if 'versions' in document:
                return get_github_user_repo(document['versions'])
    elif isinstance(document, list):
        for version in document:
            for keys in version:
                value = version[keys]
                if value is not None:
                    try:
                        return get_github_user_repo(value)
                    except NonGithubRepoError or NonGitRepoError or NoRepositoryFoundError:
                        continue
        raise NoRepositoryFoundError('No repository was found for this project')
    raise NoRepositoryFoundError('No repository was found for this project')


def fetch_github_info(path_or_owner, repo=None):
    try:
        owner, repo = solve_owner_repo_names(path_or_owner, repo)
        content, limit, headers = get_request('repos/' + owner + '/' + repo)
        document = trim_json(content, repo_keys_to_keep)
        user = get_user(document['owner'], False)
        document['owner'] = user['id']
        if 'organization' in document:
            organization = get_user(document['organization'], False)
            document['organization'] = organization['id']
        document['contributors'] = get_contributors(owner, repo)
        user_list = []
        for contributor in document['contributors']:
            user = {}
            for key in contributor:
                if key in user_keys_to_keep:
                    user[key] = contributor[key]
            user_list.append(user)
        del document['contributors']
        document['contributors'] = user_list
        return document
    except NoRepositoryFoundError:
        raise NoRepositoryFoundError
    except Exception as e:
        raise e


def get_contributors(path_or_owner, repo=None):
    owner, repo = solve_owner_repo_names(path_or_owner, repo)
    try:
        document, limit, headers = get_request('repos/' + owner + '/' + repo + '/contributors')
    except NoRepositoryFoundError:
        raise NoRepositoryFoundError
    document = format_user_list(document)
    return document


def solve_owner_repo_names(path_or_owner, repo=None):
    if repo is not None:
        owner = path_or_owner
    else:
        owner = path_or_owner[:path_or_owner.find('/')]
        repo = path_or_owner[path_or_owner.find('/') + 1:]
    return owner, repo


def get_request(path):
    r = requests.get('https://api.github.com/' + path, headers=payload)
    print(r.headers.get('X-RateLimit-Remaining'), end='\t')
    if '200' not in r.headers.get('status'):
        raise NoRepositoryFoundError
    if r.headers.get('X-RateLimit-Remaining') == 0:
        raise GithubAccessLimitReachedError('Github access limit reached')
    return r.text, r.headers.get('X-RateLimit-Remaining'), r.headers





update_repos()
#fetch_github_info('expressjs/express')
