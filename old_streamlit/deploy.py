import tensorflow as tf
import config as cfg
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import load_model as tf_load_model
import PIL
import os
import glob
import glob2
import ml_label_maker
import h5py

model_path = './data/model/test.h5'
deploy_file_path = './data/valid/'
# Load Model
temp_file = h5py.File(model_path)
model = tf_load_model(temp_file)
summary = model.summary()
print('summary: {}'.format(summary))

input_shape = (model.layers[0].input_shape[0][1], model.layers[0].input_shape[0][2])
#deploy_generator = ml_label_maker.get_evaluate_data(

#)

# Load Data


# Run Model on Data

