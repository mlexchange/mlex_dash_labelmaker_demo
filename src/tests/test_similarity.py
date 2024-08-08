from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.query import Query


@pytest.fixture
def query():
    labels_dict = {}
    labels_list = []
    num_imgs_per_label = None
    return Query(
        num_imgs=400000,
        labels_dict=labels_dict,
        labels_list=labels_list,
        num_imgs_per_label=num_imgs_per_label,
    )


def test_similarity_search(query):
    model_path = "dummy_model_path.parquet"
    index_interest = 10
    indices = list(range(18))

    # Mock data
    unlabeled_indx = list(range(100000))
    data = np.random.rand(400000, 1000)
    df_model = pd.DataFrame(data)

    # Setup mocks
    with patch.object(
        query, "hide_labeled", return_value=unlabeled_indx
    ) as mock_hide_labeled, patch(
        "pandas.read_parquet", return_value=df_model
    ) as mock_read_parquet:
        result = query.similarity_search(model_path, index_interest, indices)
        # Assertions
        mock_hide_labeled.assert_called_once()
        mock_read_parquet.assert_called_once_with(model_path, engine="pyarrow")
        assert len(result) == len(indices)
