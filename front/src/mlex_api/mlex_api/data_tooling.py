"""
A collection of tools/classes for managing data (file movement, train_test_splits, etc)
"""
import pathlib
import base64
import PIL.Image
import io
import sklearn
#import skimage
class DataTools():

    @classmethod
    def _create_directory(self, dir_name):
        folder=pathlib.Path(dir_name)
        folder_return=folder.mkdir(parents=True, exist_ok=True)
        return folder_return

    def _move_file(self, filepathfrom, filepathto):
        path_from=pathlib.Path(filepathfrom)
        path_to=pathlib.Path(filepathto)
        path_from.replace(path_to)

    @classmethod
    def _save_file(self, file_contents, file_path):
        '''
        file_contents, binary64 encoded str
        file_path, str/pathlib.Path
        
        Return: true if saved, false if errors
        '''  
        try:
            file_path = str(file_path)
            im_decode = base64.b64decode(file_contents)
            im_bytes = io.BytesIO(im_decode)
            im = PIL.Image.open(im_bytes)
            # add transforms to image
            im.save(file_path)
            return True
        except:
            return False

    @classmethod
    def _read_file_binary(self,file_path):
        image = open(file_path, 'rb')
        image_64_encode = base64.encodestring(image.read())
        return image_64_encode

    def save_test_train_split(self, list_of_files, list_of_filenames, root_dir_experiment):
        """
        Wrapped on sklearn test_train_split to organize files
        list_of_files, list bytes (base64)
        list_of_filenames, list str
        root_dir_experiment, str/pathlib.Path, where the test
        and train folders should be saved
        """
        for file_, fname in zip(list_of_files, list_of_names):

            _save_file(file, fname)
            _
        pass
        
class Classification():

    @staticmethod
    def create_labeled_directory_from_memory(
            binary_file_contents,
            binary_file_names,
            labeled_file_names
    ):

        pass

