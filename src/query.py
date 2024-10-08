import logging
from itertools import chain

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

from src.labels import Labels

logging.basicConfig(encoding="utf-8", level=logging.INFO)


class Query(Labels):
    def __init__(self, num_imgs, **kwargs):
        super().__init__(**kwargs)
        self.num_imgs = num_imgs
        pass

    def sort_labeled(self, dataset_order=None):
        labeled = {}
        for key, label in self.labels_dict.items():
            if len(label) > 0:
                labeled.setdefault(label[0], []).append(int(key))
        labeled_indices = list(chain(*labeled.values()))
        if dataset_order is not None:
            dataset_order = set(dataset_order)
            labeled_indices = set(labeled_indices) & dataset_order
            unlabeled_indices = list(dataset_order - labeled_indices)
            labeled_indices = list(labeled_indices)
        else:
            unlabeled_indices = list(set(range(self.num_imgs)) - set(labeled_indices))
        return labeled_indices + unlabeled_indices

    def hide_labeled(self):
        labeled_indices = self._get_labeled_indices()
        unlabeled_indices = set(range(self.num_imgs)) - set(labeled_indices)
        return list(unlabeled_indices)

    def similarity_search(self, model_path, index_interest):
        unlabeled_indx = self.hide_labeled()  # Get list of indexes of unlabeled images
        df_model = pd.read_parquet(model_path, engine="pyarrow")
        dist = cdist(
            df_model.iloc[index_interest, :].values[np.newaxis, :],
            df_model.loc[unlabeled_indx].values,
            "cosine",
        ).squeeze()
        ordered_indx = np.array(unlabeled_indx)[np.argsort(dist)]
        return ordered_indx
