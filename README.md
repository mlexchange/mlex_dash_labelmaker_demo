# Dash LabelMaker

Simple labeling application with a Dash UI.

## Running
To run this demo, please start the following services in the order:

* mlex_computing_api
* mlex_dash_segmentation_demo

To start a service, go to the source code folder and execute the following:
```
docker-compose up --build
```
Go to `http://localhost:8057` in web browser.

## Ingest data with MLExchange file manager
Put your dataset inside the **data folder** or use **MLExchange data connector** to transfer data to this folder (in future). 
This folder is mounted to the working directory in the container, and it is your **home data dir (HOME)**. 
Then go to the webpage and click on **Open File Manager** to lauch MLExchange file manager. It offers several options for users to ingest/manipualte data.   

1. Upload data from **Drag and Drop** to home data dir. 
Upload either a single file or a zip file (files) through drag and drop.
User can then browse the newly added files/folder in the path table and move them to a new directory inside HOME.  

2. Browse files or directories in the **HOME** and import the selected files:   
After selecting which files or directories and filtering the display by format, click on **Import Selected Files or Directories** button on the right side. 
When importing a directory, you can import **only** files of a specific format by using the rightmost dropdown menu.  

3. Move data into a new directory:  
Input the destination directory (relative to root path) and select the files/folder from **File Table**. Then click on **Move** button. 
The selected files/dirs will be (recursively) moved into the new directory and the original dirs will be automatically deleted. 
If no input, files/dirs will be moved to **HOME**.
**Please note that folders of the same name (from different dirs) will be merged**.  

4. Deleting files or directories:   
The selected file paths can be deleted by clicking **Delete the Selected** button. User must click on **Import** button again to ingest the newly selected files/paths 


## View paths in different environments
File manager allows users to view file paths either in local paths (mounted to docker) or docker paths. Users can choose which path by toggling the swith below the **Browse** button.


## Labeling instructions:

### Label manually
Assigning a new label:  
1. Select all the images to be labeled  
2. Choose label to be assigned  

Removing an assigned label (un-label):  
1. Select all the images to be unlabeled  
2. Click the "un-label" button

### Label from MLCoach  
Choose MLCoah tab on the right side bar. 
The probability of each label will be shown under each image. 
It allows users to label by a probibility threshold. 
To label iamges:  

1. Click on the label (button) and set a probability threshold.  
2. Click Label with Threshold button.

The images will be automatically labeled based on the threshold. After which, users can manually unlabel and re-label following **Label Manually** procedures.

### Label from DataClinic
Choose DataCinic tab on the right side bar.
MLExchange Data clinic will produce unsupervised similarity results of all images.
This tab allows users to tag the selected images and their top N most simialr images under the same label(s).

Please follow the instructions in the app side bar. Likewise, users can also manually unlabel and re-label following **Label Manually** procedures afterwards.













