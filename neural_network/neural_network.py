from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from imutils import paths
import numpy as np
import imutils
import cv2
import os


def image_to_feature_vector(image, size=(32, 32)):
    # resize the image to a fixed size, then flatten the image into
    # a list of raw pixel intensities
    return cv2.resize(image, size).flatten()


def extract_color_histogram(image, bins=(8, 8, 8)):
    # extract a 3D color histogram from the HSV color space using
    # the supplied number of `bins` per channel
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1, 2], None, bins,
                        [0, 180, 0, 256, 0, 256])

    # handle normalizing the histogram if we are using OpenCV 2.4.X
    if imutils.is_cv2():
        hist = cv2.normalize(hist)

    # otherwise, perform "in place" normalization in OpenCV 3
    else:
        cv2.normalize(hist, hist)

    # return the flattened histogram as the feature vector
    return hist.flatten()


DATA_SET_PATH = '../training_images'
# grab the list of images that we'll be describing
print("[INFO] describing images...")
imagePaths = list(paths.list_images(DATA_SET_PATH))

# initialize the raw pixel intensities matrix, the features matrix,
# and labels list
rawImages = []
features = []
labels = []

# loop over the input images
for (i, imagePath) in enumerate(imagePaths):
    # load the image and extract the class label (assuming that our
    # path as the format: /path/to/dataset/{class}.{image_num}.jpg
    image = cv2.imread(imagePath)
    label = imagePath.split(os.path.sep)[-2].split(".")[1]

    # extract raw pixel intensity "features", followed by a color
    # histogram to characterize the color distribution of the pixels
    # in the image
    pixels = image_to_feature_vector(image)
    hist = extract_color_histogram(image)

    # update the raw images, features, and labels matricies,
    # respectively
    rawImages.append(pixels)
    labels.append(label)
    features.append(hist)

    # show an update every 1,000 images
    if i > 0 and i % 1000 == 0:
        print("[INFO] processed {}/{}".format(i, len(imagePaths)))

# show some information on the memory consumed by the raw images
# matrix and features matrix
rawImages = np.array(rawImages)
features = np.array(features)
labels = np.array(labels)
print("[INFO] pixels matrix: {:.2f}MB".format(
    rawImages.nbytes / (1024 * 1000.0)))

# partition the data into training and testing splits, using 75%
# of the data for training and the remaining 25% for testing
(trainRI, testRI, trainRL, testRL) = train_test_split(
    rawImages, labels, test_size=0.15, random_state=42)

(trainFeat, testFeat, trainLabels, testLabels) = train_test_split(
    features, labels, test_size=0.15, random_state=42)

# train and evaluate a k-NN classifer on the raw pixel intensities
print("[INFO] evaluating raw pixel accuracy...")
parameters = {'activation': ('identity', 'logistic', 'tanh', 'relu'),
              'hidden_layer_sizes': [(100,), (500,), (1000,), (2000,)]}

model = MLPClassifier(max_iter=1000)
clf = GridSearchCV(model, parameters, cv=5)
clf.fit(trainFeat, trainLabels)
acc = clf.score(testFeat, testLabels)
print("[INFO] raw pixel accuracy: {:.2f}%".format(acc * 100))
print(clf.best_estimator_, '\n')
print(clf.best_score_, '\n')
print(clf.best_params_, '\n')
