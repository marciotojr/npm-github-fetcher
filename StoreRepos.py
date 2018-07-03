import json
import mysql.connector

valid = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.']

def get_mysql_cursor():
    db = mysql.connector.connection.MySQLConnection(user='root', password='',
                                                     host='localhost',
                                                     database='npm-github-fetcher')
    return db, db.cursor()

def get_repo(repo):
    repo = repo[:repo.rfind(',')]
    try:
        data = json.loads(repo)
        url = str(data['value']['repository']['url'])
        if 'github.com' in url:
            if '.git' in url:
                url = url.replace('.git', '')
            if url[-2:-1] == '/':
                url = url.replace('/', '')
            lpos = url.rfind('/', 0, url.rfind('/'))
            url = url[lpos+1:]
            arr = [data['id'], data['value']['_nodeVersion'], url]
            return arr
    except:
        return None


def read_repos_bak(file_path='npm_repos.json'):
    with open(file_path) as file:
        i = 1
        db = mysql.connector.connection.MySQLConnection(user='root', password='',
                              host='localhost',
                              database='npm-github-fetcher')
        for line in file:
            try:
                repo = get_repo(line)
                #print(repo)
                if repo is not None:
                #if False:
                    if i % 30000 == 0:
                        db.commit()

                        # disconnect from server
                        db.close()

                        # Open database connection
                        db = mysql.connector.connection.MySQLConnection(user='root', password='',
                                  host='localhost',
                                  database='npm-github-fetcher')

                    # prepare a cursor object using cursor() method
                    cursor = db.cursor()

                    q = "INSERT INTO npmprojects (id, name, version, repo) VALUES (%s,%s,%s,%s)"
                    data = [i, repo[0], repo[1], repo[2]]

                    # execute SQL query using execute() method.
                    cursor.execute(q, data)

                    print('Id: \t ' + str(i) + '\t\t\t' + 'Name:\t' + repo[0] + '\t\t\t' + repo[1])

                    i += 1
            finally:
                pass
        db.commit()

        # disconnect from server
        db.close()
        print(i)


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


def read_repos(file_path='npm_repos.json'):
    with open(file_path) as file:
        i = 1
        db = mysql.connector.connection.MySQLConnection(user='root', password='',
                              host='localhost',
                              database='npm-github-fetcher')
        for line in file:
            try:
                repo = get_repo(line)
                #print(repo)
                if repo is not None:
                #if False:
                    if i % 30000 == 0:
                        db.commit()

                        # disconnect from server
                        db.close()

                        # Open database connection
                        db = mysql.connector.connection.MySQLConnection(user='root', password='',
                                  host='localhost',
                                  database='npm-github-fetcher')

                    # prepare a cursor object using cursor() method
                    cursor = db.cursor()

                    repository = repo[2]

                    q = "INSERT INTO npmprojects (id, name, version, repo) VALUES (%s,%s,%s,%s)"
                    data = [i, repo[0], repo[1], repo[2]]

                    # execute SQL query using execute() method.
                    cursor.execute(q, data)

                    print('Id: \t ' + str(i) + '\t\t\t' + 'Name:\t' + repo[0] + '\t\t\t' + repo[1])

                    i += 1
            finally:
                pass
        db.commit()

        # disconnect from server
        db.close()
        print(i)


def prioritize():
    dbm, cursor = get_mysql_cursor()

    query = 'SELECT id FROM npmprojects ORDER BY version DESC'
    cursor.execute(query)

    i=0

    print("\n\n---------------------\n Prioritizing \n ")

    db, loop_cursor = get_mysql_cursor()

    for queried_data in cursor:

        print(i)
        data = [i, queried_data[0]]
        query = 'UPDATE npmprojects SET priorization_order=%s WHERE id=%s'
        loop_cursor.execute(query, data)

        if i % 3000 == 0:
            db.commit()

        i += 1
    db.commit()
    db.close()
    dbm.close()


#read_repos()
prioritize()
