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
import argparse

# Initialize Libraries/Variables
img_width, img_height = 223, 223
rotation = 0
horizontalFlip = False
verticalFlip = False
batch = 16
input_shape = (img_width, img_height, 3)
target_shape = (img_width, img_height)

parser = argparse.ArgumentParser(
    description='Train a tensorflow model given the test/train directory path, labelled with imagenet specifications')
parser.add_argument('input_dir', help='directory containing raw labels')
parser.add_argument('output_dir', help='path to output directory')
parser.add_argument('model_name', help='tensorflow model to run, case sensitive')
parser.add_argument('pooling', help='pooling option (None, Max, Avg)')
parser.add_argument('batch_size', help='number of images to load into GPU at once')
parser.add_argument('epochs', help='number of epochs to train')
parser.add_argument('stepoch', help='number of steps per epoch')

args = parser.parse_args()
input_dir = args.input_dir
output_data_dir = args.output_dir
train_data_dir = output_data_dir+'/train/'
test_data_dir = output_data_dir+'/test/'
valid_data_dir = output_data_dir+'/val/'
batch = int(args.batch_size)
model_name = args.model_name
pooling = args.pooling
epochs = int(args.epochs)
stepoch = int(args.stepoch)


# Model Params
# model_name = "ResNet50"
# pooling = 'None'
# epochs = 10
# stepoch = 10

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
        print(output_metrics)
        np.savetxt('/data/labelmaker_temp/exp/output/logs/output.csv', output_metrics)
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
ml_label_maker.save_File(model, '/data/labelmaker_temp/exp/output/test.h5')
plt.plot(accuracy)
plt.xlabel('epochs')
plt.ylabel('accuracy')
plt.savefig('/data/labelmaker_temp/exp/output/logs/accuracy.png')
plt.clf()
plt.plot(loss)
plt.xlabel('epochs')
plt.ylabel('loss')
plt.savefig('/data/labelmaker_temp/exp/output/logs/loss.png')

output_metrics = np.c_[accuracy, loss]
np.savetxt('/data/labelmaker_temp/exp/output/logs/output.csv', output_metrics)
