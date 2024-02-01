from itertools import chain
import logging

import numpy as np
import pandas as pd

from labels import Labels
from scipy.spatial.distance import cosine


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
        unlabeled_indx = self.hide_labeled()            # Get list of indexes of unlabeled images
        df_model = pd.read_parquet(model_path, engine='pyarrow') 
        f_vec = np.array(df_model)[unlabeled_indx,:]   # Get feature vectors of unlabeled images
        f_vec_int = np.array(df_model.loc[filename])   # Identify feature vector of interest
        num_data_sets = f_vec.shape[0]
        dist = np.zeros(num_data_sets)
        for ii in range(num_data_sets):                 # Calculate distance vector
            dist[ii] = cosine(f_vec_int, f_vec[ii])
        return np.array(unlabeled_indx)[np.argsort(dist)]