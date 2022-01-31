# Dash LabelMaker

Simple labeling application with a Dash UI.

## Running
```
cd ../../
docker-compose up --build
```

## How to use file explorer
Put your dataset inside the data folder which is mounted to the working directory in the container. Then go to the webpage and click on `Open File Explorer` which allows:  

1. Uploading images from `Drag and Drop`  

2. Browsing files or directores in the `work dir`, and filtering the display item formats. After selecting which files or direcotries, click on `Import Selected Files or Directories` button on the right. It also allows filtering the formats from the selected directories by selecting the rightmost dropdown menu.   


## Labeling instructions:

Assigning a new label:
1. Select all the images to be labeled
2. Choose label to be assigned

Removing an assigned label (un-label):
1. Select all the images to be unlabeled
2. Click the "un-label" button
