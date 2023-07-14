import base64, io
from functools import reduce

import glob
import os 
import pathlib
from PIL import Image

from file_manager.dataset.dataset import Dataset


FORMATS = ['**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.tif', '**/*.tiff']
NOT_ALLOWED_FORMATS = ['**/__pycache__/**', '**/.*']


class LocalDataset(Dataset):
    def __init__(self, uri, type='local', tags=[]):
        super().__init__(uri, type, tags)
        pass

    def read_data(self):
        filename = self.uri
        img = Image.open(filename)
        img = img.resize((300, 300))
        rawBytes = io.BytesIO()
        img.save(rawBytes, "JPEG")
        rawBytes.seek(0)        # return to the start of the file
        img = base64.b64encode(rawBytes.read())
        file_ext = filename[filename.find('.')+1:]
        return 'data:image/'+file_ext+';base64,'+img.decode("utf-8"), self.uri #.split('/')[-1]

    @staticmethod
    def move_dir(source, destination):
        '''
        Args:
            source, str:          full path of source directory
            destination, str:     full path of destination directory 
        '''
        dir_path, list_dirs, filenames = next(os.walk(source))
        original_dir_name = dir_path.split('/')[-1]
        destination = destination + '/' + original_dir_name
        pathlib.Path(destination).mkdir(parents=True, exist_ok=True)
        for filename in filenames:
            file_source = dir_path + '/' + filename  
            LocalDataset._move_a_file(file_source, destination)
        for dirname in list_dirs:
            dir_source = dir_path + '/' + dirname
            LocalDataset.move_dir(dir_source, destination)
        pass
    
    @staticmethod
    def _move_a_file(source, destination):
        '''
        Args:
            source, str:          full path of a file from source directory
            destination, str:     full path of destination directory 
        '''
        pathlib.Path(destination).mkdir(parents=True, exist_ok=True)
        filename = source.split('/')[-1]
        new_destination = destination + '/' + filename
        os.rename(source, new_destination)
        pass
    
    @staticmethod
    def filepaths_from_directory(directory, formats=FORMATS, sort=True):
        if type(formats) == str:
            formats = [formats]
        paths = list(reduce(lambda list1, list2: list1 + list2, \
                            (glob.glob(str(directory)+'/'+t, recursive=True) for t in formats)))
        not_allowed_paths = list(reduce(lambda list1, list2: list1 + list2, \
                            (glob.glob(str(directory)+'/'+t, recursive=True) for t in NOT_ALLOWED_FORMATS)))
        paths = list(set(paths) - set(not_allowed_paths))
        if sort:
            paths.sort()
        return paths
