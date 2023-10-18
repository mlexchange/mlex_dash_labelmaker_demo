import os
import requests

from app_layout import MLEX_COMPUTE_URL


def get_trained_models_list(user, tab):
    '''
    This function queries the MLCoach or DataClinic results
    Args:
        user:               Username
        tab:                Tab option (MLCoach vs Data Clinic)
    Returns:
        trained_models:     List of options
    '''
    if tab == 'mlcoach':
        filename = '/results.parquet'
    else:
        filename = '/f_vectors.parquet'
    model_list = requests.get(f'{MLEX_COMPUTE_URL}/jobs?&user={user}&mlex_app={tab}').json()
    trained_models = []
    for model in model_list:
        if model['job_kwargs']['kwargs']['job_type'].split(' ')[0]=='prediction_model':
            if os.path.exists(model['job_kwargs']['cmd'].split(' ')[7]+filename):  # check if the file exists
                if model['description']:
                    trained_models.append({'label': model['description'],
                                           'value': model['job_kwargs']['cmd'].split(' ')[7]+filename})
                else:
                    trained_models.append({'label': model['job_kwargs']['kwargs']['job_type'],
                                           'value': model['job_kwargs']['cmd'].split(' ')[7]+filename})
    trained_models.reverse()
    return trained_models