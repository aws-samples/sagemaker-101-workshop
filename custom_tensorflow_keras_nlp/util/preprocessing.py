from __future__ import division

# Python Built-Ins:
import os
import re
import shutil
import subprocess
import zipfile

# External Dependencies:
import numpy as np
from sklearn import preprocessing
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical

def download_dataset():
    os.makedirs("data", exist_ok=True)
    print("Downloading data...")
    subprocess.call(
        ["wget -O data/NewsAggregatorDataset.zip https://archive.ics.uci.edu/ml/machine-learning-databases/00359/NewsAggregatorDataset.zip"],
        shell=True,
    )
    
    with zipfile.ZipFile("data/NewsAggregatorDataset.zip", 'r') as zip_ref:
        print("Unzipping...")
        zip_ref.extractall("data")
    try:
        # Clean up the noise in the folder, don't care too much if it fails:
        shutil.rmtree("data/__MACOSX/")
    except:
        pass
    print("Saved to data/ folder")

def dummy_encode_labels(df,label):
    encoder = preprocessing.LabelEncoder()
    encoded_y=encoder.fit_transform(df[label].values)
    # convert integers to dummy variables (i.e. one hot encoded)
    dummy_y = to_categorical(encoded_y)
    return dummy_y, encoder.classes_

def tokenize_pad_docs(df,columns):
    docs = df[columns].values
    # prepare tokenizer
    t = Tokenizer()
    t.fit_on_texts(docs)
    vocab_size = len(t.word_index) + 1
    # integer encode the documents
    encoded_docs = t.texts_to_sequences(docs)
    print(f"Vocabulary size: {vocab_size}")
    # pad documents to a max length of 4 words
    max_length = 40
    padded_docs = pad_sequences(encoded_docs, maxlen=max_length, padding="post")
    print(f"Number of headlines: {len(padded_docs)}")
    return padded_docs, t

def get_word_embeddings(t, folder):
    os.makedirs(folder, exist_ok=True)
    if os.path.isfile(f"{folder}/glove.6B.100d.txt"):
        print("Using existing embeddings file")
    else:
        print("Downloading Glove word embeddings...")
        subprocess.call(
            [f"wget -O {folder}/glove.6B.zip http://nlp.stanford.edu/data/glove.6B.zip"],
            shell=True,
        )
        with zipfile.ZipFile(f"{folder}/glove.6B.zip", "r") as zip_ref:
            print("Unzipping...")
            zip_ref.extractall(folder)

        try:
            # Remove unnecessary files, don't mind too much if fails:
            for name in ["glove.6B.200d.txt", "glove.6B.50d.txt", "glove.6B.300d.txt", "glove.6B.zip"]:
                os.remove(os.path.join(folder, name))
        except:
            pass

    print("Loading into memory...")
    # load the whole embedding into memory
    embeddings_index = dict()
    with open(f"{folder}/glove.6B.100d.txt", "r", encoding="utf-8") as f:
        for line in f:
            values = line.split()
            word = values[0]
            coefs = np.asarray(values[1:], dtype="float32")
            embeddings_index[word] = coefs
    vocab_size = len(embeddings_index)
    print(f"Loaded {vocab_size} word vectors.")

    # create a weight matrix for words in training docs
    embedding_matrix = np.zeros((vocab_size, 100))
    for word, i in t.word_index.items():
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector

    return embedding_matrix
