import os

import requests

from src.app_layout import MLEX_COMPUTE_URL


def get_trained_models_list(user, app, similarity=True):
    """
    This function queries the MLCoach or DataClinic results
    Args:
        user:               Username
        app:                Tab option (MLCoach vs Data Clinic)
        similarity:         [Bool] Retrieve f_vec vs probabilities
    Returns:
        trained_models:     List of options
    """
    if similarity:
        filename = "/f_vectors.parquet"
    else:
        filename = "/results.parquet"
    model_list = requests.get(
        f"{MLEX_COMPUTE_URL}/jobs?&user={user}&mlex_app={app}"
    ).json()
    trained_models = []
    for model in model_list:
        if model["job_kwargs"]["kwargs"]["job_type"] == "prediction_model":
            cmd = model["job_kwargs"]["cmd"].split(" ")
            indx = cmd.index("-o")
            out_path = cmd[indx + 1]
            if os.path.exists(out_path + filename):  # check if the file exists
                if model["description"]:
                    trained_models.append(
                        {
                            "label": app + ": " + model["description"],
                            "value": out_path + filename,
                        }
                    )
                else:
                    trained_models.append(
                        {
                            "label": app
                            + ": "
                            + model["job_kwargs"]["kwargs"]["job_type"],
                            "value": out_path + filename,
                        }
                    )
    trained_models.reverse()
    return trained_models
