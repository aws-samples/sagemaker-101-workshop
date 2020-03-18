# Python Built-Ins:
import argparse
import os

# External Dependencies:
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Conv1D, Dense, Dropout, Embedding, Flatten, MaxPooling1D
from tensorflow.keras.models import Sequential


def load_training_data(base_dir):
    X_train = np.load(os.path.join(base_dir, "train_X.npy"))
    y_train = np.load(os.path.join(base_dir, "train_Y.npy"))
    return X_train, y_train

def load_testing_data(base_dir):
    X_test = np.load(os.path.join(base_dir, "test_X.npy"))
    y_test = np.load(os.path.join(base_dir, "test_Y.npy"))
    return X_test, y_test

def load_embeddings(base_dir):
    embedding_matrix = np.load(os.path.join(base_dir, "docs-embedding-matrix.npy"))
    return embedding_matrix

def parse_args():
    """Acquire hyperparameters and directory locations passed by SageMaker"""
    parser = argparse.ArgumentParser()

    # Hyperparameters sent by the client are passed as command-line arguments to the script.
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning_rate", type=float, default=0.001)
    parser.add_argument("--num_classes", type=int, default=4)
    parser.add_argument("--vocab_size", type=int, default=300)

    # Data, model, and output directories
    parser.add_argument("--output-data-dir", type=str, default=os.environ["SM_OUTPUT_DATA_DIR"])
    parser.add_argument("--model-dir", type=str, default=os.environ["SM_MODEL_DIR"])
    parser.add_argument("--train", type=str, default=os.environ["SM_CHANNEL_TRAIN"])
    parser.add_argument("--test", type=str, default=os.environ["SM_CHANNEL_TEST"])
    parser.add_argument("--embeddings", type=str, default=os.environ["SM_CHANNEL_EMBEDDINGS"])

    return parser.parse_known_args()

if __name__ == "__main__":
    args, unknown = parse_args()
    print(args)

    X_train, y_train = load_training_data(args.train)
    X_test, y_test = load_testing_data(args.test)
    embedding_matrix = load_embeddings(args.embeddings)

    model = Sequential()
    model.add(Embedding(
        args.vocab_size,
        100,
        weights=[embedding_matrix],
        input_length=40,
        trainable=False,
        name="embed",
    ))
    model.add(Conv1D(filters=128, kernel_size=3, activation="relu", name="conv_1"))
    model.add(MaxPooling1D(pool_size=5, name="maxpool_1"))
    model.add(Flatten(name="flat_1"))
    model.add(Dropout(0.3, name="dropout_1"))
    model.add(Dense(128, activation="relu", name="dense_1"))
    model.add(Dense(args.num_classes, activation="softmax", name="out_1"))

    # compile the model
    optimizer = tf.keras.optimizers.RMSprop(learning_rate=args.learning_rate)
    model.compile(optimizer=optimizer, loss="binary_crossentropy", metrics=["acc"])

    model.summary()

    print("Training model")
    model.fit(X_train, y_train, batch_size=16, epochs=args.epochs, verbose=2)
    print("Evaluating model")
    # TODO: Better differentiate train vs val loss in logs
    scores = model.evaluate(X_test, y_test, verbose=2)
    print(
        "Validation results: "
        + "; ".join(map(
            lambda i: f"{model.metrics_names[i]}={scores[i]:.5f}", range(len(model.metrics_names))
        ))
    )

    print(f"------ save model to {os.path.join(args.model_dir, 'model/1/')}")
    # save Keras model for Tensorflow Serving
    sess = tf.keras.backend.get_session()
    tf.saved_model.simple_save(
        sess,
        os.path.join(args.model_dir, "model/1"),
        inputs={ "inputs": model.input },
        outputs={ t.name: t for t in model.outputs },
    )
