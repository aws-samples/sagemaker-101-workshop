from __future__ import division

# Python Built-Ins:
import gzip
import os
import shutil
import subprocess
import tarfile
import time
from typing import Optional

# External Dependencies:
import numpy as np
from sklearn import preprocessing
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences


def wait_for_file_stable(path: str, stable_secs: int=60, poll_secs: Optional[int]=None) -> bool:
    """Wait for a file to become stable (not recently modified) & return existence

    Returns False if file does not exist. Raises FileNotFoundError if file deleted during polling.

    When running through the two notebooks at the same time in parallel, this helps to minimize any
    errors caused by initiating multiple downloads/extractions/etc on the same file in parallel.
    """
    if not poll_secs:
        poll_secs = stable_secs / 4
    try:
        init_stat = os.stat(path)
    except FileNotFoundError:
        return False

    if (time.time() - init_stat.st_mtime) < stable_secs:
        print(f"Waiting for file to stabilize... {path}")
        while (time.time() - os.stat(path).st_mtime) < stable_secs:
            time.sleep(poll_secs)
        print("File ready")

    return True


def dummy_encode_labels(df,label):
    encoder = preprocessing.LabelEncoder()
    encoded_y = encoder.fit_transform(df[label].values)
    num_classes = len(encoder.classes_)
    # convert integers to dummy variables (i.e. one hot encoded)
    dummy_y = np.eye(num_classes, dtype="float32")[encoded_y]
    return dummy_y, encoder.classes_


def tokenize_and_pad_docs(df, columns, max_length=40):
    docs = df[columns].values
    # prepare tokenizer
    t = Tokenizer()
    t.fit_on_texts(docs)
    vocab_size = len(t.word_index) + 1
    # integer encode the documents
    encoded_docs = t.texts_to_sequences(docs)
    print(f"Vocabulary size: {vocab_size}")
    print("Padding docs to max_length={} (truncating {} docs)".format(
        max_length,
        sum(1 for doc in encoded_docs if len(doc) > max_length),
    ))
    padded_docs = pad_sequences(encoded_docs, maxlen=max_length, padding="post")
    print(f"Number of headlines: {len(padded_docs)}")
    return padded_docs, t


def get_word_embeddings(t, folder, lang="en"):
    """Download pre-trained word vectors and construct an embedding matrix for tokenizer `t`

    Any tokens in `t` not found in the embedding vectors are mapped to all-zeros.
    """
    vecs_url = f"https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.{lang}.300.vec.gz"
    vecs_gz_filename = vecs_url.rpartition("/")[2]
    os.makedirs(folder, exist_ok=True)
    vecs_gz_filepath = os.path.join(folder, vecs_gz_filename)

    # Tokenizer.num_words is nullable, and there's an OOV token, so:
    tokenizer_vocab_size = len(t.word_index) + 1

    if wait_for_file_stable(vecs_gz_filepath):
        print("Using existing embeddings file")
    else:
        print("Downloading word vectors...")
        subprocess.run([" ".join(["wget", "-NP", folder, vecs_url])], check=True, shell=True)

    print("Loading into memory...")
    embeddings_index = dict()
    with gzip.open(vecs_gz_filepath, "rt") as zipf:
        firstline = zipf.readline()
        emb_vocab_size, emb_d = firstline.split(" ")
        emb_vocab_size = int(emb_vocab_size)
        emb_d = int(emb_d)
        for line in zipf:
            values = line.split()
            word = values[0]
            # Only load subset of the embeddings recognised by the tokenizer:
            if word in t.word_index:
                coefs = np.asarray(values[1:], dtype="float32")
                embeddings_index[word] = coefs
    print("Loaded {} of {} word vectors for tokenizer vocabulary length {}".format(
        len(embeddings_index),
        emb_vocab_size,
        tokenizer_vocab_size,
    ))

    # create a weight matrix for words in training docs
    embedding_matrix = np.zeros((tokenizer_vocab_size, emb_d))
    for word, i in t.word_index.items():
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector

    return embedding_matrix
