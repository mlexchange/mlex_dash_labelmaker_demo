from datetime import datetime
import itertools
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import requests

from app_layout import SPLASH_CLIENT


logging.basicConfig(encoding='utf-8', level=logging.INFO)


class Labels:
    def __init__(self, labels_dict, labels_list, num_imgs_per_label=None) -> None:
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
    
    def update_labels_list(self, add_label=None, remove_label=None):
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
        if remove_label is not None:
            self.labels_list.remove(remove_label)
            self.labels_dict = {key: [val for val in values if val!=remove_label] \
                                for key, values in self.labels_dict.items()}
            self.num_imgs_per_label.pop(remove_label)
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

    def mlcoach_labeling(self, mlcoach_model, mlcoach_label, threshold):
        '''
        Labeling process through mlcoach trained model. This process will not overwrite existing 
        labels in the dictionary
        Args:
            mlcoach_model:          MLCoach model outcome to be used for labeling
            mlcoach_label:          Label to be assigned across the data set
            threshold:              Probability threshold to assign labels
        '''
        df_prob = pd.read_parquet(mlcoach_model)
        mlcoach_filenames = df_prob.index[df_prob[mlcoach_label]>threshold/100].tolist()
        self.assign_labels(mlcoach_label, mlcoach_filenames, overwrite=False)
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
        url = f'{SPLASH_CLIENT}/datasets/search'
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
            event_id:      [str] Event id
        '''
        datasets = self._get_splash_dataset(project_id)
        self.init_labels()          # resets dict and label before loading data
        for dataset in datasets:
            for tag in dataset['tags']:
                if tag["event_id"] == event_id:
                    label = tag['name']
                    if label not in self.labels_list:
                        self.labels_list.append(label)
                    self.assign_labels(label, [dataset['uri']])
        pass

    def save_to_splash(self, project_id, tagger_id):
        '''
        Save labels to splash-ml.
        Args:
            project_id:     [str] Data project id
            tagger_id:      [str] Tagger id
        Returns:
            Request status
        '''
        # Post new tagging event
        event_status = requests.post(f'{SPLASH_CLIENT}/events', 
                               json={"tagger_id": tagger_id, 
                                     "run_time": str(datetime.utcnow())})
        new_event_id = event_status.json()["uid"]
        datasets = self._get_splash_dataset(project_id)
        uri_list = list(map(lambda d: d['uri'], datasets))
        status = ''
        for filename, label in zip(self.labels_dict.keys(), self.labels_dict.values()):
            if len(label)>0:
                label = label[0]                      # 1 label per image
                # if filename in uri_list:            # check if the dataset already exists in splash-ml
                indx = uri_list.index(filename)
                dataset_uid = datasets[indx]['uid']
                tag = {'name': str(label),
                        'event_id': new_event_id}
                data = {'add_tags': [tag]}
                response = requests.patch(f'{SPLASH_CLIENT}/datasets/{dataset_uid}/tags', \
                                            json=data)
                # else:                           # if it doesn't exist in splash-ml, post it
                #     dataset = {'type': 'file',
                #                 'uri': filename,
                #                 'tags': [{'name': 'labelmaker',
                #                         'locator': {'spec': 'label',
                #                                     'path': label}
                #                         }]
                #                 }
                #     response = requests.post(f'{SPLASH_CLIENT}/datasets/', json=dataset)
                #     status_code = response.status_code
                if response.status_code != 200:
                    logging.error(f'Filename: {filename} with label {label} failed with \
                                            status {response.status_code}: {response.json()}.')
                    status = status.append(f'Filename: {filename} with label {label} failed with \
                                            status {response.status_code}. ')
        return status
    
    def save_to_directory(self, save_dir):
        '''
        Save labels to local directory
        Args:
            save_dir:       Directory where the labels will be stored
        '''
        for label_key in self.labels_list:                              # create a folder per label
            if self.num_imgs_per_label[label_key]>0:
                label_dir = save_dir / Path(label_key)
                label_dir.mkdir(parents=True, exist_ok=True)
        filename_list = self.labels_dict.keys()
        for filename in filename_list:
            label = self.labels_dict[filename]
            if len(label)>0:
                label_dir = save_dir / Path(label[0])
                im_bytes = filename
                im = Image.open(im_bytes)
                filename = im_bytes.split("/")[-1]
                f_name = filename.split('.')[-2]
                f_ext  = filename.split('.')[-1]
                filename = Path(filename)
                i = 0
                while filename.exists():                                # check duplicate                                      
                    filename = Path(f'{label_dir}/{f_name}_{i}.{f_ext}') # filename and save under 
                    i += 1                                              # different name if needed 
                im.save(filename)
        pass
            
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
