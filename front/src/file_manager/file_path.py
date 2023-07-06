import os 
import pathlib
# import copy
import glob
from functools import reduce
from tiled.client import from_uri
from tiled.client.array import ArrayClient
from tiled.client.cache import Cache as TiledCache
from typing import List


FORMATS = ['.png', '.jpg', '.jpeg', '.tif', '.tiff']


class FilePath:
    def __init__(self, file_path, file_type, file_location='local'):
        self.file_path = file_path
        self.file_type = file_type
        self.file_location = file_location
        pass


class ListFilePaths:
    def __init__(self, list_filepaths: List[FilePath] = []):
        self.filepaths = list_filepaths
        self.tiled_client = None
        pass

    def move_dir(self, source, destination):
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
            self._move_a_file(file_source, destination)
        for dirname in list_dirs:
            dir_source = dir_path + '/' + dirname
            self.move_dir(dir_source, destination)
        pass

    def filenames_from_dir(self, dir_path, formats=FORMATS, sort=False):
        '''
        Args:
            dir_path, str:            full path of a directory
            formats, list:            supported formats, e.g., ['tiff', 'tif', 'jpg', 'jpeg', 'png']
            sort, boolean:            whether ordered or not, default False 
        Returns:
            List[str]:      a list of filenames (does not contain folders) 
        '''
        patterns = ['**/*.'+t for t in formats]
        return self._paths_from_dir(dir_path, patterns, sort)

    def paths_from_dir(self, dir_path, form, sort=False):
        '''
        Args:
            directory, str:     full path of a directory
            form, str:          A supported format in ['dir', '*', '*.png', '*.jpg, *.jpeg', 
                                '*.tif,*tiff', '*.txt', '*.csv']
            sort, boolean:      whether ordered or not, default False 
        Return:
            List[FilePath]:     List of absolute file paths (filtered by file formats) 
                                inside a directory.
        '''
        paths = []
        if form == 'dir' or form == '*':
            directories = self._paths_from_dir(dir_path,['**/'], sort) # include the root dir path
            for directory in directories[1:]:
                paths.append(FilePath(file_path=directory[:-1], file_type='dir'))
            if form == '*':
                patterns = ['**/*.'+t for t in FORMATS]
                fnames = self._paths_from_dir(dir_path, patterns, sort)
                for fname in fnames:
                    paths.append(FilePath(file_path=fname, file_type='file'))
        else:
            formats = form.split(',')
            patterns = ['**/*.'+e[2:] for e in formats]
            fnames = self._paths_from_dir(dir_path, patterns, sort)
            for fname in fnames:
                paths.append(FilePath(file_path=fname, file_type='file'))
        return ListFilePaths(paths)
    
    def paths_from_tiled(self, tiled_uri):
        '''
        '''
        self.tiled_client = from_uri(tiled_uri, cache=TiledCache.on_disk('data/cache'))
        tiled_nodes = list(self.tiled_client)
        filepaths = []
        for node in tiled_nodes:
            mod_uri = f'{tiled_uri}/api/v1/node/full/{node}?format=jpeg'
            filepaths.append(FilePath(file_path=mod_uri, file_type='uri', file_location='tiled'))
        return filepaths
    
    @staticmethod
    def docker_to_local_path(paths, docker_home, local_home):
        '''
        Args:
            paths:              List of FilePaths or a string
            docker_home, str:   full path of home dir (ends with '/') in docker environment
            local_home, str:    full path of home dir (ends with '/') mounted in local machine
            path_type:
                list-dict, default:  a list of dictionary (docker paths), e.g., [{'file_path': 'docker_path1'},{...}]
                str:                a single file path string
        Return: 
            str or List[dict]:   replace docker path with local path, the same data structure as paths
        '''
        if type(paths) == str:
            if not paths.startswith(local_home):
                files = local_home + paths.split(docker_home)[-1]
            else:
                files = paths
        else:
            files = []
            for file in paths.filepaths:
                if not file.file_path.startswith(local_home):
                    file.file_path = local_home + file.file_path.split(docker_home)[-1]
                files.append(file.__dict__)
            # first_path = paths.filepaths[0]
            # files = []
            # if first_path.file_type == 'dir':     # files = copy.deepcopy(paths)
            #     for file in paths:
            #         if not file.file_path.startswith(local_home):
            #             file.file_path = local_home + file.file_path.split(docker_home)[-1]
        return files

    @staticmethod
    def local_to_docker_path(paths, docker_home, local_home):
        '''
        Args:
            paths:             List of paths or a string 
            docker_home, str:  full path of home dir (ends with '/') in docker environment
            local_home, str:   full path of home dir (ends with '/') mounted in local machine
            path_type:
                list:          a list of path string
                str:           single path string 
        Return: 
            list or str:    replace local path with docker path, the same data structure as paths
        '''
        if type(paths) == 'str':
            if not paths.startswith(docker_home):
                files = docker_home + paths.split(local_home)[-1]
            else:
                files = paths
        else:
            files = []
            for i in range(len(paths)):
                if not paths[i].startswith(docker_home):
                    files.append(docker_home + paths[i].split(local_home)[-1])
                else:
                    files.append(paths[i])
        return files

    @staticmethod
    def _paths_from_dir(dir_path, patterns=['**/*'], sort=False):
        '''
        '''
        paths = list(reduce(lambda list1, list2: list1 + list2, \
                            (glob.glob(str(dir_path)+'/'+t, recursive=True) for t in patterns)))
        if sort:
            paths.sort()
        return paths
    
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
    def filepaths_from_directory(directory, pattern='**/*', sort=False):
        if sort:
            return sorted(pathlib.Path(directory).glob(pattern))
        else:
            return pathlib.Path(directory).glob(pattern)
