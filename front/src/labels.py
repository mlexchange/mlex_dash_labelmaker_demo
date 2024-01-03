import os, shutil, itertools, logging, tempfile
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import requests

from app_layout import SPLASH_URL


logging.basicConfig(encoding='utf-8', level=logging.INFO)


class Labels:
    def __init__(self,
                 labels_dict,
                 labels_list,
                 num_imgs_per_label=None
                 ) -> None:
        self.labels_dict = labels_dict
        self.labels_list = labels_list
        if num_imgs_per_label is None:
            self.num_imgs_per_label = self.get_num_imgs_per_label()
        else:
            self.num_imgs_per_label = num_imgs_per_label
        pass
    
    def init_labels(self, filenames=None, labels_list=None):
        '''
        Initializes the labels dictionary with empty lists for each filename
        Args:
            filenames:      List of filenames within the data set
            labels_list:    List of current available labels
        '''
        if labels_list:
            self.labels_list = labels_list
        if filenames is None:
            filenames = self.labels_dict.keys()
        self.labels_dict = {fname: [] for fname in filenames}
        self.num_imgs_per_label = self.get_num_imgs_per_label()
        pass

    def get_num_imgs_per_label(self):
        '''
        Calculates the labeling progress in terms of number of labeled images
        Returns:
            num_imgs_per_label:     Number of labeled images per label
        '''
        assigned_labels = list(itertools.chain.from_iterable(self.labels_dict.values()))
        num_imgs_per_label = {}
        for label in self.labels_list:
            num_imgs_per_label[label] = assigned_labels.count(label)
        return num_imgs_per_label
    
    def update_labels_list(self, add_label=None, remove_label=None, rename_label=None, new_name=None):
        '''
        Updates the labels list
        Args:
            add_label:          New label to be added to the list
            remove_label:       Label to be removed from the list and dictionary (if this label has
                                been used to label at least 1 image within the data set)
        '''
        if add_label is not None:
            self.labels_list.append(add_label)
            self.num_imgs_per_label[add_label] = 0
        elif remove_label is not None:
            self.labels_list.remove(remove_label)
            self.labels_dict = {key: [val for val in values if val!=remove_label] \
                                for key, values in self.labels_dict.items()}
            self.num_imgs_per_label.pop(remove_label)
        elif rename_label is not None and new_name is not None:
            mod_indx = self.labels_list.index(rename_label)
            self.labels_list[mod_indx] = new_name
            new_num_imgs_per_label = {}
            for label in self.labels_list:
                new_num_imgs_per_label[label] = self.num_imgs_per_label[label] if label!=new_name \
                                                else self.num_imgs_per_label[rename_label]
            self.num_imgs_per_label = new_num_imgs_per_label
            value_mapping = {rename_label: new_name}
            self.labels_dict = {key: [value_mapping.get(value, value) for value in values] for 
                                key, values in self.labels_dict.items()}
        pass
    
    def assign_labels(self, label, filenames_to_label, overwrite=True):
        '''
        Assign labels in dictionary with or without overwriting existing labels
        Args:
            label:                  Label to be assigned
            filenames_to_label:     List of filenames to be labeled
            overwrite:              If True, the new label will overwrite any existing label in the
                                    dictionary, ow the label is not overwritten and the new label is
                                    ignored when the image is already labeled
        '''
        if not overwrite:
            filenames = list(self.labels_dict.keys())
            labeled_filenames = [key for key, value in self.labels_dict.items() if bool(value)]
            filenames_to_label = list((set(filenames) - set(labeled_filenames))\
                                      .intersection(filenames_to_label))
        for filename in filenames_to_label:
            current_labels = self.labels_dict[filename]
            if len(current_labels)>0:
                self.num_imgs_per_label[current_labels[0]] -= 1
                if label is None:
                    self.labels_dict[filename] = []
            if label is not None:
                self.labels_dict[filename] = [label]
                self.num_imgs_per_label[label] += 1
        pass

    def probability_labeling(self, probability_model, probability_label, threshold):
        '''
        Labeling process through probability-based trained model. This process will not overwrite
        existing labels in the dictionary
        Args:
            probability_model:      Probability-based model outcome to be used for labeling
            probability_label:      Label to be assigned across the data set
            threshold:              Probability threshold to assign labels
        '''
        df_prob = pd.read_parquet(probability_model)
        probability_filenames = df_prob.index[df_prob[probability_label]>threshold/100].tolist()
        self.assign_labels(probability_label, probability_filenames, overwrite=False)
        pass

    def manual_labeling(self, label, num_clicks, filenames):
        '''
        Manual labeling process where highlighted images (odd number of clicks) are labeled
        Args:
            label:          Label to be assigned
            num_clicks:     List of number of clicks per image
            filenames:      List of filenames corresponding to the images in the data set 
        '''
        filenames_to_label = []
        for clicks, filename in zip(num_clicks, filenames):
            if clicks is not None:
                if clicks % 2 == 1:
                    filenames_to_label.append(filename)
        self.assign_labels(label, filenames_to_label)
        pass

    def _get_splash_dataset(self, project_id):
        '''
        Retrieve the current data set of interest from splash-ml with their labels
        Args:
            project_id:     Data project_id
        '''
        uri_list = list(self.labels_dict.keys())
        url = f'{SPLASH_URL}/datasets/search'
        params = {"page[offset]": 0, "page[limit]": len(uri_list)}
        data = {"uris": uri_list, "project": project_id}
        status = requests.post(url, params=params, json=data)
        if status.status_code != 200:
            logging.error(f'Data set was not retrieved from splash-ml due to {status.status_code}: \
                          {status.json()}')
        return status.json()

    def load_splash_labels(self, project_id, event_id):
        '''
        Query labels from splash-ml
        Args:
            project_id:     Data project_id
            event_id:      [str] Event id
        '''
        datasets = self._get_splash_dataset(project_id)
        self.init_labels()          # resets dict and label before loading data
        for dataset in datasets:
            for tag in dataset['tags']:
                if tag["event_id"] == event_id:
                    label = tag['name']
                    if label not in self.labels_list:
                        self.update_labels_list(add_label=label)
                    self.assign_labels(label, [dataset['uri']])
        pass

    def save_to_splash(self, tagger_id, datasets, project_id):
        '''
        Save labels to splash-ml.
        Args:
            tagger_id:      [str] Tagger id
            datasets:       [list of dict] Data Project
            project_id:     Data project_id
        Returns:
            Request status
        '''
        # Post new tagging event
        event_status = requests.post(f'{SPLASH_URL}/events', 
                               json={"tagger_id": tagger_id, 
                                     "run_time": str(datetime.utcnow())})
        new_event_id = event_status.json()["uid"]
        uri_list = list(map(lambda d: d['uri'], datasets))
        splash_datasets = requests.post(f'{SPLASH_URL}/datasets/search',
                                        params = {"page[offset]": 0, "page[limit]": len(uri_list)},
                                        json={'project': project_id, 'uris': uri_list}).json()
        splash_uris = [d['uri'] for d in splash_datasets]
        status = ''
        for filename, label in zip(self.labels_dict.keys(), self.labels_dict.values()):
            if len(label)>0:
                label = label[0]                      # 1 label per image
                if filename in splash_uris:
                    indx = splash_uris.index(filename)
                    dataset_uid = splash_datasets[indx]['uid']
                    tag = {'name': str(label), 'event_id': new_event_id}
                    data = {'add_tags': [tag]}
                    response = requests.patch(f'{SPLASH_URL}/datasets/{dataset_uid}/tags',
                                              json=data)
                else:
                    indx = uri_list.index(filename)
                    new_dataset = datasets[indx]
                    new_dataset = {key: value for key, value in new_dataset.items() if key in {'uri', 'type'}}
                    new_dataset['project'] = project_id
                    new_dataset['tags'] = [{'name': str(label), 'event_id': new_event_id}]
                    response = requests.post(f'{SPLASH_URL}/datasets',
                                             json=[new_dataset])
                if response.status_code != 200:
                    logging.error(f'Filename: {filename} with label {label} failed with \
                                  status {response.status_code}: {response.json()}.')
                    status =+ f'Filename: {filename} with label {label} failed with \
                               status {response.status_code}. '
        return status
    
    def save_to_directory(self, data_project):
        '''
        Zips images with labels to be downloaded
        '''
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = os.path.join(temp_dir, "downloaded_images")
            # create a folder per label
            for label_key in self.labels_list:
                if self.num_imgs_per_label[label_key]>0:
                    label_dir = data_path / Path(label_key)
                    label_dir.mkdir(parents=True, exist_ok=True)
            for indx, (filename, label) in enumerate(self.labels_dict.items()):
                if len(label)>0:
                    img, uri = data_project.data[indx].read_data(export='pillow')
                    label_dir = f'{data_path}/{label[0]}'
                    base_name = uri.split('/')[-1].split('.')[0]
                    filename = Path(f'{base_name}.tif')
                    i = 0   # check duplicate filename and save under different name if needed
                    while filename.exists():
                        filename = Path(f'{label_dir}/{base_name}_{i}.tif')
                        i += 1
                    img.save(f'{label_dir}/{filename}')
            shutil.make_archive('/app/tmp/results', 'zip', data_path)
        return '/app/tmp/results'
            
    def get_labeling_progress(self):
        '''
        Calculates the labeling progress
        Returns:
            progress_values:    [float] Percentage of images assigned to each label
            progress_labels:    [str] Number of images assigned to each label
            totral_num_labeled: [str] Message displaying how many images have been labeled and how
                                many images are in the data set
        '''
        num_imgs_per_label = list(self.num_imgs_per_label.values())
        progress_values = list(100*np.array(num_imgs_per_label) / max(np.sum(num_imgs_per_label), 1))
        progress_labels = list(map(str, num_imgs_per_label))
        total_num_labeled = f'Labeled {np.sum(num_imgs_per_label)} out of {len(self.labels_dict)}'
        return progress_values, progress_labels, total_num_labeled