from itertools import chain
import logging

import numpy as np
import pandas as pd

from labels import Labels
# import pycbir


logging.basicConfig(encoding='utf-8', level=logging.INFO)


class Query(Labels):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass
        
    def sort_labels(self):
        labeled = {}
        for indx, label in enumerate(self.labels_dict.values()):
            if len(label)>0:
                labeled.setdefault(label[0], []).append(indx)
        labeled_filenames = list(chain(*labeled.values()))
        unlabeled_filenames = list(set(range(len(self.labels_dict)))-set(labeled_filenames))
        return labeled_filenames + unlabeled_filenames
    
    def hide_labeled(self):
        list_values = list(self.labels_dict.values())
        indx = [i for i, x in enumerate(list_values) if x == []]
        return indx
    
    def similarity_search(self, model_path, filename):
        df_clinic = pd.read_parquet(model_path)
        row_dataframe = df_clinic.loc[[filename]]
        image_order = [int(order) for order in row_dataframe.values.tolist()[0]]
        return image_order