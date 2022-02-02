# Dash LabelMaker

Simple labeling application with a Dash UI.

## Running
```
cd ../../
docker-compose up --build
```

## How to ingest data?
Put your dataset inside the data folder which is mounted to the working directory in the container. Then go to the webpage and click on `Open File Explorer` which allows:  

1. Uploading images from `Drag and Drop` to cache.  

2. Upload data from `Drag and Drop` to work dir. User can then browse the newly added files/folder in the path table.

3. Browsing files or directores in the `work dir`, and filtering the display by format:   
After selecting which files or direcotries, click on `Import Selected Files or Directories` button on the right. It also allows filtering the formats from the selected directories by selecting the rightmost dropdown menu.  

4. Deleting files or directories:   
The selected file paths can be deleted by clicking `Delete the Selected` button. User must click on `Import` button again to ingest the newly selected files/paths. 


## Labeling instructions:

Assigning a new label:  
1. Select all the images to be labeled  
2. Choose label to be assigned  

Removing an assigned label (un-label):  
1. Select all the images to be unlabeled  
2. Click the "un-label" button
