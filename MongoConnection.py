from pymongo import MongoClient

class MongoConnection:

    def __init__(self, host='localhost', port=27017, db='social_seco'):
        self.client = MongoClient(host, port)
        self.db = self.client[db]

    def get_collection(self, collection):
        return self.db[collection]

    def get_db(self):
        return self.db
