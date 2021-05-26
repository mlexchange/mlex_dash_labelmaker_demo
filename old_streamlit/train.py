"""
Assume that folders ./data/train and ./data/test exist and ./data/output
exist.
This script will train and save a model
"""
import tensorflow as tf
import config as cfg
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import PIL
import os
import glob
import glob2
import ml_label_maker
import matplotlib.pyplot as plt
import numpy as np

# Initialize Libraries/Variables
img_width, img_height = 223, 223
rotation = 0
horizontalFlip = False
verticalFlip = False
batch = 16
input_shape = (img_width, img_height, 3)
target_shape = (img_width, img_height)

train_data_dir = './data/train/'
test_data_dir = './data/test/'
valid_data_dir = './data/valid/'
output_data_dir = './data/output/'

# Model Params
model_name = "ResNet50"
pooling = 'None'
epochs = 10
stepoch = 10

# Read in data

train_generator, valid_generator, test_generator = ml_label_maker.data_processing(
    rotation,
    horizontalFlip,
    verticalFlip,
    batch,
    target_shape,
    train_data_dir,
    valid_data_dir,
    test_data_dir,
)

# Create Model
accuracy = []
loss = []
class fit_myCallback(tf.keras.callbacks.Callback):
    #For model training
    def __init__(self, accuracy_list, loss_list):
        self.accuracy_list = accuracy_list
        self.loss_list = loss_list
        pass
    def on_batch_end(self, epoch, logs={}):
        self.accuracy_list.append(logs.get('accuracy'))
        self.loss_list.append(logs.get('loss'))
        output_metrics = np.c_[self.accuracy_list, self.loss_list]
        np.savetxt('./data/logs/output.csv', output_metrics)
        pass

class eval_myCallback(tf.keras.callbacks.Callback):

    def __init__(self, accuracy_chart, loss_chart):
        #self.accuracy_chart = accuracy_chart
        #self.loss_chart = loss_chart
        pass
    #for model evaluation
    def on_test_batch_end(self, batch, logs={}):
        #self.accuracy_chart.add_rows([logs.get('accuracy')])
        #self.loss_chart.add_rows([logs.get('loss')])
        pass


fit_callbacks = fit_myCallback(accuracy, loss)
# Launch Training

model = ml_label_maker.create_model(
    model_name,
    pooling,
    stepoch,
    epochs,
    train_generator,
    valid_generator,
    fit_callbacks,
    input_shape,
)
classes = train_generator.class_indices

# save model
ml_label_maker.save_File(model, 'test.h5')
plt.plot(accuracy)
plt.xlabel('epochs')
plt.ylabel('accuracy')
plt.savefig('./data/logs/accuracy.png')
plt.clf()
plt.plot(loss)
plt.xlabel('epochs')
plt.ylabel('loss')
plt.savefig('./data/logs/loss.png')

output_metrics= np.c_[accuracy, loss]
np.savetxt('./data/logs/output.csv', output_metrics)
