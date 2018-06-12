from urllib.request import urlretrieve

urlretrieve("https://skimdb.npmjs.com/registry/_design/scratch/_view/byField", "npm_repos.json")
