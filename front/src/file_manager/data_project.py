from typing import List

from file_manager.dataset.local_dataset import LocalDataset
from file_manager.dataset.tiled_dataset import TiledDataset


class DataProject:
    def __init__(self, data: List = []):
        self.data = data
        pass

    def init_from_dict(self, data: List):
        self.data = []
        for item in data:
            if item['type']=='tiled':
                self.data.append(TiledDataset(**item))
            else:
                self.data.append(LocalDataset(**item))
        
    @staticmethod
    def browse_data(data_type, browse_format, dir_path=None, tiled_uri=None):
        if data_type == 'tiled':
            uris = TiledDataset.browse_data(tiled_uri, browse_format, tiled_uris=[])
            data = [TiledDataset(uri=item) for item in uris]
        else:
            if browse_format=='*':
                uris = LocalDataset.filepaths_from_directory(dir_path)
            else:
                if browse_format == '**/*.jpg':
                    browse_format = ['**/*.jpg', '**/*.jpeg']
                elif browse_format == '**/*.tif':
                    browse_format = ['**/*.tif', '**/*.tiff']
                uris = LocalDataset.filepaths_from_directory(dir_path, browse_format)
            data = [LocalDataset(uri=str(item)) for item in uris]
        return data
    
    def get_dict(self):
        data_project_dict = [dataset.__dict__ for dataset in self.data]
        return data_project_dict
    
    def get_table_dict(self):
        data_table_dict = [{"uri": dataset.uri, "type": dataset.type} for dataset in self.data]
        return data_table_dict
    
