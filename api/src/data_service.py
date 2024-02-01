from uuid import uuid4

from src.model import Dataset

class DataService():
    def __init__(self, client, db_name=None):
        if db_name is None:
            db_name = 'data_manager'
        self._db = client[db_name]
        self._collection_project = self._db.project
        self._create_indexes()
    
    def get_dataset(self, user_id=None) -> Dataset:
        
        if user_id:
            item = self._collection_project.find_one({"user_id": user_id}) #, {'_id': 0})
        else:
            item = self._collection_project.find_one()
        self._clean_mongo_ids(item)
        dataset = Dataset.parse_obj(item)
        return dataset
    
    def add_dataset(self, dataset: Dataset) -> str:
        # check if dataset exists
        current_dataset = self._collection_project.find_one({'user_id': dataset.user_id})
        if current_dataset:
            dataset.uid = current_dataset['uid']
            dataset_dict = dataset.dict()
            self._collection_project.update_one({'uid': current_dataset['uid']}, 
                                                {'$set': dataset_dict}, 
                                                upsert=False)
        else:
            dataset.uid = str(uuid4())
            dataset_dict = dataset.dict()
            self._collection_project.insert_one(dataset_dict)
        return dataset.uid
    
    def _create_indexes(self):
        self._collection_project.create_index([('uid', 1)], unique=True)
        self._collection_project.create_index([('user_id', 1)])

    @staticmethod
    def _clean_mongo_ids(data):
        if '_id' in data:
            # Remove the internal mongo id before schema validation
            del data['_id']