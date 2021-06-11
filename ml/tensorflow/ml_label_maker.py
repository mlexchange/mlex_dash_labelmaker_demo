import config as cfg
import tensorflow as tf
import config as cfg
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import PIL
import os
import glob
import glob2
import pathlib
import random
import numpy as np


# dimensions of our images.
img_width, img_height = 223, 223
#input_shape = ((img_width, img_height))
#IMG_SIZE,IMG_SIZE = 223, 223
#nb_channels = 3
#
#cf = cfg.Config('main.cfg') 
#
#
#data_dir = cf['DATA_DIR']
#train_data_dir = cf['TRAIN_DATA_DIR']  # "./
#validation_data_dir = cf['VALIDATION_DATA_DIR']  # "./data/valid"
#test_data_dir = cf['TEST_DATA_DIR']  # "./data/test"
#
## model save directory
#model_save_dir = cf['MODEL_SAVE_DIR']  # "./modelSave"
#
#classes = [subdir for subdir in sorted(os.listdir(test_data_dir)) if
#        os.path.isdir(os.path.join(test_data_dir, subdir))]
#class_num = len(classes)
#print(class_num)

def test_train_classify_split(root_dir: str, train_fraction= .8):
    """
    Given a root directory, where files are categorized by the directory
    they are in (class name == dir name), this will create two new dirs, 
    test and train, containing the split
    """
    root_path = pathlib.Path(root_dir)
    train_path = root_path / 'train'
    train_path.mkdir(exist_ok = True)
    test_path = root_path / 'test'
    test_path.mkdir(exist_ok = True)
    all_things = list(root_path.glob('**/*', ))
    all_labels = [x for x in all_things if x.is_dir()]
    for label_path in all_labels:
        label = label_path.stem
        if ('test' in str(label_path)) or ('train' in str(label_path)):
            # picking up previous test/train split, skip these
            continue
        label_files = list(label_path.glob('*'))
        # generate test train split
        print('\nthere are {} files in label {}'.format(len(label_files), label))
        n_train = int(len(label_files)*train_fraction)
        print('n_train: {}, n_test: {}'.format(n_train, len(label_files)-n_train))
        called_index = {-1:-1}
        for i in range(n_train):
            train_index = -1
            cont = True
            while (cont):
                train_index = random.randint(0, len(label_files)-1)
                if train_index not in called_index:
                    called_index[train_index] = i
                    cont = False
            assert(train_index != -1)

        for i, file_n in enumerate(label_files):
            if i in called_index:
                file_path = root_path / 'train' / label
                file_path.mkdir(exist_ok=True)
            else:
                file_path = root_path / 'test' / label
                file_path.mkdir(exist_ok=True)
            print('moving file {} to {}'.format(str(file_n), str(file_path/file_n.name)))
            file_n.replace(file_path/file_n.name)






# Takes in the randomization options for images and a path to the image file
# that you want used for model.evaluate.  Batch size can be changed for use in
# other functions, but for evaluate you want 1 batch
def get_evaluate_data(rotation_angle, horizontal_flip, vertical_flip,
        evaluate_data_dir, input_shape, batch_size=1):

    test_datagen = ImageDataGenerator(
        rotation_range=rotation_angle,
        horizontal_flip=horizontal_flip, 
        vertical_flip=vertical_flip)

    first_data = glob.glob(evaluate_data_dir+'/**/*.*', recursive=True)
    data_type = os.path.splitext(first_data[1])[-1]
    if(data_type == '.jpeg'):
        test_generator = test_datagen.flow_from_directory(
            evaluate_data_dir,
            target_size= input_shape,
            color_mode="rgb",
            batch_size=batch_size,
            class_mode='categorical')
    else:
        print('please choose a folder with images')
        test_generator = None

    print(type(test_generator))
    return test_generator

# keras callback for evaluating the model so you can see the accuracy on the
# data
class eval_myCallback(tf.keras.callbacks.Callback):
    
    def __init__(self, accuracy_chart, loss_chart):
        self.accuracy_chart = accuracy_chart
        self.loss_chart = loss_chart
    #for model evaluation
    def on_test_batch_end(self, batch, logs={}):
        accuracy_chart.add_rows([logs.get('accuracy')])
        loss_chart.add_rows([logs.get('loss')])


def data_processing(rotation_angle, horizontal_flip, vertical_flip, batch_size, input_shape,
        train_data_dir, validation_data_dir, test_data_dir):
    """
    Process the images and allows randomization as part of the training with random flips or angles if you allow it
    """
    train_datagen = ImageDataGenerator(
            rotation_range=rotation_angle,
            horizontal_flip=horizontal_flip, 
            vertical_flip=vertical_flip)

    test_datagen = ImageDataGenerator(
            rotation_range=rotation_angle,
            horizontal_flip=horizontal_flip, 
            vertical_flip=vertical_flip)

    
    first_data = list(pathlib.Path(train_data_dir).glob("**/*.*"))
    #print(pathlib.Path(train_data_dir))
    #print(first_data)
    data_type = first_data[0].suffix
    print('generating text')
    print('datatype {}'.format(data_type))
    #print(first_data)
    if(data_type == '.jpeg') or (data_type=='.jpg'):
        print('data is jpg')
        train_generator = train_datagen.flow_from_directory(
                train_data_dir,
                target_size=input_shape,
                batch_size=batch_size,
                color_mode="rgb",
                class_mode='categorical')

        print(train_generator)
        valid_generator = test_datagen.flow_from_directory(
                validation_data_dir,
                target_size= input_shape,
                color_mode="rgb",
                batch_size=batch_size,
                class_mode='categorical')

        test_generator = test_datagen.flow_from_directory(
                test_data_dir,
                target_size= input_shape,
                color_mode="rgb",
                batch_size=batch_size,
                class_mode='categorical',
                shuffle=False)
    elif(data_type == '.npy'):
        train_paths = first_data
        validation_paths = glob.glob(validation_data_dir+'/**/*.*', recursive=True)
        test_paths = glob.glob(test_data_dir+'/**/*.*', recursive=True)
        
        
        i = 0
        labels = {}
        for name in classes:
            labels[name] = i
            i+=1






        xTrain = list()
        yTrain = list()
        xValid = list()
        yValid = list()
        xTest = list()
        yTest = list()
        

        for path in train_paths:
            tmp_arr = np.load(path)
            
            input_arr = np.array([[[0,0,0] for y in
                    range(len(tmp_arr))] for x in range(len(tmp_arr))])
            for x in range(len(tmp_arr)):
                for y in range(len(tmp_arr)):
                    rgb = int((255 * tmp_arr[x][y])+0.5)
                    input_arr[x][y] = [rgb, rgb, rgb]
            xTrain.append(input_arr)
            yTrain.append(labels[path.split('/')[-2]])



        for path in validation_paths:
            tmp_arr = np.load(path)
            
            input_arr = np.array([[[0,0,0] for y in
                    range(len(tmp_arr))] for x in range(len(tmp_arr))])
            for x in range(len(tmp_arr)):
                for y in range(len(tmp_arr)):
                    rgb = int((255 * tmp_arr[x][y])+0.5)
                    input_arr[x][y] = [rgb, rgb, rgb]
            xValid.append(input_arr)
            yValid.append(labels[path.split('/')[-2]])

        for path in test_paths:
            tmp_arr = np.load(path)
            
            input_arr = np.array([[[0,0,0] for y in
                    range(len(tmp_arr))] for x in range(len(tmp_arr))])
            for x in range(len(tmp_arr)):
                for y in range(len(tmp_arr)):
                    rgb = int((255 * tmp_arr[x][y])+0.5)
                    input_arr[x][y] = [rgb, rgb, rgb]
            xTest.append(input_arr)
            yTest.append(labels[path.split('/')[-2]])
        
        xTrain = np.array(xTrain)
        xValid = np.array(xValid)
        xTest = np.array(xTest)
        yTrain = tf.keras.utils.to_categorical(yTrain, num_classes=14)
        yValid = tf.keras.utils.to_categorical(yValid, num_classes=14)
        yTest = tf.keras.utils.to_categorical(yTest, num_classes=14)

        print(len(xTrain), len(xTrain[0]), len(xTrain[0][0]), len(xTrain[0][0][0]))
        print(len(yTrain), len(yTrain[0]))

        print(type(xTrain))
        print(type(yTrain))

        train_generator = train_datagen.flow(
                x=xTrain,
                y=yTrain,
                batch_size = batch_size,
                shuffle=True)

        valid_generator = test_datagen.flow(
                x=xValid,
                y=yValid,
                batch_size = batch_size,
                shuffle=True)

        test_generator = test_datagen.flow(
                x=xTest,
                y=yTest,
                batch_size = batch_size,
                shuffle=True)
            





    return train_generator, valid_generator, test_generator


# creates a model based on the options given by the user in the streamlit
# interface and trains it off of train_generator data
def create_model(
        value, pooling, stepoch, epochs, train_generator, valid_generator,
        fit_callbacks, input_shape):
    class_num = len(train_generator.class_indices)
    code = compile(
            "tf.keras.applications." + value +
            "(include_top=True, weights=None, input_tensor=None," +
            "pooling=" + pooling + 
            ", input_shape = " + str(input_shape) + 
            ", classes= class_num)","<string>","eval") 
    model = eval(code)
    tf.keras.utils.plot_model(model, "model_layout.png", show_shapes=True)
    opt=tf.keras.optimizers.Adam()
    model.compile(
            optimizer='adam', loss='categorical_crossentropy',
            metrics=['accuracy'])
    #fit model while also keeping track of data for streamlit plots.
    print('Fitting model...')
    model.fit(
            train_generator, steps_per_epoch=stepoch, validation_steps=stepoch, epochs=epochs,
            verbose=1, validation_data=test_generator,
            callbacks=[fit_callbacks])  
    print('Model is fit!')
    return model  

# saves model as an .h5 file on local disk
def save_File(model, save_path='my_model.h5'):
    # save model
    model.save(save_path)
    print("Saved to disk")


def retrain(loaded_model, start: int,  epochs: int, 
        rotation: float, horizontalFlip: bool, batch: int, 
        train_data_dir: str, validation_data_dir: str, test_data_dir: str,steps_per_epoch: int = 10,  verbose: bool = True) -> None:
    """
    Retrain cnn using transfer learning

    Args: 
        loaded_model (tensorflow model)
        start (int), layer index to begin training on (> start will be trained)
        steps_per_epoch (int)
        epochs (int),
        verbose (bool) = 1,
        rotation (float),
        horizontalFlip (bool) = False,
        batch (int), 
        train_data_dir (str),
        validation_data_dir (str),
        test_data_dir (str)
    
    Returns:
        None
    """
        
        ### SETUP ###

    fit_callbacks = fit_myCallback(accuracy_chart, loss_chart)

    loaded_model.trainable = True
    for layers in loaded_model.layers[:int(start)]:
        layers.trainable = False
    # compiles and fits the model with the locked layers, but same optimizer
    # as before, should probably be changed to a softer opt for better
    # results
    opt=tf.keras.optimizers.Adam()
    loaded_model.compile(
            optimizer=opt, loss='categorical_crossentropy',
            metrics=['accuracy'])
    #fit model while also keeping track of data for streamlit plots.
    train_generator, valid_generator, test_generator = data_processing(rotation,
        horizontalFlip, verticalFlip, batch, train_data_dir,
        validation_data_dir, test_data_dir)


    loaded_model.fit(
            train_generator, steps_per_epoch = 10, epochs=epochs, verbose=1,
            validation_data=test_generator, callbacks=[fit_callbacks])  
    save_File(loaded_model)


