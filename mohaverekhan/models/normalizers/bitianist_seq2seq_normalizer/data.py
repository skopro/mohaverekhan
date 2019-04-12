import random
import sys
import os
import logging

import pickle
import itertools
from collections import defaultdict

import numpy as np
import pandas as pd
import nltk

# from ..tools import utils
# from mohaverekhan import utils

logger = logging.getLogger(__name__)

# logger = utils.get_logger(logger_name='data_setup')
current_dir = os.path.abspath(os.path.dirname(__file__))

from mohaverekhan.models import Normalizer, Text, TextNormal, Word, WordNormal
from mohaverekhan import cache


EN_WHITELIST = '۰۱۲۳۴۵۶۷۸۹0123456789اآب‌پتثجچحخدذرزژسشصضطظعغفقکگلمنوهی ' # space is included in whitelist
EN_BLACKLIST = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~\''

SRC_DIR = '/home/bitianist/Dropbox/bachelor_project/data/final'

limit = {
        'maxinf' : 500,
        'mininf' : 1,
        'maxf' : 500,
        'minf' : 1
        }

UNK = 'unk'
VOCAB_SIZE = 10000



def ddefault():
    return 1


# '''
#  split sentences in one line
#   into multiple lines
#     return [list of lines]

# '''
# def split_line(line):
#     return line.split('.')


# '''
#  remove anything that isn't in the vocabulary
#     return str(pure ta/en)

# '''
# def filter_characters(line, whitelist):
#     return ''.join([ ch if ch in whitelist else ' ' for ch in line.__str__() ])


'''
 read list of words, create index to word,
  word to index dictionaries
    return tuple( vocab->(word, count), idx2w, w2idx )

'''
def index_(tokenized_sentences, vocab_size):
    # get frequency distribution
    freq_dist = nltk.FreqDist(itertools.chain(*tokenized_sentences))
    # get vocabulary of 'vocab_size' most used words
    vocab = freq_dist.most_common(vocab_size)
    # index2word
    index2word = ['_'] + [UNK] + [ x[0] for x in vocab ]
    # word2index
    word2index = dict([(w,i) for i,w in enumerate(index2word)] )
    return index2word, word2index, freq_dist


'''
 filter too long and too short sequences
    return tuple( filtered_ta, filtered_en )

'''
def filter_length(informals, formals):
    filtered_informals, filtered_formals = [], []
    raw_data_len = len(informals)

    for i in range(0, len(informals) - 1):
        inflen, flen = len(informals[i].split(' ')), len(formals[i].split(' '))
        if inflen >= limit['mininf'] and inflen <= limit['maxinf']:
            if flen >= limit['minf'] and flen <= limit['maxf']:
                filtered_informals.append(informals[i])
                filtered_formals.append(formals[i])

    # print the fraction of the original data, filtered
    filt_data_len = len(filtered_informals)
    filtered = int((raw_data_len - filt_data_len)*100/raw_data_len)
    logger.info(f'{raw_data_len - filt_data_len} of {raw_data_len} data filtered from original data')
    logger.info(str(filtered) + '% filtered from original data')
    logger.info(f'filtered_informals has {len(filtered_informals)} items')
    logger.info(f'filtered_formals has {len(filtered_formals)} items')
    return filtered_informals, filtered_formals


'''
 create the final dataset :
  - convert list of items to arrays of indices
  - add zero padding
      return ( [array_en([indices]), array_ta([indices]) )

'''
def zero_pad(inftokenized, ftokenized, w2idx):
    # num of rows
    data_len = len(inftokenized)

    # numpy arrays to store indices
    idx_inf = np.zeros([data_len, limit['maxinf']], dtype=np.int32)
    idx_f = np.zeros([data_len, limit['maxf']], dtype=np.int32)

    for i in range(data_len):
        inf_indices = pad_seq(inftokenized[i], w2idx, limit['maxinf'])
        f_indices = pad_seq(ftokenized[i], w2idx, limit['maxf'])

        #logger.info(len(idx_q[i]), len(q_indices))
        #logger.info(len(idx_a[i]), len(a_indices))
        idx_inf[i] = np.array(inf_indices)
        idx_f[i] = np.array(f_indices)

    return idx_inf, idx_f


'''
 replace words with indices in a sequence
  replace with unknown if word not in lookup
    return [list of indices]

'''
def pad_seq(seq, lookup, maxlen):
    indices = []
    for word in seq:
        if word in lookup:
            indices.append(lookup[word])
        else:
            indices.append(lookup[UNK])
    return indices + [0]*(maxlen - len(seq))

    

def log_sample(index, src, dest):
    logger.info(f'src[{index if index >= 0 else len(src) + index - 1}] : {src[index]}')
    logger.info(f'dest[{index if index >= 0 else len(dest) + index - 1}] : {dest[index]}')

def get_text_normals():
    informals, formals = [], []
    informal_text, formal_text = None, None
    informal_text_normal, formal_text_normal = None, None
    normalizer = cache.normalizers['bitianist-informal-replacement-normalizer']

    text_normals = TextNormal.objects.filter(
        is_valid=True
    )

    for text_normal in text_normals:
        informal_text = text_normal
        formal_text = text_normal.text

        informal_text_normal = normalizer.normalize(informal_text)
        formal_text_normal = normalizer.normalize(formal_text)

        informals.append(informal_text_normal.content)
        formals.append(formal_text_normal.content)

    logger.info(f'> len(informals) : {len(informals)}')
    logger.info(f'> len(formals) : {len(formals)}')
    logger.info(f'> {len(informals)} text normals exist for training.')
    return informals, formals

def get_word_normals():
    informals, formals = [], []
    informal_word, formal_word = None, None
    informal_word_normal, formal_word_normal = None, None
    normalizer = cache.normalizers['bitianist-informal-replacement-normalizer']

    word_normals = WordNormal.objects.filter(
        is_valid=True
    )

    for word_normal in word_normals:
        informal_word = word_normal
        formal_word = word_normal.word

        informal_word_normal = normalizer.normalize(informal_word)
        formal_word_normal = normalizer.normalize(formal_word)

        informals.append(informal_word_normal.content)
        formals.append(formal_word_normal.content)

    logger.info(f'> len(informals) : {len(informals)}')
    logger.info(f'> len(formals) : {len(formals)}')
    logger.info(f'> {len(informals)} word normals exist for training.')
    return informals, formals

def get_data():
    logger.info(f'>> Getting data...')
    informals, formals = [], []
    
    text_informals, text_formals = get_text_normals()
    word_informals, word_formals = get_word_normals()

    informals = text_informals + word_informals
    formals = text_formals + word_formals

    logger.info(f'> len(informals) : {len(informals)}')
    logger.info(f'> len(formals) : {len(formals)}')
    logger.info(f'> {len(informals)} text + word normals exist for training.')
    return informals, formals
    

def process_data():
    try:
        # informals, formals = read_from_excel()
        informals, formals = get_data()

        log_sample(20, informals, formals)
        log_sample(100, informals, formals)
        log_sample(-20, informals, formals)
        log_sample(-100, informals, formals)

        logger.info(f'informals[36] : {informals[36]}')
        logger.info(f'formals[36] : {formals[36]}')

        # filter out too long or too short sequences
        logger.info('>> Filter length')
        informals, formals = filter_length(informals, formals)

        log_sample(30, informals, formals)
        log_sample(130, informals, formals)
        log_sample(-30, informals, formals)
        log_sample(-130, informals, formals)

        # # data fixing
        # logger.info('>> Fix data')
        # informals, formals = fix_data(informals, formals)

        # convert list of [lines of text] into list of [list of words ]
        logger.info('>> Tokenized (Segment lines into words)')
        inftokenized = [ wordlist.split(' ') for wordlist in informals ]
        ftokenized = [ wordlist.split(' ') for wordlist in formals ]

        log_sample(10, inftokenized, ftokenized)
        log_sample(90, inftokenized, ftokenized)
        log_sample(-10, inftokenized, ftokenized)
        log_sample(-90, inftokenized, ftokenized)

        # indexing -> idx2w, w2idx : informal/formal
        logger.info(' >> Index words')
        idx2w, w2idx, freq_dist = index_( inftokenized + ftokenized , vocab_size=VOCAB_SIZE)

        logger.info(f'idx2w[20] : {idx2w[20]}')
        logger.info(f'w2idx[idx2w[20]] : {w2idx[idx2w[20]]}')

        logger.info(' >> Zero Padding')
        idx_inf, idx_f = zero_pad(inftokenized, ftokenized, w2idx)

        logger.info(f'idx_inf[67] : {idx_inf[67]}')
        logger.info([idx2w[idx] for idx in idx_inf[67] if idx != 0])
        logger.info(f'idx_f[67] : {idx_f[67]}')
        logger.info([idx2w[idx] for idx in idx_f[67] if idx != 0])


        logger.info(' >> Save numpy arrays to disk')
        # save them
        np.save(os.path.join(current_dir, 'idx_inf.npy'), idx_inf)
        np.save(os.path.join(current_dir, 'idx_f.npy'), idx_f)

        # let us now save the necessary dictionaries
        metadata = {
                'w2idx' : w2idx,
                'idx2w' : idx2w,
                'limit' : limit,
                'freq_dist' : freq_dist
                    }

        logger.info(f"len(metadata['idx2w'] : {len(metadata['idx2w'])}")
        logger.info(f"len(metadata['w2idx'] : {len(metadata['w2idx'])}")

        # write to disk : data control dictionaries
        with open(os.path.join(current_dir, 'metadata.pkl'), 'wb') as f:
            pickle.dump(metadata, f)

        return
    except Exception as e:
        logger.error(f'error : {e}')



def load_data(PATH=''):
    # read data control dictionaries
    try:
        with open(PATH + 'metadata.pkl', 'rb') as f:
            metadata = pickle.load(f)
    except:
        metadata = None
    # read numpy arrays
    idx_inf = np.load(PATH + 'idx_inf.npy')
    idx_f = np.load(PATH + 'idx_f.npy')
    return metadata, idx_inf, idx_f

import numpy as np
from random import sample

'''
 split data into train (70%), test (15%) and valid(15%)
    return tuple( (trainX, trainY), (testX,testY), (validX,validY) )

'''
def split_dataset(x, y, ratio = [0.7, 0.15, 0.15] ):
    # number of examples
    data_len = len(x)
    lens = [ int(data_len*item) for item in ratio ]

    trainX, trainY = x[:lens[0]], y[:lens[0]]
    testX, testY = x[lens[0]:lens[0]+lens[1]], y[lens[0]:lens[0]+lens[1]]
    validX, validY = x[-lens[-1]:], y[-lens[-1]:]

    return (trainX,trainY), (testX,testY), (validX,validY)


'''
 generate batches from dataset
    yield (x_gen, y_gen)

    TODO : fix needed

'''
def batch_gen(x, y, batch_size):
    # infinite while
    while True:
        for i in range(0, len(x), batch_size):
            if (i+1)*batch_size < len(x):
                yield x[i : (i+1)*batch_size ].T, y[i : (i+1)*batch_size ].T

'''
 generate batches, by random sampling a bunch of items
    yield (x_gen, y_gen)

'''
def rand_batch_gen(x, y, batch_size):
    while True:
        sample_idx = sample(list(np.arange(len(x))), batch_size)
        yield x[sample_idx].T, y[sample_idx].T

#'''
# convert indices of alphabets into a string (word)
#    return str(word)
#
#'''
#def decode_word(alpha_seq, idx2alpha):
#    return ''.join([ idx2alpha[alpha] for alpha in alpha_seq if alpha ])
#
#
#'''
# convert indices of phonemes into list of phonemes (as string)
#    return str(phoneme_list)
#
#'''
#def decode_phonemes(pho_seq, idx2pho):
#    return ' '.join( [ idx2pho[pho] for pho in pho_seq if pho ])


'''
 a generic decode function
    inputs : sequence, lookup

'''
def decode(sequence, lookup, separator=''): # 0 used for padding, is ignored
    return separator.join([ lookup[element] for element in sequence if element ])


# def init():
#     global logger
#     logger = logging.getLogger(__name__)



# import re

# def fix_data(informals, formals):
#     fixed_informals, fixed_formals, low_words, low_words_sentences = [], [], [], []
#     nl = '\n'
#     for sentence in informals + formals:
#         for word in sentence.split(' '):
#             word = word.strip()
#             if len(word) <= 3:
#                 if word not in low_words and word.strip() is not '':
#                     low_words.append(word)
#                     low_words_sentences.append(f'[{word}] in [{sentence}]')
                
#     logger.info(f"\n\nlow_words :\n{nl.join(low_words_sentences)}\n\n-------------------------------------------------\n\n")
    
#     corrections = { 
#         'هارو': 'ها رو',
#         'هامون': 'هایمان',
#         'ده است': 'ده‌است',
#         ' می ': ' می‌',
#         ' نمی ': ' نمی‌',
#         ' ها ': '‌ها ',
#         ' های ': '‌های ',
#         ' هایمان ': '‌هایمان ',
#         ' ام ': '‌ام ',
#         'ه ی ': 'ه‌ی ',
#         ' ایم ': '‌ایم ',
#         ' مان ': '‌مان ',
#     }

#     regex_corrections = {
#         r' های$': '‌های',
#         r'^می ': 'می‌',
#         r'^نمی ': 'نمی‌',
#         r' ها$': '‌ها',
#         r' ام$': '‌ام',
#         r' هایمان$': '‌هایمان',
#         r' ایم$': '‌ایم',
#         r' مان$': '‌مان',
#     }

#     for text in informals:
#         for key, value in corrections.items():
#             text = text.replace(key, value)
#         for key,value in regex_corrections.items():
#             text = re.sub(key, value, text)
#         fixed_informals.append(text)

#     for text in formals:
#         for key, value in corrections.items():
#             text = text.replace(key, value)
#         for key,value in regex_corrections.items():
#             text = re.sub(key, value, text)
#         fixed_formals.append(text)

#     tokens = []
#     for sentence in fixed_informals + fixed_formals:
#         for token in sentence.split(' '):
#             token = token.strip()
#             if token not in tokens:
#                 tokens.append(token)
#             for key in corrections:
#                 key = key.strip()
#                 if key == token:
#                     logger.warn(f'wrong : [{key}] exists in [{sentence}]')


#     logger.info(f'len(tokens) : {len(tokens)}')
#     logger.info(f'tokens : \n{tokens}')
#     for key in corrections:
#         key = key.strip()
#         if key in tokens:
#             logger.warn(f'wrong : [{key}] exists in tokens')
                
#     return fixed_informals, fixed_formals

    # def read_from_excel():
#     logger.info('>> Read from excel')
#     informals, formals = [], []
#     target_informal_word, target_formal_word = '', ''

#     # Add sentence equivalents
#     excel_path = os.path.join(SRC_DIR, 'sentence_equivalents.xlsx')
#     sheet_name = 'sentence_equivalents'
#     df = pd.read_excel(excel_path, sheet_name=sheet_name)
#     logger.info(f'Column headings: {df.columns}')
#     counter = 0
#     for i in df.index:
#         target_informal_word = df['عبارت غیر رسمی'][i].__str__().strip()
#         target_formal_word = df['عبارت رسمی'][i].__str__().strip()
#         if target_informal_word == 'nan':
#             break
#         informals.append(target_informal_word)
#         formals.append(target_formal_word)
#         counter += 1 
#     logger.info(f' > {counter} sentences added.')


#     # Add word equivalents
#     excel_path = os.path.join(SRC_DIR, 'word_equivalents.xlsx')
#     sheet_name = 'word_equivalents'
#     df = pd.read_excel(excel_path, sheet_name='word_equivalents')
#     logger.info(f'Column headings: {df.columns}')
#     counter = 0
#     for i in df.index:
#         target_informal_word = df['کلمه غیر رسمی'][i].__str__().strip()
#         target_formal_word = df['کلمه رسمی'][i].__str__().strip()
#         if target_formal_word == 'nan':
#             break
#         if target_formal_word in formals:
#             logger.info(f'word {target_formal_word} is duplicate in row {i}')
#             continue
#         informals.append(target_informal_word)
#         formals.append(target_formal_word)
#         counter += 1 
#     logger.info(f' > {counter} words added.')

#     logger.info(f'len(informals) : {len(informals)}')
#     logger.info(f'len(formals) : {len(formals)}')
#     logger.info(f' > {len(informals)} data (texts + words) exist for training.')
#     return informals, formals