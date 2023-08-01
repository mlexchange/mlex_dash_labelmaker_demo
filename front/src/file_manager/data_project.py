from datetime import datetime
import json
from typing import List

import requests

from file_manager.dataset.local_dataset import LocalDataset
from file_manager.dataset.tiled_dataset import TiledDataset


class DataProject:
    def __init__(self, data: List = []):
        '''
        Definition of a DataProject
        Args:
            data:       List of data sets within the project
        '''
        self.data = data
        pass

    def init_from_dict(self, data: List):
        '''
        Initialize the object from a dictionary
        '''
        self.data = []
        for item in data:
            if item['type']=='tiled':
                self.data.append(TiledDataset(**item))
            else:
                self.data.append(LocalDataset(**item))
        
    @staticmethod
    def browse_data(data_type, browse_format, dir_path=None, tiled_uri=None):
        '''
        Browse data according to browse format and data type
        Args:
            data_type:          Tiled or local
            browse_format:      File format to retrieve during this process
            dir_path:           Directory path if data_type is local
            tiled_uri:          Tiled URI if data_type is tiled
        Returns:
            data:               Retrieve Dataset according to data_type and browse format
        '''
        if data_type == 'tiled':
            uris = TiledDataset.browse_data(tiled_uri, browse_format, tiled_uris=[])
            data = [TiledDataset(uri=item) for item in uris]
        else:
            if browse_format=='*':
                uris = LocalDataset.filepaths_from_directory(dir_path)
            else:
                if browse_format == '**/*.jpg':             # Add variations of the file extensions
                    browse_format = ['**/*.jpg', '**/*.jpeg']
                elif browse_format == '**/*.tif':
                    browse_format = ['**/*.tif', '**/*.tiff']
                # Recursively call the method if a subdirectory is encountered
                uris = LocalDataset.filepaths_from_directory(dir_path, browse_format)
            data = [LocalDataset(uri=str(item)) for item in uris]
        return data
    
    def get_dict(self):
        '''
        Retrieve the dictionary from the object
        '''
        data_project_dict = [dataset.__dict__ for dataset in self.data]
        return data_project_dict
    
    def get_table_dict(self):
        '''
        Retrieve a curated dictionary for the dash table without tags due to imcompatibility with 
        dash table and a list of items in a cell
        '''
        data_table_dict = [{"uri": dataset.uri, "type": dataset.type} for dataset in self.data]
        return data_table_dict
    
    def add_to_splash(self, splash_uri):
        '''
        Add list of data sets to splash-ml
        Args:
            splash_uri:         URI to splash-ml service
            dataset_list:       List of data sets to post or patch
        Return:
            event_uid:          Tagging event uid assigned by splash-ml
        '''
        event_uid = requests.post(f'{splash_uri}/events',               # Post new tagging event
                                  json={'tagger_id': 'labelmaker',
                                        'run_time': str(datetime.utcnow())}).json()['uid']
        for dataset in self.data:
            dataset._add_event_id(event_uid)
            # Check if the data set exists in splash-ml
            splash_dataset = requests.get(f'{splash_uri}/datasets', 
                                          json={'uris': [dataset.uri]}).json()
            if len(splash_dataset)>0:
                # If it exists, patch it
                splash_dataset_uid = splash_dataset[0]['uid']
                requests.patch(f'{splash_uri}/datasets/{splash_dataset_uid}/tags',
                               json={'add_tags': dataset.tags})
            else:
                # If it doesn't exist, post it
                dataset_dict=dataset.__dict__
                requests.post(f'{splash_uri}/datasets', json=dataset_dict)
        return event_uid
    
