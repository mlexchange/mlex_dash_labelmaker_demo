# Dash LabelMaker

Simple labeling application with a Dash UI.

## Running
```
cd ../../
docker-compose up --build
```

## Ingest data with MLExchange file manager
Put your dataset inside the data folder or use **MLExchange data connector** to transfer data to this folder (in future) which is mounted to the working directory in the container. Then go to the webpage and click on **Open File Manager** to lauch MLExchange file manager. It offers several options for users to ingest/manipualte data.  

1. Upload images from **Drag and Drop** to cache.  

2. Upload data from **Drag and Drop** to work dir. User can then browse the newly added files/folder in the path table and move them to a new directory.  

3. Move data to a new directory:  
Input the destination directory (relative to root path) and select the files/folder from **File Table**. Then click on **Move** button. The selected files/dirs will be moved into the new directory and the original dirs will be automatically deleted.
**Please note that folders of the same name (from different dirs) will be merged**.  

4. Browse files or directories in the **work dir** and import the selected files:   
After selecting which files or directories and filtering the display by format, click on **Import Selected Files or Directories** button on the right side. When importing a directory, you can import **only** files of a specific format by using the rightmost dropdown menu.  

5. Deleting files or directories:   
The selected file paths can be deleted by clicking **Delete the Selected** button. User must click on **Import** button again to ingest the newly selected files/paths. 


## Labeling instructions:

Assigning a new label:  
1. Select all the images to be labeled  
2. Choose label to be assigned  

Removing an assigned label (un-label):  
1. Select all the images to be unlabeled  
2. Click the "un-label" button
