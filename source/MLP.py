import os
import time

import matplotlib
from keras.layers import Dense, Input, Reshape, concatenate
from keras.models import Model, Sequential
from keras.preprocessing.image import ImageDataGenerator
from keras.utils import plot_model

# Force matplotlib to not use any Xwindows backend. If you need to import
# pyplot, do it after setting `Agg` as the backend.
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np
from sklearn import svm
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from bag_of_visual_words import BoVW
from evaluator import Evaluator
from utils import Color, colorprint


class multi_layer_perceptron(object):
    class LAYERS(object):
        FIRST = 'pool1'
        SECOND = 'fc1'
        THIRD = 'fc2'
        LAST = 'fc3'
        LABELS = 'fc4'

    def __init__(self, img_size=32, batch_size=16,
                 dataset_dir='/home/datasets/scenes/MIT_split',
                 model_fname='my_first_mlp.h5'):
        # initialyze model
        self.IMG_SIZE = img_size
        self.BATCH_SIZE = batch_size
        self.DATASET_DIR = dataset_dir
        self.MODEL_FNAME = model_fname
        colorprint(Color.BLUE, 'Creating object\n')

        if not os.path.exists(self.DATASET_DIR):
            colorprint(Color.RED,
                       'ERROR: dataset directory ' + self.DATASET_DIR + ' do not exists!\n')

    def build_MLP_model(self):
        # Build MLP model
        init = time.time()
        colorprint(Color.BLUE, 'Building MLP model...\n')

        # Build the Multi Layer Perceptron model
        self.model = Sequential()
        self.model.add(Reshape((self.IMG_SIZE * self.IMG_SIZE * 3,),
                               input_shape=(self.IMG_SIZE, self.IMG_SIZE, 3),
                               name=self.LAYERS.FIRST))
        self.model.add(
            Dense(units=2048, activation='relu', name=self.LAYERS.SECOND))
        self.model.add(
            Dense(units=1024, activation='relu', name=self.LAYERS.THIRD))
        self.model.add(
            Dense(units=1024, activation='relu', name=self.LAYERS.LAST))
        self.model.add(
            Dense(units=8, activation='softmax', name=self.LAYERS.LABELS))

        self.model.compile(loss='categorical_crossentropy',
                           optimizer='sgd',
                           metrics=['accuracy'])

        print(self.model.summary())

        plot_model(self.model, to_file='modelMLP.png', show_shapes=True,
                   show_layer_names=True)

        colorprint(Color.BLUE, 'Done!\n')

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

    def build_MLP_two_outputs_model(self):
        # Build MLP model
        init = time.time()
        colorprint(Color.BLUE, 'Building MLP model...\n')

        # Input layers
        main_input = Input(shape=(self.IMG_SIZE, self.IMG_SIZE, 3),
                           dtype='float32', name='main_input')
        inp = Reshape((self.IMG_SIZE * self.IMG_SIZE * 3,),
                      input_shape=(self.IMG_SIZE, self.IMG_SIZE, 3),
                      name='Reshape')(main_input)

        # First branch layers
        first = Dense(512, activation='relu', name='1stMLP-1')(inp)
        first = Dense(512, activation='relu', name='1stMLP-2')(first)

        # Second branch layers
        second = Dense(1024, activation='relu', name='2ndMLP')(inp)

        # Concatenate the previous layers 
        x = concatenate([first, second], name='concatenation')
        main_output = Dense(units=8, activation='softmax', name='main_output')(
            x)

        # Compile the model
        self.model = Model(inputs=main_input, outputs=main_output)
        self.model.compile(loss='categorical_crossentropy',
                           optimizer='sgd',
                           metrics=['accuracy'])

        print(self.model.summary())

        plot_model(self.model, to_file='modelMLP.png', show_shapes=True,
                   show_layer_names=True)

        colorprint(Color.BLUE, 'Done!\n')

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

    def train_MLP_model(self):
        # train the MLP model
        init = time.time()

        if os.path.exists(self.MODEL_FNAME):
            colorprint(Color.YELLOW,
                       'WARNING: model file ' + self.MODEL_FNAME + ' exists and will be overwritten!\n')

        colorprint(Color.BLUE, 'Start training...\n')

        # this is the dataset configuration we will use for training
        # only rescaling
        train_datagen = ImageDataGenerator(
            rescale=1. / 255,
            horizontal_flip=True)

        # this is the dataset configuration we will use for testing:
        # only rescaling
        test_datagen = ImageDataGenerator(rescale=1. / 255)

        # this is a generator that will read pictures found in
        # subfolers of 'data/train', and indefinitely generate
        # batches of augmented image data
        train_generator = train_datagen.flow_from_directory(
            self.DATASET_DIR + '/train',  # this is the target directory
            target_size=(self.IMG_SIZE, self.IMG_SIZE),
            # all images will be resized to IMG_SIZExIMG_SIZE
            batch_size=self.BATCH_SIZE,
            classes=['coast', 'forest', 'highway', 'inside_city', 'mountain',
                     'Opencountry', 'street', 'tallbuilding'],
            class_mode='categorical')  # since we use binary_crossentropy loss, we need categorical labels

        # this is a generator that will read pictures found in
        # subfolers of 'data/test', and indefinitely generate
        # batches of augmented image data
        validation_generator = test_datagen.flow_from_directory(
            self.DATASET_DIR + '/test',
            target_size=(self.IMG_SIZE, self.IMG_SIZE),
            batch_size=self.BATCH_SIZE,
            classes=['coast', 'forest', 'highway', 'inside_city', 'mountain',
                     'Opencountry', 'street', 'tallbuilding'],
            class_mode='categorical')

        self.history = self.model.fit_generator(
            train_generator,
            steps_per_epoch=1881 // self.BATCH_SIZE,
            epochs=50,
            validation_data=validation_generator,
            validation_steps=807 // self.BATCH_SIZE)

        colorprint(Color.BLUE, 'Done!\n')
        colorprint(Color.BLUE,
                   'Saving the model into ' + self.MODEL_FNAME + ' \n')
        self.model.save_weights(
            self.MODEL_FNAME)  # always save your weights after training or during training
        colorprint(Color.BLUE, 'Done!\n')

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

    def load_MLP_model(self):
        # load a MLP model
        init = time.time()

        if not os.path.exists(self.MODEL_FNAME):
            colorprint(Color.YELLOW,
                       'Error: model file ' + self.MODEL_FNAME + ' exists and will be overwritten!\n')

        colorprint(Color.BLUE,
                   'Loading the model from ' + self.MODEL_FNAME + ' \n')
        self.model.load_weights(
            self.MODEL_FNAME)  # always save your weights after training or during training
        colorprint(Color.BLUE, 'Done!\n')

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

    def get_layer_output(self, layer=LAYERS.LAST, image_set='test'):
        # get layer output
        init = time.time()

        colorprint(Color.BLUE, 'Getting layer output...\n')
        model_layer = Model(inputs=self.model.input,
                            outputs=self.model.get_layer(layer).output)

        # this is the dataset configuration we will use for testing:
        # only rescaling
        datagen = ImageDataGenerator(rescale=1. / 255)
        # this is a generator that will read pictures found in
        # subfolers of 'data/test', and indefinitely generate
        # batches of augmented image data
        generator = datagen.flow_from_directory(
            self.DATASET_DIR + '/' + image_set,
            target_size=(self.IMG_SIZE, self.IMG_SIZE),
            batch_size=self.BATCH_SIZE,
            classes=['coast', 'forest', 'highway', 'inside_city', 'mountain',
                     'Opencountry', 'street', 'tallbuilding'],
            class_mode='categorical',
            shuffle=False)

        labels = generator.classes

        # get the features from images
        features = model_layer.predict_generator(generator, steps=2)
        colorprint(Color.BLUE, 'Done!\n')

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

        return features, labels

    def plot_history(self):

        # summarize history for accuracy
        plt.plot(self.history.history['acc'])
        plt.plot(self.history.history['val_acc'])
        plt.title('model accuracy')
        plt.ylabel('accuracy')
        plt.xlabel('epoch')
        plt.legend(['train', 'validation'], loc='upper left')
        plt.savefig('accuracy.jpg')
        plt.close()

        # summarize history for loss
        plt.plot(self.history.history['loss'])
        plt.plot(self.history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train', 'validation'], loc='upper left')
        plt.savefig('loss.jpg')

    def plot_results(self):
        # plot classification results

        colorprint(Color.BLUE, 'Getting classification results...\n')
        init = time.time()

        # this is the dataset configuration we will use for testing:
        # only rescaling
        test_datagen = ImageDataGenerator(rescale=1. / 255)
        # this is a generator that will read pictures found in
        # subfolers of 'data/test', and indefinitely generate
        # batches of augmented image data

        test_generator = test_datagen.flow_from_directory(
            self.DATASET_DIR + '/test',
            target_size=(self.IMG_SIZE, self.IMG_SIZE),
            batch_size=self.BATCH_SIZE,
            classes=['coast', 'forest', 'highway', 'inside_city', 'mountain',
                     'Opencountry', 'street', 'tallbuilding'],
            class_mode='categorical',
            shuffle=False)
        # Get ground truth
        test_labels = test_generator.classes

        # Predict test images
        predictions_raw = self.model.predict_generator(test_generator)
        predictions = []
        for prediction in predictions_raw:
            predictions.append(np.argmax(prediction))
        # Evaluate results
        evaluator = Evaluator(test_labels, predictions,
                              label_list=list([0, 1, 2, 3, 4, 5, 6, 7]))

        #
        scores = self.model.evaluate_generator(test_generator)
        colorprint(Color.BLUE,
                   'Evaluator \nAcc (model)\nAccuracy: {} \nPrecision: {} \nRecall: {} \nFscore: {}'.
                   format(scores[1], evaluator.accuracy, evaluator.precision,
                          evaluator.recall,
                          evaluator.fscore) + '\n')
        cm = evaluator.confusion_matrix()

        # Plot the confusion matrix on test data
        colorprint(Color.BLUE, 'Confusion matrix:\n')
        colorprint(Color.BLUE, cm)
        print(cm)

        plt.matshow(cm)
        plt.title('Confusion matrix')
        plt.colorbar()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')
        plt.show()
        plt.savefig('cm.jpg')
        colorprint(Color.BLUE,
                   'Final accuracy: ' + str(evaluator.accuracy) + '\n')

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

    def cross_validate_SVM(self, features, train_labels):
        """ cross_validate classifier with k stratified folds """
        colorprint(Color.BLUE, 'Cross_validating the SVM classifier...\n')
        init = time.time()
        stdSlr = StandardScaler().fit(features)
        D_scaled = stdSlr.transform(features)
        kfolds = StratifiedKFold(n_splits=5, shuffle=False, random_state=50)

        parameters = {'kernel': ('linear', 'rbf'), 'C': [1, 10],
                      'gamma': np.linspace(0, 0.01, num=11)}
        grid = GridSearchCV(svm.SVC(), param_grid=parameters, cv=kfolds,
                            scoring='accuracy')
        grid.fit(D_scaled, train_labels)

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')
        colorprint(Color.BLUE, "Best parameters: %s Accuracy: %0.2f\n" % (
            grid.best_params_, grid.best_score_))

    def train_classifier_SVM(self, features, train_labels):
        # Train an SVM classifier
        colorprint(Color.BLUE, 'Training the SVM classifier...\n')
        init = time.time()
        self.stdSlr = StandardScaler().fit(features)
        D_scaled = self.stdSlr.transform(features)

        # Train an SVM classifier with RBF kernel
        # self.clf = svm.SVC(kernel='rbf', C=10, gamma=.002).fit(D_scaled,
        #                                                      train_labels)
        self.clf = svm.SVC(kernel='linear').fit(D_scaled, train_labels)
        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

    def evaluate_performance_SVM(self, features, test_labels, do_plotting):
        # Test the classification accuracy
        colorprint(Color.BLUE, 'Testing the SVM classifier...\n')
        init = time.time()
        test_data = self.stdSlr.transform(features)
        accuracy = 100 * self.clf.score(test_data, test_labels)

        predictions = self.clf.predict(test_data)
        evaluator = Evaluator(test_labels, predictions,
                              label_list=list([0, 1, 2, 3, 4, 5, 6, 7]))

        colorprint(Color.BLUE,
                   'Evaluator \nAccuracy: {} \nPrecision: {} \nRecall: {} \nFscore: {}'.
                   format(evaluator.accuracy, evaluator.precision,
                          evaluator.recall,
                          evaluator.fscore) + '\n')
        cm = evaluator.confusion_matrix()

        # Plot the confusion matrix on test data
        colorprint(Color.BLUE, 'Confusion matrix:\n')
        colorprint(Color.BLUE, cm)
        print(cm)
        if do_plotting:
            plt.matshow(cm)
            plt.title('Confusion matrix')
            plt.colorbar()
            plt.ylabel('True label')
            plt.xlabel('Predicted label')
            plt.show()
            plt.savefig('cm.jpg')

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')
        colorprint(Color.BLUE, 'Final accuracy: ' + str(accuracy) + '\n')

    def cross_validate_BoVW(self, features, train_labels):
        """ cross_validate classifier with k stratified folds """
        colorprint(Color.BLUE, 'Cross_validating the SVM classifier...\n')
        init = time.time()

        # Create BoVW classifier
        BoVW_classifier = BoVW(k=512)

        # rearenge feautures to a single array
        features = np.array(features)
        size_descriptors = features[0].shape[1]
        D = np.zeros(
            (np.sum([len(p) for p in features]), size_descriptors),
            dtype=np.uint8)
        startingpoint = 0
        for i in range(len(features)):
            D[startingpoint:startingpoint + len(features[i])] = \
                features[i]
            startingpoint += len(features[i])

        # Compute Codebook
        BoVW_classifier.compute_codebook(D)

        # get train visual word encoding
        visual_words = BoVW_classifier.get_train_encoding(features,
                                                          Keypoints=[])

        # Cross validate classifier
        BoVW_classifier.cross_validate(visual_words, train_labels)

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

    def train_classifier_BoVW(self, features, train_labels):
        # Train an BoVW classifier
        colorprint(Color.BLUE,
                   '[train_classifier_BoVW]: Training the classifier...\n')
        init = time.time()

        # Create BoVW classifier
        self.BoVW_classifier = BoVW(k=512)

        # rearrange features to a single array
        features = np.array(features)
        # print(features.shape)
        size_descriptors = features.shape[1]

        size_of_mini_batches = 64
        # print(int(size_descriptors / size_of_mini_batches))
        for i in range(int(size_descriptors / size_of_mini_batches)):
            size_of_batch_of_descriptors = features.shape[1]
            batch_of_features = features[
                                size_of_mini_batches * i:size_of_mini_batches * (
                                    i + 1)]
            print(batch_of_features.shape)
            print('D will be a {}x{} matrix of uint8'.format(
                np.sum([len(p) for p in batch_of_features]),
                size_of_batch_of_descriptors))

            # FIXME: fix loop to avoid this code
            # stop it when finish
            if np.sum([len(p) for p in batch_of_features]) == 0:
                break

            D = np.zeros(
                (np.sum([len(p) for p in batch_of_features]),
                 size_of_batch_of_descriptors),
                dtype=np.uint8)
            startingpoint = 0
            for i in range(len(batch_of_features)):
                D[startingpoint:startingpoint + len(batch_of_features[i])] = \
                    batch_of_features[i]
                startingpoint += len(batch_of_features[i])

            # Compute Codebook
            self.BoVW_classifier.compute_codebook_partial(D)

        self.BoVW_classifier.compute_codebook_partial(None, only_save=True)

        # get train visual word encoding
        visual_words = self.BoVW_classifier.get_train_encoding(features,
                                                               Keypoints=[])

        # Train an SVM classifier
        print("Problematic code here, the next shapes should match")
        print(visual_words.shape)
        print(train_labels.shape)
        self.BoVW_classifier.train_classifier(visual_words, train_labels)

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')

    def evaluate_performance_BoVW(self, features, test_labels, do_plotting):
        # Test the classification accuracy
        colorprint(Color.BLUE,
                   '[evaluate_performance_BOVW]: Testing the SVM classifier...\n')
        init = time.time()

        # get train visual word encoding
        features = np.array(features)
        visual_words_test = self.BoVW_classifier.get_train_encoding(features,
                                                                    Keypoints=[])

        # Test the classification accuracy
        self.BoVW_classifier.evaluate_performance(visual_words_test,
                                                  test_labels,
                                                  do_plotting, train_data=[])

        end = time.time()
        colorprint(Color.BLUE, 'Done in ' + str(end - init) + ' secs.\n')
