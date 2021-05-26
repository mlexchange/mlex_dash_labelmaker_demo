"""
name: label-maker-main.py
maintainer: adam green
date: 2021-02-03

description
===============

label-maker-main will launch a streamlit instance. It is the main application script,
and will handle bringing in the project specific functions from other libraries (ml/data handling). 

The goal is to keep this clean, and only have the nuts and bolts of running the streamlit application here.
"""

##### DEPENDENCIES ################
import numpy as np
import streamlit as st
import PIL
import config as cfg
import os
import ml_label_maker  #data processing and ml
import tensorflow as tf
import h5py
import json
from tensorflow.keras.models import Sequential as tf_Sequential
from tensorflow.keras.models import load_model as tf_load_model
import pathlib
import matplotlib.pyplot as plt

import SessionState


# dimensions of our images.
img_width, img_height = 223, 223
input_shape = ((img_width, img_height))
IMG_SIZE,IMG_SIZE = 223, 223
input_size = (223, 223)
nb_channels = 3

cf = cfg.Config('main.cfg') 


data_dir = cf['DATA_DIR']
train_data_dir = cf['TRAIN_DATA_DIR']  # "./
validation_data_dir = cf['VALIDATION_DATA_DIR']  # "./data/valid"
test_data_dir = cf['TEST_DATA_DIR']  # "./data/test"

# model save directory
model_save_dir = cf['MODEL_SAVE_DIR']  # "./modelSave"

classes = [subdir for subdir in sorted(os.listdir(test_data_dir)) if
        os.path.isdir(os.path.join(test_data_dir, subdir))]
class_num = len(classes)
print(class_num)
        
    

# Memory Management for GPU
#config = tf.compat.v1.ConfigProto()
#config.gpu_options.allow_growth=True
#sess = tf.compat.v1.Session(config=config)
#tf.compat.v1.keras.backend.set_session(sess)
#

def single_file_selector(folder_path='.', side_bar=True):
    filenames = os.listdir(folder_path)
    if side_bar:
        selected_filename = st.sidebar.selectbox(
                'Select a file in ' + folder_path , filenames)
    else:
        selected_filename = st.selectbox(
                'Select a file in ' + folder_path , filenames)
    path = os.path.join(folder_path, selected_filename)
    return path

# creates a streamlit select drop down box to select files in current dir.  when
# one is selected, assuming its a dir, it calls itself again with that dir
# unless you wanted to select that dir as the path point
def recursive_file_selector(folder_path='.', side_bar=True):
    try:
        filenames = os.listdir(folder_path)
        filenames.insert(0,"Select Current Directory")
    #    filenames.insert(0,"None")
        if side_bar:
            selected_filename = st.sidebar.selectbox(
                    'select a file in ' + folder_path , filenames)
        else:
            selected_filename = st.selectbox(
                    'Select a file in ' + folder_path , filenames)
        path = os.path.join(folder_path, selected_filename)
        if os.path.isfile(path):
            return os.path.join(folder_path, selected_filename)
        elif selected_filename == "Select Current Directory":
            return folder_path
        else:
            return recursive_file_selector(folder_path=path)
    except:
        print("Folder Finder Error Catch")


def main():
     ### SETUP ###

    state = SessionState._get_state()
    state.image_size = input_size #need standard image size (this can be modified if you load in an external model)
    st.title("LabelMaker")
    """
    This demo demonstrates the ability of modern machine learning to classify x-ray data.
    """


    st.sidebar.title("LabelMaker Functions")
    tab = st.sidebar.selectbox("",(
         'Create New Model', 'Load Trained Model', 'Load Training Images','Evaluate Model on Data', 'Test Prediction using Model',
        'Test Prediction using Model (slider)', 'Transfer Learning',
        'View Images in Categories', 'Save and Load Models', 'State Management'))
    if tab == 'Load Training Images':
        load_images(state)
    if tab == 'Create New Model':
        tab_create_new_model(state)
    if tab == 'Load Trained Model':
        tab_load_trained(state)
    elif tab == "Evaluate Model on Data":
        tab_evalute_model(state)
    elif tab == "Test Prediction using Model":
        tab_test_prediction(state)
    elif tab == "Test Prediction using Model (slider)":
        tab_test_prediction_slider(state)
    elif tab == "Transfer Learning":
        tab_transfer_learning(state)
    elif tab == "View Images in Categories":
        tab_view_image_categories(state)
    elif tab == "Save and Load Models":
        tab_save_load_model()
    elif tab == 'State Management':
        tab_state_management(state)


    return None

# keras callbacks for model training.  Threads while keras functions are running
# so that you can see training or evaluation of the model in progress

class fit_myCallback(tf.keras.callbacks.Callback):
    #For model training
    def __init__(self, accuracy_chart, loss_chart):
        self.accuracy_chart = accuracy_chart
        self.loss_chart = loss_chart
    def on_batch_end(self, epoch, logs={}):
        self.accuracy_chart.add_rows([logs.get('accuracy')])
        self.loss_chart.add_rows([logs.get('loss')])
        
#    def on_train_end(self, logs={}):
#        try:
#            st.text("Accuracy: "+str(logs.get('accuracy'))+" Loss: "+
#J                str(logs.get('loss')))
 #       except:
 #           print('no logs') #tested with tensorflow 2.1.0 this gives an error. Don't know why. It can no longer access logs when training is over.



# keras callback for evaluating the model so you can see the accuracy on the
# data
class eval_myCallback(tf.keras.callbacks.Callback):
    
    def __init__(self, accuracy_chart, loss_chart):
        self.accuracy_chart = accuracy_chart
        self.loss_chart = loss_chart
    #for model evaluation
    def on_test_batch_end(self, batch, logs={}):
        self.accuracy_chart.add_rows([logs.get('accuracy')])
        self.loss_chart.add_rows([logs.get('loss')])

def load_images(state):
    '''
    Can manually load training/test/validation images in
    '''
    st.subheader("Image Selection")
    state.file_uploader = st.file_uploader("Image Ingestion",
    type=['png', 'jpeg', 'jpg'], accept_multiple_files=True)
    image_file = []
    if image_file is not None:
	    for image_f in state.file_uploader:
		    st.write(type(image_f))
		    file_details = {"Filename":image_f.name,"FileType":image_f.type,"FileSize":image_f.size}
		    st.write(file_details)
		    img = load_image(image_f)
		    st.image(img,width=200)
    st.text(image_file)



def tab_create_new_model(state):
    ''' Allows you to train models and saves the most recent model to its current dir
for use in predict and evaluate
training model tab that lets you change the aspects of the images
    Args:
        image_size, this is needed to set the correct input layers for the pretrained networks
    Returns:
        model (tensorflow/keras tensor), the trained model
    '''

    ### SETUP AND INPUT ##############
    state.input_shape = (state.image_size[0], state.image_size[1], 3)
    st.text("Sample Image")
    st.sidebar.title("Image Randomization Options")
    rotation = st.sidebar.slider('Allowed Rotation Angle',0,360,0,1)
    horizontalFlip = st.sidebar.checkbox('Horizontal Flip', value = False)
    verticalFlip = st.sidebar.checkbox('Vertical Flip', value = False)
    st.sidebar.title("Training Options")
    pooling = st.sidebar.radio("Pooling Options",('None','Max','Average')) 
    stepoch = st.sidebar.slider("Steps Per Epoch",10,100,10)
    epochs = st.sidebar.slider('Epochs',1,100,1,1)
    batch = st.sidebar.slider('Batch Size',4,1500,4,8)
    value = st.sidebar.selectbox("ML Model", [
        "Xception", "VGG16", "VGG19", "ResNet101", "ResNet152", "ResNet50V2",
        "ResNet50", "ResNet152V2", "InceptionV3", "DenseNet201", "NASNetLarge",
        "InceptionResNetV2", "DenseNet169"])

    state.model_name = st.sidebar.text_input('Model Name', 'adams_model.h5')
    ### RUN ####
    train_generator, valid_generator, test_generator = ml_label_maker.data_processing(
        rotation, horizontalFlip, verticalFlip, batch, state.input_shape, train_data_dir,
        validation_data_dir, test_data_dir)
       #this is a test 
    ### OUTPUT ###
    pimage = st.sidebar.slider('Sample image',1,train_generator.n,1,1)
    try:
        image = PIL.Image.open(train_generator.filepaths[pimage - 1])
        st.image(image)
    except:
        print("using numpy array")
    if st.sidebar.button('Train CNN now'):
        
        st.title('Model Accuracy Graphs')

        st.text('Accuracy')
        accuracy_chart = st.line_chart()

        st.text('Loss')
        loss_chart = st.line_chart()

        fit_callbacks = fit_myCallback(accuracy_chart, loss_chart)

        state.model = ml_label_maker.create_model(
                value, pooling, stepoch, epochs, train_generator, valid_generator,
                fit_callbacks, input_shape)
        state.classes = train_generator.class_indices
        print(state.classes)
        print(state.model)

    if st.sidebar.button("Show Model"):
        if state.model_file is not None:
            print('model file: {}'.format(state.model_file))
            print(st.__version__)

            print(state.model)
            print(state.model.summary())
            print(state.classes)

    if st.sidebar.button('Save Model'):
        ml_label_maker.save_File(state.model, state.model_name)
        with open('class_list.json', 'w') as f:
            json.dump(state.classes, f)

    return state.model

def tab_load_trained(state):

    #state.model = None
    if st.sidebar.button("Choose CNN File"):
        state.model_file =  st.file_uploader("Choose Model File")
        print(state.model_file)
    if st.sidebar.button("Load CNN Into Memory"):
        print(state.model_file)
        if state.model_file is not None:
            #state.model = model_file.getvalue()
            temp_file = h5py.File(state.model_file, 'r')
            state.model = tf_load_model(temp_file)
            with open('class_list.json', 'r') as f:
                state.classes = json.load(f)
            print('classes: {}'.format(state.classes))
            st.text("Model Loaded")
            state.model.summary(print_fn = st.text)
            summary = state.model.summary()
            print('summary: {}'.format(summary))
            #state.model.layers
            assert(len(state.model.layers[0].input_shape[0]) == 4)
            state.input_shape = (state.model.layers[0].input_shape[0][1], state.model.layers[0].input_shape[0][2])

            print('input shape from mode: {}'.format(state.input_shape))

def tab_evalute_model(state):
    """
    Calculate accuracy on validation data set
    """
    ### SETUPT AND INPUT ###
    st.sidebar.title("Choose a Validation Directory")
    filename = ''
    #while pathlib.Path(filename).suffix != 'jpeg':
    try:
        filename = single_file_selector(folder_path=data_dir)
        assert(len(list(pathlib.Path(filename).glob("**/*.jpeg"))) > 0)

        print('select directory with jpeg files please')
        st.write('You selected `%s`' % filename)
        st.sidebar.title("Image Randomization Options")
        rotation = st.sidebar.slider('Allowed Rotation Angle',0,360,0,1)
        horizontalFlip = st.sidebar.checkbox('Horizontal Flip', value = False)
        verticalFlip = st.sidebar.checkbox('Vertical Flip', value = False)
        batch = 1

        print(state.input_shape)
        test_generator = ml_label_maker.get_evaluate_data(
                rotation, horizontalFlip, verticalFlip, filename, state.input_shape)
        #you need to feed state.input_size in, as an externally loaded model may be expecting different sized images

    except Exception as e:
        #print('please select a directory with jpeg files')
        #print(list(pathlib.Path(filename).glob("**/*.jpeg")))
        #print(len(list(pathlib.Path(filename).glob("**/*.jpeg"))))
        print(e)

    if st.sidebar.button('Evaluate on Data'):
    ### RUN ###
        # load model
       # print('loading from file')
       # loaded_model = tf_load_model("my_model.h5") #fails on h5py > 3.0 (json.loads(model_config.decode('utf-8') AttEr: 'str' object has no attr 'decode'))
        try:
            st.title('Evaluation Data')
            st.text('Accuracy')
            accuracy_chart = st.line_chart()
            st.text('Loss')
            loss_chart = st.line_chart()


            loaded_model = state.model 
            eval_callbacks = eval_myCallback(accuracy_chart, loss_chart)
            results = loaded_model.evaluate(
                test_generator, callbacks=[eval_callbacks])
            st.text("test loss, test acc: " +str(results[0])+ ", " +str(results[1]))

        except Exception as e:
            st.text("Please load or train a model")
            print(e)
            ### OUTPUT ###

def tab_test_prediction(state):
    """
    Prediction tab that shows model's predictions on certain images across all 14 classes
    """

    ###  SETUP AND INPUT ###
    img_path = ''
    try:
        img_path = recursive_file_selector(data_dir)
        print('img_path: {}'.format(img_path))
        assert(pathlib.Path(img_path).suffix == '.jpeg')
        print(state.input_shape)
        img = tf.keras.preprocessing.image.load_img(img_path, target_size=state.input_shape)
        input_arr = tf.keras.preprocessing.image.img_to_array(img)
        input_arr = np.array([input_arr])
        st.image(img)
        if st.sidebar.button('Predict on Sample Image'):
            # if (train_generator == None):
            #    st.text("Model not trained.")
            try:
                loaded_model = state.model
                predictions = loaded_model.predict(input_arr)[0] * 100
                classes = [subdir for subdir
                           in sorted(os.listdir(test_data_dir))
                           if os.path.isdir(os.path.join(
                        test_data_dir, subdir))]
                class_probs = dict(zip(classes, predictions))
                for className in class_probs:
                    st.text(className + " probability: %.4f%%"
                            % class_probs[className])
                # predictions = loaded_model.predict(
                #     (np.resize(
                #         np.asarray(img), (1, 223, 223, 3)
                #     ) * (1./255)).astype("float32")
                # )
            except FileNotFoundError:
                st.text("Model h5 file not found. Train a model.")
    except Exception as e:
        st.text("Select an image.")
        print(pathlib.Path(img_path).suffix)
        print(e)


def tab_test_prediction_slider(state):
    train_generator, valid_generator, test_generator = ml_label_maker.data_processing(
            0, False, False, 1, state.input_shape, train_data_dir,
            validation_data_dir, test_data_dir)
    pimage = st.sidebar.slider('Sample image',1,test_generator.n,1,1)
    img_path = test_generator.filepaths[pimage - 1]
    # instead of what follows, could go through every image in the generator
    #     and throw them out until we reach the one we want; might be inefficient
    #     for large datasets though
    img = tf.keras.preprocessing.image.load_img(img_path, target_size=state.input_shape)
    input_arr = tf.keras.preprocessing.image.img_to_array(img)
    input_arr = np.array([input_arr])

    st.image(img)

    if st.sidebar.button('Predict on Sample Image'):
        try:
            loaded_model = state.model
            predictions = loaded_model.predict(input_arr)[0] * 100
            classes = [subdir for subdir
                       in sorted(os.listdir(test_data_dir))
                       if os.path.isdir(os.path.join(
                    test_data_dir, subdir))]
            class_probs = dict(zip(classes, predictions))
            for className in class_probs:
                st.text(className + " probability: %.4f%%"
                        % class_probs[className])
        except FileNotFoundError:
            st.text("Model h5 file not found. Train a model.")


def tab_transfer_learning(state):
    """
    Tab that enables transfer learning, allowing you to take in a pre-trained neural net and train it further on new data
    """

    #loaded_model = tf_load_model("my_model.h5")
    loaded_model = state.model

    
    st.sidebar.title("Image Randomization Options")
    rotation = st.sidebar.slider('Allowed Rotation Angle',0,360,0,1)
    horizontalFlip = st.sidebar.checkbox('Horizontal Flip', value = False)
    verticalFlip = st.sidebar.checkbox('Vertical Flip', value = False)
    st.sidebar.title("Training Options")
    epochs = st.sidebar.slider('Epochs',1,100,1,1)
    batch = st.sidebar.slider('Batch Size',16,1500,128,8)

    model_len = len(loaded_model.layers)
    st.text("Number of Layers in the loaded Model: " +str(model_len))
    start = st.slider("Select a Layer to start training at",1,model_len,100)


    train_generator, valid_generator, test_generator = ml_label_maker.data_processing(rotation,
            horizontalFlip, verticalFlip, batch, state.input_size, train_data_dir,
            validation_data_dir, test_data_dir)

    if st.button("Retrain Layers"):
        st.text('Accuracy')
        accuracy_chart = st.line_chart()
        st.text('Loss')
        loss_chart = st.line_chart()


        ml_label_maker.retrain(loaded_model, epochs,
                rotation, horizontalFlip, verticalFlip, batch, train_data_dir, 
                validation_data_dir, test_data_dir, steps_per_epoch = 10, verbose = True )
        #tag: todo 
        # Let's wrap this all in a function call and move it over to ml
        """
        def retrain():
            Input: accuracy_chart, loss_chart? 
            Output:
        """
        # Locks the layers that you dont want to train so you can selectivly
        # train the model (Training the last layers is the most effective)
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
        loaded_model.fit(
                train_generator, steps_per_epoch = 10, epochs=epochs, verbose=1,
                validation_data=valid_generator, callbacks=[fit_callbacks])  
        save_File(loaded_model)


    st.title('Current Model Layout')
    try:
        image2 = PIL.Image.open('model_layout.png')
        st.image(image2, caption='Model Layout')
    except FileNotFoundError:
        st.text("File not found. Try making a model first.")


def tab_view_image_categories(state):
    """
    Tab that allows you to view classified images
    """
    st.sidebar.title("Select an Image to View")
    try:
        img_path = recursive_file_selector(data_dir) 
        image = PIL.Image.open(img_path)
        
        st.image(image, caption='Example')
    except:
        print("Cant Load Image using None Path or selected one")

    
    n_classes = len(state.classes)

    n_cols =  3
    n_rows = n_classes // n_cols + n_classes % n_cols
    fig, ax = plt.subplots(ncols = n_cols, nrows = n_rows)
    classes = state.classes
    print(classes)
    for category, n_hot in classes.items():
        print(category)
    for a in ax.flatten():
        a.axis('off')
    st.pyplot(fig)
 

def tab_save_load_model(image_size = (223, 223)):
    """
    tab that allows you to save trained model as .h5 file, 
    or load a saved model. Default to my_model.h5
    """
    st.title("Save Current Model")
    model_name = st.text_input('Type in Model Name')
    if st.button("Save Current Model"):
        loaded_model = tf-tensorflow.keras.models("my_model.h5")
        save_File(loaded_model, save_path=model_save_dir+"/"+model_name+".h5")
    st.title("Load Saved Model")
    model_path = single_file_selector(folder_path=model_save_dir, side_bar=False)
    if st.button("Load Model"):
        loaded_model = tf-tensorflow.keras.models(model_path)
        save_File(loaded_model)


def tab_state_management(state):
    if st.sidebar.button("Print State"):
        print(vars(state))
        st.text(json.dumps(vars(state), indent = 4, default=str))
    if st.sidebar.button("Clear State"):
        state.clear()
        state.file_uploader = []

if __name__ == "__main__":
    main()
