import re
import time
from datetime import datetime
import json

import numpy as np
import pandas as pd
from gensim.models import Word2Vec


def timeit(func, args=None):
    start = time.time()
    print('calling {0} \n'.format(func.__name__))
    result = func(*args) if args else func()
    print('{0} took {1} seconds \n\n'.format(func.__name__, time.time() - start))
    return result


def load_model(model_name='/data/duke/models/word2vec/en_1000_no_stem/en.model'):
    ''' Load a word2vec model from a file in models/ '''
    return Word2Vec.load(model_name)


def get_dropped(all_headers, new_headers):
    return set(all_headers).difference(set(new_headers))


def load_dataset(full_df, model, drop_nan=True, verbose=False):
    headers = full_df.columns.values

    # TODO confirm that the columns selected can't be cast to a numeric type to avoid numeric strings (e.g. '1')
    text_df = full_df.select_dtypes(['object'])  # drop non-text rows (pandas strings are of type 'object')
    dtype_dropped = get_dropped(headers, text_df.columns.values)
    if(verbose):
        print('dropped non-text columns: {0} \n'.format(list(dtype_dropped)))

    if drop_nan: # drop columns if there are any missing values
        text_df = text_df.dropna(axis=1, how='any')
        nan_dropped = get_dropped(headers, text_df.columns.values)
        nan_dropped = nan_dropped.difference(dtype_dropped)
        if(verbose):
            print('dropped columns with missing values: {0} \n'.format(list(nan_dropped)))
    
    data = {}
    if(verbose):
        print('normalizing headers')
    data['headers'] = normalize_headers(headers, model, verbose=verbose) 

    for col in text_df.columns.values:
        if(verbose):
            print('normalizing column: ', col)
        data[col] = normalize_text(text_df[col].values, model, verbose=verbose) 

    return data


def get_timestamp():
    return datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M:%S')


def load_types(model, types_filename='/data/duke/models/ontologies/types'):
    # load types and normalize (remove out of vocab etc.)
    with open(types_filename, 'r') as f:  
        types = f.read().splitlines()
        return normalize_types(types, model)  


def normalize_types(types, model, verbose=False):
    # create a lol of types split by capitalization
    types = np.array([re.findall('[A-Z][^A-Z]*', typ) for typ in types])  # list of lists of single words
    # TODO more general processing? split by spaces?
    # remove types with out-of-vocab words

    in_vocab = [np.all([word in model.wv.vocab for word in typ]) for typ in types]   
    if(verbose):
        print('dropped {0} out of {1} type values for having out-of-vocab words. \n'.format(len(types) - sum(in_vocab), len(types)))

    return types[in_vocab]


def normalize_headers(headers, model, verbose=False):
    headers = np.array([h.replace('_', ' ').replace('-', ' ').lower().split(' ') for h in headers])  # list of lists of single words

    in_vocab = [np.all([word in model.wv.vocab for word in h]) for h in headers]   
    if(verbose):
        print('dropped {0} out of {1} headers for having out-of-vocab words. \n'.format(len(headers) - sum(in_vocab), len(headers)))

    return headers[in_vocab]


def normalize_text(text, model, verbose=False):
    text = np.array([t.replace('_', ' ').replace('-', ' ').lower().split(' ') for t in text])  # list of lists of single words

    in_vocab = [np.all([word in model.wv.vocab for word in t]) for t in text]
    if(verbose):
        print('dropped {0} out of {1} text values for having out-of-vocab words \n'.format(len(text) - sum(in_vocab), len(text)))

    return text[in_vocab] 


def log_top_similarities(sorted_types, similarities, n_keep=20):
    print('top {0} types, similarities: \n'.format(n_keep))
    for typ, sim in zip(sorted_types[:n_keep], similarities[:n_keep]):
        print(typ, sim)
    print('\n\n')


class NumpyEncoder(json.JSONEncoder):
    
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)