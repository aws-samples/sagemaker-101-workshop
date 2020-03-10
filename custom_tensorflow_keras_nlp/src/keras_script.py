import tensorflow as tf
import argparse
import os
import numpy as np
import sys
from keras.wrappers.scikit_learn import KerasClassifier
from keras.utils import np_utils
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline

from tensorflow import keras
from tensorflow.keras import layers

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Dropout
from tensorflow.keras.layers import Conv1D, MaxPooling1D
from tensorflow.keras.layers import Embedding


def load_training_data(base_dir):
    X_train = np.load(os.path.join(base_dir, 'train_X.npy'))
    y_train = np.load(os.path.join(base_dir, 'train_Y.npy'))
    return X_train, y_train

def load_testing_data(base_dir):
    X_test = np.load(os.path.join(base_dir, 'test_X.npy'))
    y_test = np.load(os.path.join(base_dir, 'test_Y.npy'))
    return X_test, y_test

def load_embeddings(base_dir):
    embedding_matrix = np.load( os.path.join(base_dir, 'docs-embedding-matrix.npy'))
    return embedding_matrix
# Acquire hyperparameters and directory locations passed by SageMaker
def parse_args():
    parser = argparse.ArgumentParser()

    # hyperparameters sent by the client are passed as command-line arguments to the script.
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--vocab_size', type=int, default=300)
    parser.add_argument('--num_classes', type=int, default=4)
    
    # Data, model, and output directories
    parser.add_argument('--output-data-dir', type=str, default=os.environ['SM_OUTPUT_DATA_DIR'])
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--train', type=str, default=os.environ['SM_CHANNEL_TRAIN'])
    parser.add_argument('--test', type=str, default=os.environ['SM_CHANNEL_TEST'])
    parser.add_argument('--embeddings', type=str, default=os.environ['SM_CHANNEL_EMBEDDINGS'])
    
    return parser.parse_known_args()

if __name__ == "__main__":
    
    args, unknown = parse_args()
    
    print(args)

    x_train, y_train = load_training_data(args.train)
    x_test, y_test = load_testing_data(args.test)
    embedding_matrix=load_embeddings(args.embeddings)
    
    model = Sequential()
    model.add(Embedding(args.vocab_size, 100, 
                            weights=[embedding_matrix],
                            input_length=40, 
                            trainable=False, 
                            name="embed"))
    model.add(Conv1D(filters=128, 
                         kernel_size=3, 
                         activation='relu',
                         name="conv_1"))
    model.add(MaxPooling1D(pool_size=5,
                               name="maxpool_1"))
    model.add(Flatten(name="flat_1"))
    model.add(Dropout(0.3,
                         name="dropout_1"))
    model.add(Dense(128, 
                        activation='relu',
                        name="dense_1"))
    model.add(Dense(args.num_classes,
                        activation='softmax',
                        name="out_1"))

        # compile the model
    model.compile(optimizer='rmsprop',
                      loss='binary_crossentropy',
                      metrics=['acc'])


    model.summary()


    model.fit(x_train, y_train, batch_size=16, epochs=args.epochs, verbose=2)
    model.evaluate(x_test, y_test, verbose=2)
    print('------ save model to {}'.format(os.path.join(args.model_dir, 'model/1/')))
    # save Keras model for Tensorflow Serving
    sess = tf.keras.backend.get_session()
    tf.saved_model.simple_save(
        sess,
        os.path.join(args.model_dir, 'model/1'),
        inputs={'inputs': model.input},
        outputs={t.name: t for t in model.outputs})
    
    