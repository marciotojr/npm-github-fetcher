from pymongo import MongoClient
import json, urllib.request
from bson.objectid import ObjectId
import mysql.connector

user_removable = ('git@github.com:', )


def get_mysql_cursor():
    db = mysql.connector.connection.MySQLConnection(user='root', password='',
                                                     host='localhost',
                                                     database='npm-github-fetcher')
    return db, db.cursor()


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def create_document(repo_id, obj):
    obj['id'] = obj['_id']
    repo_id = str(repo_id)
    for i in range(12-len(repo_id)):
        repo_id = '0'+repo_id

    for versions in obj['versions']:
        version = obj['versions'][versions]
        for key in version.keys():
            new_key = key.replace("_", "")
            if new_key != key:
                obj['versions'][versions][new_key] = obj['versions'][versions][key]
                del obj['versions'][versions][key]

    del obj['_id']
    obj['_id'] = ObjectId(str.encode(repo_id))
    JSONEncoder().encode(obj)
    return obj


def get_npm_repo_info(serial_id, repo_id):

    client = MongoClient('localhost', 27017)
    db = client['social_seco']
    collection = db['npm-repos']

    parsed = create_document(serial_id, fetch_repo_info(repo_id))
    collection.insert(parsed, check_keys=False)


def fetch_repo_info(repo_id):
    with urllib.request.urlopen("https://registry.npmjs.org/" + repo_id) as url:
        data = json.loads(url.read().decode())
        print(data)


def get_config_variable(key):
    client = MongoClient('localhost', 27017)
    db = client['social_seco']
    collection = db['config-variables']
    variable_value = collection.find_one({'key': key})
    return int(variable_value['value'])


def check_username(username, action):
    if username[0] == '-':
        action['passed'] = False
    else:
        for character in username:
            if not (str.isupper(character) or str.islower(character) or str.isnumeric(character) or character == '-'):
                action['passed'] = False
                break


def check_repo_name(repo_name, action):
    for character in repo_name:
        if not (str.isupper(character) or str.islower(character) or str.isnumeric(character) or character in ['/', '_',
                                                                                                              '-', '.',
                                                                                                              '#']):
            action['passed'] = False
            break


def clean():
    # TODO make it a while
    if True:
        count = 0

        total = 0

        dbm, cursor = get_mysql_cursor()

        query = 'SELECT COUNT(*) FROM npmprojects WHERE repo NOT LIKE ""'
        cursor.execute(query)

        for lines in cursor:
            total = int(lines[0])

        dbm, cursor = get_mysql_cursor()

        query = 'SELECT id, repo FROM npmprojects WHERE repo NOT LIKE ""'
        cursor.execute(query)

        for queried_data in cursor:

            action = {'delete': False, 'passed': True, 'change': False}

            repo_data = queried_data[1].split('/')

            if len(repo_data) != 2:
                action['passed'] = False
                if len(repo_data) < 2:
                    delete = True
            else:
                repo_name = repo_data[1]
                user_name = repo_data[0]

                if len(repo_data[0]) == 0 or len(repo_data[1]) == 0:
                    action['passed'] = False
                    action['delete'] = True
                else:

                    if repo_data[0][0] == '-':
                        action['passed'] = False
                    else:
                        for item in user_removable:
                            if repo_data[0] == item:
                                action['change'] = True
                                repo_name = repo_name.replace(item, '')

                        for character in repo_data[0]:
                            if not (str.isupper(character) or str.islower(character) or str.isnumeric(character) or character == '-'):
                                action['passed'] = False
                                break

            db, update_cursor = get_mysql_cursor()

            if delete:
                query = 'UPDATE npmprojects SET repo="" WHERE id = %s'

                data = [queried_data[0]]

                update_cursor.execute(query, data)

                update_cursor.close()

                db.commit()

            count += 1
            percentage = (count / total) * 100

            if action['passed']:
                color = '\033[92m'
            else:
                color = '\033[91m'
            if action['delete']:
                color = '\033[93m'
            if not action['passed'] or action['delete']:
                print(color, "%.2f" % percentage, end='')
                print("%\t", queried_data[1])

        db.commit()

        # disconnect from server
        db.close()




#get_npm_repo_info(100673, 'express')
clean()