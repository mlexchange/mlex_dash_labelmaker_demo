# Dash LabelMaker
Simple labeling application with a Dash UI. This is our first release.

## Install

### Install the labeling pipeline (Labelmaker + Data Clinic + MLCoach)
1. First [install the MLExchange platform](https://github.com/mlexchange/mlex).
	
2. Clone the following repositories:

	* [mlex\_data\_clinic](https://github.com/mlexchange/mlex_data_clinic)
	* [mlex\_mlcoach](https://github.com/mlexchange/mlex_mlcoach)
	* [splash\_ml](https://github.com/als-computing/splash-ml)

	These repositories should be in the same directory, as shown below:
	
	```
	project_directory
	│
	│   mlex_data_clinic
	│   mlex_mlcoach
	|   mlex_dash_labelmaker_demo
	│   splash_ml
	
	```

3. Inside the `mlex_dash_labelmaker_demo` folder, create an environmental file named `.env` as below:

	```
	MONGO_DB_USERNAME=your_username
	MONGO_DB_PASSWORD=your_password
	# uncomment the line below to use Tiled data streaming service (deprecated atm) 
	# TILED_KEY=your_tiled_key
	```

4. Run `./install`. Then go to `http://localhost:8057` in web browser and follow the instructions on each tab.
5. To uninstall the labelmaker pipeline, run `./uninstall`.



---
### Running as a standalone application (Labelmaker only)
To start this labeling service, go to the source code folder and execute the following:
```
docker-compose up --build
```
Go to `http://localhost:8057` in web browser.

Please note that starting the service in this way will not provide connectivity to Data Clinic and MLCoach.

## Ingest data with MLExchange file manager

### Dataset Description
Currently, the file manager supports directory based data definition, similar to the following example:

```
data_directory
│
│   image001.jpeg
│   image002.jpeg
│   ...

```

The supported image formats are: TIFF, TIF, JPG, JPEG, and PNG.

### Instructions
Put your dataset inside the **data folder** or use **MLExchange data connector** to transfer data to this folder (future release). 
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
The File Manager allows users to view file paths either in local paths (mounted to docker) or docker paths. Users can choose which path by toggling the swith below the **Browse** button.


## Labeling instructions:

### Label manually
Assigning a new label:  
1. Select all the images to be labeled  
2. Choose label to be assigned  

Removing an assigned label (un-label):  
1. Select all the images to be unlabeled  
2. Click the "un-label" button

### Label from MLCoach  
Choose MLCoach tab on the right sidebar. This options allows users to label images by using a trained MLCoach model and
a given probability threshold. 

To label images:  

1. Choose an MLCoach model from the dropdown. The probability of each label will be shown under each image according to 
the selected model.
2. Click on the label-name (e.g. "Label 1") and set a probability threshold.  
3. Click "Label with Threshold" button.

The images will be automatically labeled based on the threshold. After which, users can manually un-label and re-label
following **Label Manually** procedures.

For further details on the operation of MLCoach, please refer to its [documentation](https://github.com/mlexchange/mlex_mlcoach).

### Label from Data Clinic
Choose Data Clinic tab on the right sidebar. This tab allows users to tag the selected images and their top N most 
similar images under the same label(s) by using a trained Data Clinic model.

Please follow the instructions in the app sidebar. Likewise, users can also manually un-label and re-label following
**Label Manually** procedures afterwards.

For further details on the operation of Data Clinic, please refer to its [documentation](https://github.com/mlexchange/mlex_data_clinic).


## Copyright
MLExchange Copyright (c) 2021, The Regents of the University of California,
through Lawrence Berkeley National Laboratory (subject to receipt of
any required approvals from the U.S. Dept. of Energy). All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

(1) Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

(2) Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

(3) Neither the name of the University of California, Lawrence Berkeley
National Laboratory, U.S. Dept. of Energy nor the names of its contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.













