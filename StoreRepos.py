import json
import mysql.connector

valid = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.']


def get_repo(repo):
    repo = repo[:repo.rfind(',')]
    try:
        data = json.loads(repo)
        return [data['id'], data['value']['_nodeVersion']]
    except:
        return None


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

                    q = "INSERT INTO npmprojects (id, name, version) VALUES (%s,%s,%s)"
                    data = [i, repo[0], repo[1]]

                    # execute SQL query using execute() method.
                    cursor.execute(q, data)

                    print('Id: \t ' + str(i) + '\t\t\t' + 'Name:\t' + repo[0] + '\t\t\t' + repo[1])

                    i += 1

            finally:
                pass
        db.commit()

        # disconnect from server
        db.close()


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



read_repos()
