"""CNN-based image classification on SageMaker with TensorFlow and Keras

REFERENCE SOLUTION IMPLEMENTATION

(Complete me with help from Local Notebook.ipynb, and the NLP example's src/main.py!)
"""

# Dependencies:
import argparse
import os

import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras import backend as K
from tensorflow.keras.layers import Conv2D, Dense, Dropout, Flatten, MaxPooling2D
from tensorflow.keras.models import Sequential

def parse_args():
    """Acquire hyperparameters and directory locations passed by SageMaker"""
    parser = argparse.ArgumentParser()

    # Hyperparameters sent by the client are passed as command-line arguments to the script.
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=128)

    # Data, model, and output directories
    parser.add_argument("--output-data-dir", type=str, default=os.environ.get("SM_OUTPUT_DATA_DIR"))
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN"))
    parser.add_argument("--test", type=str, default=os.environ.get("SM_CHANNEL_TEST"))

    return parser.parse_known_args()

# TODO: Other function definitions, if you'd like to break up your code into functions?

def load_data(args):
    labels = sorted(os.listdir(args.train))
    n_labels = len(labels)
    x_train = []
    y_train = []
    x_test = []
    y_test = []
    print("Loading label ", end="")
    for ix_label in range(n_labels):
        label_str = labels[ix_label]
        print(f"{label_str}...", end="")
        trainfiles = filter(
            lambda s: s.endswith(".png"),
            os.listdir(os.path.join(args.train, label_str))
        )
        for filename in trainfiles:
            # Can't just use tf.keras.preprocessing.image.load_img(), because it doesn't close its
            # file handles! So get "Too many open files" error... Grr
            with open(os.path.join(args.train, label_str, filename), "rb") as imgfile:
                x_train.append(
                    # Squeeze (drop) that extra channel dimension, to be consistent with prev
                    # format:
                    np.squeeze(tf.keras.preprocessing.image.img_to_array(
                        Image.open(imgfile)
                    ))
                )
                y_train.append(ix_label)
        # Repeat for test data:
        testfiles = filter(
            lambda s: s.endswith(".png"),
            os.listdir(os.path.join(args.test, label_str))
        )
        for filename in testfiles:
            with open(os.path.join(args.test, label_str, filename), "rb") as imgfile:
                x_test.append(
                    np.squeeze(tf.keras.preprocessing.image.img_to_array(
                        Image.open(imgfile)
                    ))
                )
                y_test.append(ix_label)
    print("Shuffling trainset...")
    train_shuffled = [(x_train[ix], y_train[ix]) for ix in range(len(y_train))]
    np.random.shuffle(train_shuffled)

    x_train = np.array([datum[0] for datum in train_shuffled])
    y_train = np.array([datum[1] for datum in train_shuffled])
    train_shuffled = None

    print("Shuffling testset...")
    test_shuffled = [(x_test[ix], y_test[ix]) for ix in range(len(y_test))]
    np.random.shuffle(test_shuffled)

    x_test = np.array([datum[0] for datum in test_shuffled])
    y_test = np.array([datum[1] for datum in test_shuffled])
    test_shuffled = None

    if K.image_data_format() == "channels_first":
        x_train = np.expand_dims(x_train, 1)
        x_test = np.expand_dims(x_train, 1)
    else:
        x_train = np.expand_dims(x_train, len(x_train.shape))
        x_test = np.expand_dims(x_test, len(x_test.shape))

    x_train = x_train.astype("float32")
    x_test = x_test.astype("float32")
    x_train /= 255
    x_test /= 255

    input_shape = x_train.shape[1:]

    print("x_train shape:", x_train.shape)
    print("input_shape:", input_shape)
    print(x_train.shape[0], "train samples")
    print(x_test.shape[0], "test samples")

    # convert class vectors to binary class matrices
    y_train = tf.keras.utils.to_categorical(y_train, n_labels)
    y_test = tf.keras.utils.to_categorical(y_test, n_labels)

    print("n_labels:", n_labels)
    print("y_train shape:", y_train.shape)

    return x_train, y_train, x_test, y_test, input_shape, n_labels

def build_model(input_shape, n_labels):
    model = Sequential()
    model.add(Conv2D(32, kernel_size=(3, 3), activation="relu", input_shape=input_shape))
    model.add(Conv2D(64, (3, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Dense(128, activation="relu"))
    model.add(Dropout(0.5))
    model.add(Dense(n_labels, activation="softmax"))

    model.compile(
        loss=tf.keras.losses.categorical_crossentropy,
        optimizer=tf.keras.optimizers.Adadelta(),
        metrics=["accuracy"]
    )

    return model

# Training script:
if __name__ == "__main__":
    # Load arguments from CLI / environment variables:
    args, _ = parse_args()
    print(args)

    # TODO: Load images from container filesystem into training / test data sets?
    x_train, y_train, x_test, y_test, input_shape, n_labels = load_data(args)

    # TODO: Create the Keras model?
    model = build_model(input_shape, n_labels)

    # Fit the Keras model:
    model.fit(
        x_train, y_train,
        batch_size=args.batch_size,
        epochs=args.epochs,
        shuffle=True,
        verbose=2, # Hint: You might prefer =2 for running in SageMaker!
        validation_data=(x_test, y_test)
    )

    # TODO: Evaluate model quality and log metrics?
    score = model.evaluate(x_test, y_test, verbose=0)
    print(f"Test loss: {score[0]}")
    print(f"Test accuracy: {score[1]}")

    # TODO: Save outputs (trained model) to specified folder?
    sess = K.get_session()
    tf.saved_model.simple_save(
        sess,
        os.path.join(args.model_dir, "model/1"),
        inputs={ "inputs": model.input },
        outputs={ t.name: t for t in model.outputs },
    )
