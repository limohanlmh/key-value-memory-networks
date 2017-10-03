# -*- coding: utf-8

import pickle
from nltk.tokenize import word_tokenize
import numpy as np
import functools
from itertools import chain
import copy

def save_pickle(d, path):
    print('save pickle to', path)
    with open(path, mode='wb') as f:
        pickle.dump(d, f)

def load_pickle(path):
    print('load', path)
    with open(path, mode='rb') as f:
        return pickle.load(f)

def lower_list(word_list):
    return [w.lower() for w in word_list]

def load_entities(path):
    with open(path, 'r') as f:
        lines = f.readlines()
        return [e.lower().rstrip() for e in lines]

def load_task(fpath):
    with open (fpath) as f:
        lines = f.readlines()
        data, story = [], []
        for l in lines:
            l = l.rstrip()
            turn, left = l.split(' ', 1)
            
            if turn == '1': # new story
                story = []

            if '\t' in left: # question
                q, a = left.split('\t', 1)
                q = word_tokenize(q)
                q = lower_list(q)
                if q[-1] == '?':
                    q = q[:-1]
                if '\t' in a:
                    a = a.split('\t')[0] # discard reward
                a = a.split('|') # may contain several labels
                a = lower_list(a)

                substory = [x for x in story if x]

                data.append((substory, q, a))
                story.append('')
            else: # normal sentence
                s = word_tokenize(left)
                if s[-1] == '.':
                    s = s[:-1]
                s = lower_list(s)
                story.append(s)

    return data

def vectorize(data, w2i, max_sentence_size, memory_size, entities=None):
    if entities:
        e2i = dict((e, i) for i, e in enumerate(entities))

    S, Q, A = [], [], []
    for story, question, answer in data:
        # Vectroize story
        ss = []
        for sentence in story:
            s_pad_len = max(0, max_sentence_size - len(sentence))
            ss.append([w2i[w] for w in sentence] + [0] * s_pad_len)
        ss = ss[::-1][:memory_size] # discard old memory lager than memory_size
        # pad to memory_size
        lm = max(0, memory_size - len(ss))
        for _ in range(lm):
            ss.append([0] * max_sentence_size)

        # Vectroize question
        q_pad_len = max(0, max_sentence_size - len(question))
        q = [w2i[w] for w in question] + [0] * q_pad_len

        # Vectroize answer
        if entities:
            y = np.zeros(len(entities), dtype='byte')
            for a in answer:
                y[e2i[a]] = 1
        else:
            y = np.zeros(len(w2i) + 1) # +1 for nil word
            for a in answer:
                y[w2i[a]] = 1

        S.append(ss)
        Q.append(q)
        A.append(y)
    
    S = np.array(S, dtype=np.uint16)
    Q = np.array(Q, dtype=np.uint16)
    A = np.array(A, dtype='byte')

    return S, Q, A

def load_kv_pairs(path, entities):
    """load key-value paris from KB"""

    w2i = dict((e, i) for i, e in enumerate(entities))
    data = []
    with open(path, 'r') as f:
        lines = f.readlines()
        data = [l.rstrip().split(' ', 1)[1] for l in lines if l != '\n']
    kv_pairs = []
    for sentence in data:
        k = []
        for w in sentence:
            if w in w2i:
                k.append(w2i[w])
            elif w.find('_') != -1:
                w2i[w] = len(w2i)
                k.append(w2i[w])
        v = copy.deepcopy(k)
        kv_pairs.append((k, v))

    return kv_pairs
        
if __name__ == '__main__':
    entities = load_pickle('entities.pickle')
    kv_pairs = load_kv_pairs('./data/movieqa/knowledge_source/wiki_entities/wiki_entities_kb.txt', entities)
    
    # data = load_task('./data/tasks_1-20_v1-2/en/qa1_single-supporting-fact_test.txt')
    # data = load_task('./data/tasks_1-20_v1-2/en/qa5_three-arg-relations_test.txt')

    # vocab = functools.reduce(lambda x, y: x | y, (set(list(chain.from_iterable(s)) + q + a) for s, q, a in data))
    # w2i = dict((c, i) for i, c in enumerate(vocab, 1))
    # i2w = dict((i, c) for i, c in enumerate(vocab, 1))
    # print(len(vocab))    print("HOGE")
    # S, Q, A = vectorize(data,)