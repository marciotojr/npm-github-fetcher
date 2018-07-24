from urllib.request import urlretrieve
from pathlib import Path


file_path = "npm_repos.json"


def change_file_path(new_path):
    global file_path
    file_path = new_path


def get_npm_repos():
    if not Path(file_path).is_file():
        urlretrieve("https://skimdb.npmjs.com/registry/_design/scratch/_view/byField", file_path)
    return open(file_path, 'r')
