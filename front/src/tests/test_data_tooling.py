import base64
import sys
import pathlib
sys.path.append('..')
sys.path.append('../../')
from mlex_api.mlex_api.data_tooling import DataTools as dt


def test_data_save():
    # get binary file first
    filebin = dt._read_file_binary(file_path='./arc00015.jpg')
    print(type(filebin))
    assert type(filebin) == bytes


def test_save_file():
    filebin = dt._read_file_binary(file_path='./arc00015.jpg')
    output_names = ['./test_arc00015.png', './test_arc00015.tiff']
    # delete test files if exist
    for name in output_names:
        pathlib.Path(name).unlink(missing_ok=True)

    image = dt._save_file(filebin, './test_arc00015.png')
    image = dt._save_file(filebin, './test_arc00015.tiff')
    print(type(image))




if __name__ == '__main__':
    test_data_save()
    test_save_file()
