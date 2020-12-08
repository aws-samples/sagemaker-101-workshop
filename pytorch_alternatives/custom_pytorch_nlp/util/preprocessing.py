from __future__ import division

# Python Built-Ins:
import os
import re
import subprocess
import functools
import operator
from collections import Counter

# External Dependencies:
import numpy as np
import torchtext
from sklearn import preprocessing

def to_categorical(y, num_classes):
    """ 1-hot encodes a tensor """
    return np.eye(num_classes, dtype='float32')[y]

def download_dataset():
    os.makedirs("data", exist_ok=True)
    print("Downloading data...")
    subprocess.call(
        ["wget -O data/NewsAggregatorDataset.zip https://archive.ics.uci.edu/ml/machine-learning-databases/00359/NewsAggregatorDataset.zip"],
        shell=True,
    )
    subprocess.call(["unzip -o data/NewsAggregatorDataset.zip -d data"], shell=True)
    subprocess.call(["rm -rf data/__MACOSX/"], shell=True)
    print("Saved to data/ folder")

def dummy_encode_labels(df,label):
    encoder = preprocessing.LabelEncoder()
    encoded_y=encoder.fit_transform(df[label].values)
    # convert integers to dummy variables (i.e. one hot encoded)
    dummy_y = to_categorical(encoded_y, len(encoder.classes_))
    return dummy_y, encoder.classes_

def tokenize_and_pad_docs(df,columns):
    docs = df[columns].values
    # pad documents to a max length of 10 words
    max_length = 40
    
    t = torchtext.data.Field(
      lower       = True,
      tokenize   = "basic_english",
      fix_length  = max_length
    )
    docs = list(map(t.preprocess, docs))
    padded_docs = t.pad(docs)
    t.build_vocab(padded_docs)
    numericalized_docs = []
    for d in padded_docs:
        temp = []
        for c in d:
            temp.append(t.vocab.stoi[c])
        numericalized_docs.append(temp)
    return np.array(numericalized_docs), t

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
        print("Unzipping...")
        subprocess.call([f"unzip -o {folder}/glove.6B.zip -d {folder}"], shell=True)

        subprocess.call(
            [
                f"rm {folder}/glove.6B.200d.txt {folder}/glove.6B.50d.txt "
                f"{folder}/glove.6B.300d.txt {folder}/glove.6B.zip"
            ],
            shell=True
        )

    print("Loading into memory...")
    # load the whole embedding into memory
    embeddings_index = dict()
    with open(f"{folder}/glove.6B.100d.txt", "r") as f:
        for line in f:
            values = line.split()
            word = values[0]
            coefs = np.asarray(values[1:], dtype="float32")
            embeddings_index[word] = coefs
    vocab_size = len(embeddings_index)
    print(f"Loaded {vocab_size} word vectors.")

    # create a weight matrix for words in training docs
    embedding_matrix = np.zeros((vocab_size, 100))
    i = 0
    for word in t.vocab.itos:
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector
        i = i+1

    return embedding_matrix
