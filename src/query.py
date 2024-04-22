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

    def sort_labels(self):
        labeled = {}
        for indx, label in enumerate(self.labels_dict.values()):
            if len(label) > 0:
                labeled.setdefault(label[0], []).append(indx)
        labeled_filenames = list(chain(*labeled.values()))
        unlabeled_filenames = list(
            set(range(len(self.labels_dict))) - set(labeled_filenames)
        )
        return labeled_filenames + unlabeled_filenames

    def hide_labeled(self):
        labeled_indices = [int(k) for k, v in self.labels_dict.items() if v != []]
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
