import random
import numpy as np


def w2v_similarity(words, types, model):
    return np.array([model.wv.n_similarity(words, typ) for typ in types])/2 + 1/2  # normalize similarity between 0 and 1


def freq_nearest_similarity(words, types, model, extra_args={'n_nearest': 3}):
    n_nearest = extra_args['n_nearest']

    similarities = w2v_similarity(words, types, model)
    sorted_inds = np.argsort(similarities)[::-1]

    # return indicator vector for types that are among the n_nearest most similar
    neighbors = np.zeros(len(types))
    neighbors[sorted_inds[:n_nearest]] = 1

    return neighbors


def get_type_similarities(data, types, model, similarity_func=w2v_similarity, extra_args=None):

    similarities = np.zeros(len(types))
    numsamples = 500
    n_processed = 0
    for dat in data[0:max(len(data), numsamples)]:
        try:
            similarities += similarity_func(dat, types, model, extra_args) if extra_args \
                       else similarity_func(dat, types, model) 
            n_processed += 1
                
        except KeyError as err:
            print('error checking distance of word {0} to types (out of vocab?):'.format(dat), err)
            raise err
        except Exception as err:
            print('unknown error: ', err)
            print(dat)
            print("==========")
            raise err

    similarities /= max(1, n_processed)  # divide to get average 
    types = np.array([' '.join(typ) for typ in types])  # unpack lol with spaces between words and convert to np array
    
    # print('average similarity max, min: ', np.max(similarities), ', ', np.min(similarities), '\n\n')

    return similarities