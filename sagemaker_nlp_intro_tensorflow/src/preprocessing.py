from __future__ import division

import pandas as pd
import tensorflow as tf
import re
import numpy as np
import os
import subprocess
import shlex

from sklearn import preprocessing
from keras.utils.np_utils import to_categorical

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

def download_dataset():
    subprocess.call(["wget https://archive.ics.uci.edu/ml/machine-learning-databases/00359/NewsAggregatorDataset.zip"],shell=True)
    subprocess.call(["echo y| unzip NewsAggregatorDataset.zip"],shell=True)
    subprocess.call(["rm -rf __MACOSX/"],shell=True)

def dummy_encode_labels(df,label):    
    
    encoder = preprocessing.LabelEncoder()
    encoded_y=encoder.fit_transform(df[label].values)
    # convert integers to dummy variables (i.e. one hot encoded)
    dummy_y = to_categorical(encoded_y)
    return dummy_y

def tokenize_pad_docs(df,columns):
    docs = df[columns].values
    # prepare tokenizer
    t = Tokenizer()
    t.fit_on_texts(docs)
    vocab_size = len(t.word_index) + 1
    # integer encode the documents
    encoded_docs = t.texts_to_sequences(docs)
    print("Vocabulary size: " + str(vocab_size))
    # pad documents to a max length of 4 words
    max_length = 40
    padded_docs = pad_sequences(encoded_docs, maxlen=max_length, padding='post')
    print("Number of headlines: " + str(len(padded_docs)))
    return padded_docs, t

def run_command(command):
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print output.strip()
    rc = process.poll()
    return rc

def get_word_embeddings(t):
    #download public embeddings
    #run_command("wget http://nlp.stanford.edu/data/glove.6B.zip && unzip glove.6B.zip")
    subprocess.call(["wget http://nlp.stanford.edu/data/glove.6B.zip && unzip glove.6B.zip"],shell=True)
    
    print('Finished downloading Glove word embeddings')
    subprocess.call(["rm 2pageSessions.csv glove.6B.200d.txt glove.6B.50d.txt glove.6B.300d.txt glove.6B.zip"],shell=True)
    
    
    # load the whole embedding into memory
    embeddings_index = dict()
    f = open('glove.6B.100d.txt')
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddings_index[word] = coefs
    f.close()
    vocab_size=len(embeddings_index)
    print('Loaded %s word vectors.' % vocab_size)
    
    # create a weight matrix for words in training docs
    embedding_matrix = np.zeros((vocab_size, 100))
    for word, i in t.word_index.items():
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector
            
    return embedding_matrix
    
    