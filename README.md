# Label Maker
Image labeling application with a Dash UI.

## Install

### Install the labeling pipeline (Labelmaker + Data Clinic + MLCoach + Latent Space Explorer)
1. Clone this repository in your local device

2. Inside the `mlex_labelmaker` folder, create an environmental file named `.env` as below:

	```
	# Directory setup
	DATA_DIR=/path/to/data

	# Apps URLs
	MLCOACH_URL=http://localhost:8062
	DATA_CLINIC_URL=http://localhost:8072
	LATENT_SPACE_EXPLORER_URL=http://localhost:8092

	# Services URLs
	SPLASH_URL=http://splash:80/api/v0
	MLEX_COMPUTE_URL=http://job-service:8080/api/v0
	MLEX_CONTENT_URL=http://content-api:8000/api/v0

	# Default Tiled setup
	DEFAULT_TILED_URI=
	DEFAULT_TILED_QUERY=

	# Mongo env
	MONGO_DB_USERNAME=local_test
	MONGO_DB_PASSWORD=<your-password>
	```

3. Run `docker compose up`

## Ingest data with MLExchange File Manager

The MLExchange File Manager supports data access through:

1. Loading data from file system: You can access image data located at the ```data``` folder in the main directory. Currently, the supported formats are: PNG, JPG/JPEG, and TIF/TIFF.

2. Loading data from [Tiled](https://blueskyproject.io/tiled/): Alternatively, you can access data through Tiled by providing a ```tiled_server_uri``` in the frontend of your application and the ```TILED_KEY``` associated with this server as an environment variable.

More information available at [File Manager](https://github.com/mlexchange/mlex_file_manager).


## Labeling instructions:

### Label manually
Assigning a new label:
1. Select all the images to be labeled
2. Choose label to be assigned

Removing an assigned label (un-label):
1. Select all the images to be unlabeled
2. Click the "un-label" button

### Label from MLCoach
Choose MLCoach tab on the right sidebar. This options allows users to label images by using a trained MLCoach model and a given probability threshold.

To label images:

1. Choose an MLCoach model from the dropdown. The probability of each label will be shown under each image according to
the selected model.
2. Click on the label-name (e.g. "Label 1") and set a probability threshold.
3. Click "Label with Threshold" button.

The images will be automatically labeled based on the threshold. After which, users can manually un-label and re-label
following **Label Manually** procedures.

For further details on the operation of MLCoach, please refer to its [documentation](https://github.com/mlexchange/mlex_mlcoach).

### Label from Data Clinic
Choose Data Clinic tab on the right sidebar. This tab allows users to tag similar images under the same label by using a trained Data Clinic model.

Please follow the instructions in the app sidebar. Likewise, users can also manually un-label and re-label following **Label Manually** procedures afterwards.

For further details on the operation of Data Clinic, please refer to its [documentation](https://github.com/mlexchange/mlex_data_clinic).


## Copyright
MLExchange Copyright (c) 2023, The Regents of the University of California,
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
