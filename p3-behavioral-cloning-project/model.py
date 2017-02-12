import tensorflow as tf
from keras.models import Sequential
from keras.layers.core import Dense, Flatten, Dropout, Lambda
from keras.layers.convolutional import Convolution2D
from keras.layers.advanced_activations import ELU
from keras.optimizers import Adam
import numpy as np
import cv2
import matplotlib.pyplot as plt
from pandas.io.parsers import read_csv
from keras.callbacks import EarlyStopping
tf.python.control_flow_ops = tf
from keras.callbacks import ModelCheckpoint
import matplotlib.gridspec as gridspec
import matplotlib.image as mpimg
import scipy.misc
import random

tf.python.control_flow_ops = tf

print('Modules loaded.')

"""
Hyperparemters
"""
# Nerual Network Training
BATCH_SIZE = 2  # BUG in batch size # 2 works to have accurate number of total samples
EPOCHS = 10
SAMPLES_EPOCH = 12000
VALIDATION_SAMPLES = 2000
LEARNING_RATE = .0001

# Recovery control
# Float, handled as absolute value, valid range from 0 -> 1
RECOVERY_OFFSET = .25

# Preprocessing
FEATURE_GENERATION_MULTIPLE = 2

# Data balancing
# .4 seems to work well
UNIFORM_TEST_MAX = .5  # Max absolute value of data balanced
ZEROS = .60  # Percent chance of getting zeros, higher chance of getting zeros
# NOTE as we add (+/-) for recover angles, the net number of zeros
# will be ~ ZEROS / 3 ie .5 zeros setting will result in ~.16

SEED = 8373
custom_random = np.random.RandomState(seed=SEED)
print(custom_random.randint(0, 100))  # Should return 91


"""
Test suite
"""

# run_once credit
# http://stackoverflow.com/questions/4103773/efficient-way-of-having-a-function-only-execute-once-in-a-loop


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


@run_once
def check_Shape(check_text, X_train, y_train):
    print(check_text, X_train.shape, y_train.shape)


"""
Pre processing pipeline
"""

track_angles = []

# credit
# https://medium.com/@vivek.yadav/improved-performance-of-deep-learning-neural-network-models-on-traffic-sign-classification-using-6355346da2dc#.llnuj74vg


def augment_brightness_camera_images(image):
    image = image.astype(np.uint8)
    image1 = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    random_bright = .25 + np.random.uniform()
    # print(random_bright)
    image1[:, :, 2] = image1[:, :, 2] * random_bright
    image1 = cv2.cvtColor(image1, cv2.COLOR_HSV2RGB)
    return image1


def transform_image(img, ang_range, shear_range, trans_range):
    '''
    This function transforms images to generate new images.
    The function takes in following arguments,
    1- Image
    2- ang_range: Range of angles for rotation
    3- shear_range: Range of values to apply affine transform to
    4- trans_range: Range of values to apply translations over.

    A Random uniform distribution is used to generate different parameters for transformation

    '''
    # Rotation
    ang_rot = np.random.uniform(ang_range) - ang_range / 2
    # updated to reflect gray pipeline
    rows, cols, ch = img.shape
    Rot_M = cv2.getRotationMatrix2D((cols / 2, rows / 2), ang_rot, 1)

    # Translation
    tr_x = trans_range * np.random.uniform() - trans_range / 2
    tr_y = trans_range * np.random.uniform() - trans_range / 2
    Trans_M = np.float32([[1, 0, tr_x], [0, 1, tr_y]])

    # Shear
    pts1 = np.float32([[5, 5], [20, 5], [5, 20]])

    pt1 = 5 + shear_range * np.random.uniform() - shear_range / 2
    pt2 = 20 + shear_range * np.random.uniform() - shear_range / 2

    pts2 = np.float32([[pt1, 5], [pt2, pt1], [5, pt2]])

    shear_M = cv2.getAffineTransform(pts1, pts2)

    img = cv2.warpAffine(img, Rot_M, (cols, rows))
    img = cv2.warpAffine(img, Trans_M, (cols, rows))
    img = cv2.warpAffine(img, shear_M, (cols, rows))

    # added for brightness
    img = augment_brightness_camera_images(img)

    return img


def balance_data(data):

    uniform_test_max = UNIFORM_TEST_MAX
    max_tries = 1
    zero_flag = False
    data_length = len(data)

    # Test if zeros are in line with other numbers
    if custom_random.random_sample(1) <= ZEROS:
        zero_flag = True

    while True:

        uniform_test = (custom_random.uniform(0, uniform_test_max))
        line_number = custom_random.randint(len(data))
        line = data[line_number]
        steering_angle = line[3]

        if zero_flag is True:
            if steering_angle == 0:
                return line
            else:
                continue
        else:
            # Handle non-zero angles
            if steering_angle != 0 and abs(steering_angle) <= uniform_test:
                return line
            else:  # Handle exceptions
                if max_tries > data_length:
                    print("Exceeded search time, skipping angle:",
                          steering_angle, "Data length:", data_length)
                    return line
                else:
                    continue


def recovery(line):

    y_train = np.empty([0, 1])
    y_single_sample = line[3]
    y_single_sample = round(y_single_sample, 3)
    # print(y_single_sample)
    assert type(y_single_sample) == float
    # print(type(y_single_sample))
    new_labels = []

    for i in range(3):

        if i == 1:  # left are negative angles, positive to return to center
            # print("Left", line[i])   #Refactor to an ASSERT
            steering_adjust = +RECOVERY_OFFSET  # normally .25
            # print(type(steering_adjust))
            steering_correction = min(
                1, y_single_sample + steering_adjust)
            assert steering_correction != 1.01, steering_correction != -1
            # print(steering_correction)
        elif i == 2:  # right
            # print("Right", line[i])
            steering_adjust = -RECOVERY_OFFSET
            steering_correction = max(-1,
                                      y_single_sample + steering_adjust)
            assert steering_correction != -1.01, steering_correction != +1
        elif i == 0:
            # print("Center", line[i])
            steering_correction = y_single_sample

        track_angles.append(steering_correction)
        new_labels.append([steering_correction])

    # print("new labels", new_labels)
    y_train = np.append(y_train, new_labels, axis=0)
    # print(y_train)

    return y_train


def chop_images(line):

    X_train = np.empty([0, 80, 320, 3])

    for i in range(3):

        imgname = line[i].strip()
        X_single_sample = cv2.imread(imgname)
        # print("X original  shape", X_single_sample.shape)
        top = int(.4 * X_single_sample.shape[0])
        bottom = int(.1 * X_single_sample.shape[0])
        X_single_sample = X_single_sample[top:-bottom, :]
        # print("X new shape", X_single_sample.shape)
        # save images for visualization if required
        # scipy.misc.imsave(
        # 'figs/orginal' + str(np.random.randint(999)) + '.jpg', X_single_sample)
        X_train = np.append(X_train, [X_single_sample], axis=0)

    return X_train


def adjust_colours(X_train):

    for feature in X_train:

        feature = feature.astype(np.uint8)  # fix error 215
        feature = cv2.cvtColor(feature, cv2.COLOR_BGR2RGB)
        # scipy.misc.imsave(
        #'figs2/adjust-colours' + str(np.random.randint(10000)) + '.jpg', feature)

    return X_train


def flip_images(X_train, y_train):

    for feature in X_train:
        feature = np.fliplr(feature)

    for angle in y_train:
        angle = -angle

    return X_train, y_train


def generate_features(X_train, y_train):

    new_features = []
    new_labels = []

    for i in range(FEATURE_GENERATION_MULTIPLE):

        for feature in X_train:
            feature = transform_image(feature, 10, 2, 2)

            # credit https://github.com/navoshta/behavioral-cloning
            # switched to used custom random function
            # Adding shadows
            h, w = feature.shape[0], feature.shape[1]
            [x1, x2] = custom_random.choice(w, 2, replace=False)
            k = h / (x2 - x1)
            b = - k * x1
            for j in range(h):
                c = int((j - b) / k)
                feature[j, :c, :] = (feature[j, :c, :] * .5).astype(np.int32)

            # scipy.misc.imsave('figs2/gen-features' + str(np.random.randint(10000)) + '.jpg', feature)
            new_features.append(feature)

        for label in y_train:
            new_labels.append(label)
            track_angles.append(label)

    X_train = np.append(X_train, new_features, axis=0)
    y_train = np.append(y_train, new_labels, axis=0)

    return X_train, y_train


def process_line(data):

    balanced_line = balance_data(data)
    X_train = chop_images(balanced_line)
    X_train = adjust_colours(X_train)
    y_train = recovery(balanced_line)

    if custom_random.random_sample(1) <= .5:
        flip_images(X_train, y_train)
    # Check_text = "After image generation, shapes: "
    # check_Shape(Check_text, X_train, y_train)

    return X_train, y_train


def generate_arrays_from_file(path):
    batch_tracker = 0
    while 1:
        for batch in range(BATCH_SIZE):
            # load the labels and file paths to images
            data = read_csv(path).values
            X_train, y_train = process_line(data)
            X_train, y_train = generate_features(X_train, y_train)

            X_train = np.append(X_train, X_train, axis=0)
            y_train = np.append(y_train, y_train, axis=0)

        # print(batch_tracker)
        batch_tracker = batch_tracker + 1

        Check_text = "Batch shape: "
        check_Shape(Check_text, X_train, y_train)

        yield X_train, y_train


"""
Model architecture
"""
init_type = "glorot_uniform"
border_mode_type = "valid"

row, col, ch = 80, 320, 3
model = Sequential()
model.add(Lambda(lambda X_train: X_train / 127.5 - 1,
                 input_shape=(row, col, ch),
                 output_shape=(row, col, ch)))


model.add(Convolution2D(24, 5, 5,
                        subsample=(2, 2),
                        border_mode=border_mode_type,
                        init=init_type))
# convout1 = ELU()
model.add(ELU())

model.add(Convolution2D(36, 5, 5,
                        subsample=(2, 2),
                        border_mode=border_mode_type,
                        init=init_type))
model.add(ELU())

model.add(Convolution2D(48, 5, 5,
                        subsample=(2, 2),
                        border_mode=border_mode_type,
                        init=init_type))
model.add(ELU())

model.add(Convolution2D(64, 3, 3,
                        subsample=(2, 2),
                        border_mode=border_mode_type,
                        init=init_type))
model.add(ELU())

model.add(Convolution2D(64, 3, 3,
                        subsample=(2, 2),
                        border_mode=border_mode_type,
                        init=init_type))
model.add(ELU())

model.add(Flatten())

model.add(Dense(1164, init=init_type))
model.add(ELU())

model.add(Dense(100, init=init_type))
model.add(ELU())

model.add(Dense(50, init=init_type))
model.add(ELU())

model.add(Dense(10, init=init_type))
model.add(ELU())

model.add(Dense(1))


optimizer_settings = Adam(lr=LEARNING_RATE)
model.compile(optimizer=optimizer_settings, loss='mse')

early_stopping = EarlyStopping(monitor='val_loss', patience=2)

checkpointer = ModelCheckpoint(
    filepath="temp-model/weights.hdf5", verbose=1, save_best_only=True)

"""
Train architecture
"""

if __name__ == "__main__":

    print("Training")

    '''
    saves the model weights after each epoch if the validation loss decreased
    Credit https://keras.io/callbacks/#create-a-callback
    '''

    history = model.fit_generator(
        generate_arrays_from_file('driving_log.csv'),
        samples_per_epoch=SAMPLES_EPOCH, nb_epoch=EPOCHS, verbose=2,
        callbacks=[early_stopping, checkpointer],
        validation_data=generate_arrays_from_file('validation_log2.csv'),
        nb_val_samples=VALIDATION_SAMPLES)

    """
    Save model
    """
    model.save('my_model.h5')

    print("Model saved.")

    model.summary()
    print("Complete.")

    # model.predict()
    # summarize history for loss
    plt_number = custom_random.randint(0, 10000)

    """
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    fig2 = plt.gcf()
    plt.show()
    fig2.savefig('testing-figures/loss-history' + str(plt_number) + '.png')
    """

    # print(track_angles)
    track_angles = np.asarray(track_angles)
    # print("Negative angles:", np.where(track_angles>0).shape)
    print("Length of track angles: ", len(track_angles))

    plt.hist(track_angles, bins='auto')
    plt.title("Gaussian Histogram")
    plt.xlabel("Value")
    plt.ylabel("Frequency")

    fig = plt.gcf()
    plt.show()
    fig.savefig('testing-figures/angle-histogram' + str(plt_number) + '.png')

    print(min(track_angles))
    print(max(track_angles))

    non_zero_count = (np.count_nonzero(track_angles))
    zeros_counter = len(track_angles) - non_zero_count

    np_unique_angles, np_unique_counts = np.unique(
        track_angles, return_counts=True)

    # for angle in np_unique_angles:
    # print(angle, np_unique_counts[angle])

    print("Non zero angles:", non_zero_count)
    print("Number of zeros: ", zeros_counter)
    print("Percent zero angle", zeros_counter / len(track_angles))
    print("Number of original zeros (Before Recovery +/-): ", zeros_counter * 3)
    print("Unique angles, non recovery:", len(np.unique(track_angles)) / 3)

    print("Non zero, non recovery angles:", len(
        track_angles) - zeros_counter * 3)

    print(np_unique_angles, np_unique_counts)

    plt.hist(np.unique(track_angles), bins='auto')
    plt.title("Gaussian Histogram")
    plt.xlabel("Value")
    plt.ylabel("Frequency")

    fig = plt.gcf()
    plt.show()
    fig.savefig('testing-figures/unique-angles-histogram' +
                str(plt_number) + '.png')

    # balance_bins(track_angles)
