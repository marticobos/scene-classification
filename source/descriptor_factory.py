import os

import cv2
import numpy as np

from source import DATA_PATH


class Descriptor(object):
    pass


class SIFT(Descriptor):
    def __init__(self, number_of_features):
        # FIXME: remove number_of_features if they are not explicity needed
        self.number_of_features = number_of_features
        self.detector = cv2.SIFT(nfeatures=self.number_of_features)

    def detectAndCompute(self, gray):
        kpt, des = self.detector.detectAndCompute(gray, None)
        return kpt, des

    def generate(self, train_images, train_labels):
        ## type: (list, list) -> (np.array, np.array)
        """ Compute descriptors using SIFT

        Read the just 30 train images per class.
        Extract SIFT keypoints and descriptors.
        Store descriptors in a python list of numpy arrays.

        :rtype: tuple(list, list)
        :type train_images: list
        :type train_labels: list
        :param train_images: list of images
        :param train_labels: list of labels of the given images
        :return: descriptors and labels
        """
        train_descriptors = []
        train_label_per_descriptor = []

        for filename, train_label in zip(train_images, train_labels):
            filename_path = os.path.join(DATA_PATH, filename)
            if train_label_per_descriptor.count(train_label) < 30:
                print('Reading image ' + filename)
                ima = cv2.imread(filename_path)
                gray = cv2.cvtColor(ima, cv2.COLOR_BGR2GRAY)
                kpt, des = self.detectAndCompute(gray)
                train_descriptors.append(des)
                train_label_per_descriptor.append(train_label)
                print(str(len(kpt)) + ' extracted keypoints and descriptors')

        # Transform everything to numpy arrays

        descriptors = train_descriptors[0]
        labels = np.array(
            [train_label_per_descriptor[0]] * train_descriptors[0].shape[0])

        for i in range(1, len(train_descriptors)):
            descriptors = np.vstack((descriptors, train_descriptors[i]))
            labels = np.hstack((labels, np.array(
                [train_label_per_descriptor[i]] * train_descriptors[i].shape[
                    0])))

        return descriptors, labels