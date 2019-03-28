#! /usr/bin/python
# -*- coding: utf8 -*-
"""Sequence to Sequence Learning for Twitter/Cornell Chatbot.

References
----------
http://suriyadeepan.github.io/2016-12-31-practical-seq2seq/
"""
import time
import os

import numpy as np
import tensorflow as tf
import tensorlayer as tl

from tqdm import tqdm
from sklearn.utils import shuffle
from tensorlayer.layers import DenseLayer, EmbeddingInputlayer, Seq2Seq, retrieve_seq_length_op2

from . import data
from mohaverekhan import utils

logger = utils.get_logger(logger_name='seq2seq')
logger.info('-------------------------------------------------------------------')
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
logger.info(f'CURRENT_DIR : {CURRENT_DIR}')
MODEL_PATH = os.path.join(utils.DATA_PATH, 'persian_informal_to_formal_seq2seq_model.npz')

sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False)
inference, cleanup = None, None
"""
Training model

inference_mode : Flag for INFERENCE mode
data_corpus : Data corpus to use for training and inference
batch_size : Batch size for training on minibatches
num_epochs : Number of epochs for training
learning_rate : Learning rate to use when training model
"""
def train(inference_mode=True, data_corpus='mohaverekhan_v1', batch_size=128, num_epochs=60, learning_rate=0.001):
    global inference, cleanup
    if cleanup is not None:
        cleanup()

    logger.info(f'inference_mode : {inference_mode}')
    logger.info(f'data_corpus : {data_corpus}')
    logger.info(f'batch_size : {batch_size}')
    logger.info(f'num_epochs : {num_epochs}')
    logger.info(f'learning_rate : {learning_rate}')

    metadata, trainX, trainY, testX, testY, validX, validY = initial_setup(data_corpus)
    # Parameters
    src_len = len(trainX)
    tgt_len = len(trainY)
    logger.info(f'len(trainX) : {len(trainX)}')
    logger.info(f'len(trainY) : {len(trainY)}')
    logger.info(f'len(testX) : {len(testX)}')
    logger.info(f'len(testY) : {len(testY)}')
    logger.info(f'len(validX) : {len(validX)}')
    logger.info(f'len(validY) : {len(validY)}')
    assert src_len == tgt_len

    n_step = src_len // batch_size
    src_vocab_size = len(metadata['idx2w']) # 8002 (0~8001)
    logger.info(f"len(metadata['idx2w'] : {len(metadata['idx2w'])}")
    logger.info(f"len(metadata['w2idx'] : {len(metadata['w2idx'])}")
    emb_dim = 1024

    word2idx = metadata['w2idx']   # dict  word 2 index
    idx2word = metadata['idx2w']   # list index 2 word

    unk_id = word2idx['unk']   # 1
    pad_id = word2idx['_']     # 0

    start_id = src_vocab_size  # 8002
    end_id = src_vocab_size + 1  # 8003

    word2idx.update({'start_id': start_id})
    word2idx.update({'end_id': end_id})
    idx2word = idx2word + ['start_id', 'end_id']

    src_vocab_size = tgt_vocab_size = src_vocab_size + 2

    """ A data for Seq2Seq should look like this:
    input_seqs : ['how', 'are', 'you', '<PAD_ID'>]
    decode_seqs : ['<START_ID>', 'I', 'am', 'fine', '<PAD_ID'>]
    target_seqs : ['I', 'am', 'fine', '<END_ID>', '<PAD_ID'>]
    target_mask : [1, 1, 1, 1, 0]
    """
    # Preprocessing
    target_seqs = tl.prepro.sequences_add_end_id([trainY[10]], end_id=end_id)[0]
    decode_seqs = tl.prepro.sequences_add_start_id([trainY[10]], start_id=start_id, remove_last=False)[0]
    target_mask = tl.prepro.sequences_get_mask([target_seqs])[0]
    if not inference_mode:
        logger.info(f'encode_seqs {[idx2word[id] for id in trainX[10]]}')
        logger.info(f'target_seqs {[idx2word[id] for id in target_seqs]}')
        logger.info(f'decode_seqs {[idx2word[id] for id in decode_seqs]}')
        logger.info(f'target_mask {target_mask}')
        logger.info(f'{len(target_seqs)} {len(decode_seqs)} {len(target_mask)}')

    # Init Session
    tf.reset_default_graph()
    sess = tf.Session(config=sess_config)
    # Training Data Placeholders
    encode_seqs = tf.placeholder(dtype=tf.int64, shape=[batch_size, None], name="encode_seqs")
    decode_seqs = tf.placeholder(dtype=tf.int64, shape=[batch_size, None], name="decode_seqs")
    target_seqs = tf.placeholder(dtype=tf.int64, shape=[batch_size, None], name="target_seqs")
    target_mask = tf.placeholder(dtype=tf.int64, shape=[batch_size, None], name="target_mask") 

    net_out, _ = create_model(encode_seqs, decode_seqs, src_vocab_size, emb_dim, is_train=True, reuse=False)
    net_out.print_params(False)

    logger.info(f' encode_seqs : {encode_seqs}')
    logger.info(f' decode_seqs : {decode_seqs}')
    logger.info(f' target_seqs : {target_seqs}')
    logger.info(f' target_mask : {target_mask}')
    logger.info(f' src_vocab_size : {src_vocab_size}')
    logger.info(f' emb_dim : {emb_dim}')
    # Inference Data Placeholders
    encode_seqs2 = tf.placeholder(dtype=tf.int64, shape=[1, None], name="encode_seqs")
    decode_seqs2 = tf.placeholder(dtype=tf.int64, shape=[1, None], name="decode_seqs")
    logger.info(f' encode_seqs2 : {encode_seqs2}')
    logger.info(f' decode_seqs2 : {decode_seqs2}')

    # encode_seqs2 = tf.placeholder(dtype=tf.int64, name="encode_seqs")
    # decode_seqs2 = tf.placeholder(dtype=tf.int64, name="decode_seqs")

    net, net_rnn = create_model(encode_seqs2, decode_seqs2, src_vocab_size, emb_dim, is_train=False, reuse=True)
    y = tf.nn.softmax(net.outputs)
    logger.info(f'net_rnn : {net_rnn}')
    logger.info(f'net.outputs : {net.outputs}')
    logger.info(f'net : {net}')
    logger.info(f'y : {y}')
    # Loss Function
    loss = tl.cost.cross_entropy_seq_with_mask(logits=net_out.outputs, target_seqs=target_seqs, 
                                                input_mask=target_mask, return_details=False, name='cost')
    logger.info(f'loss : {loss}')

    # Optimizer
    train_op = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(loss)

    # Init Vars
    sess_run = sess.run(tf.global_variables_initializer())
    logger.info(f'sess_run : {sess_run}')

    # Load Model
    logger.info(f'MODEL_PATH : {MODEL_PATH}')
    load_and_assign_npz = tl.files.load_and_assign_npz(sess=sess, name=MODEL_PATH, network=net)
    logger.info(f'load_and_assign_npz : {load_and_assign_npz}')

    """
    Inference using pre-trained model
    """
    def inference_function(seed):
        logger.info(f' > Inference with {seed}')
        seed_id = [word2idx.get(w, unk_id) for w in seed.split(" ")]
        
        # Encode and get state
        state = sess.run(net_rnn.final_state_encode,
                        {encode_seqs2: [seed_id]})
        # Decode, feed start_id and get first word [https://github.com/zsdonghao/tensorlayer/blob/master/example/tutorial_ptb_lstm_state_is_tuple.py]
        o, state = sess.run([y, net_rnn.final_state_decode],
                        {net_rnn.initial_state_decode: state,
                        decode_seqs2: [[start_id]]})
        w_id = tl.nlp.sample_top(o[0], top_k=3)
        w = idx2word[w_id]
        # Decode and feed state iteratively
        sentence = [w]
        for _ in range(100): # max sentence length
            o, state = sess.run([y, net_rnn.final_state_decode],
                            {net_rnn.initial_state_decode: state,
                            decode_seqs2: [[w_id]]})
            w_id = tl.nlp.sample_top(o[0], top_k=2)
            w = idx2word[w_id]
            if w_id == end_id:
                break
            sentence = sentence + [w]
        return " ".join([word for word in sentence if word is not '_'])

    def cleanup_function():
        # session cleanup
        sess.close()

    inference = inference_function
    cleanup = cleanup_function

    if inference_mode:
        logger.info('Test : خونه')
        sentence = inference('خونه')
        logger.info(f' > {sentence}')
        return

    seeds = ["بریم خونه",
                "اونا میان",
                "غذاش خیلی عالیه",
                "نون"]
    for epoch in range(num_epochs):
        trainX, trainY = shuffle(trainX, trainY, random_state=0)
        total_loss, n_iter = 0, 0
        for X, Y in tqdm(tl.iterate.minibatches(inputs=trainX, targets=trainY, batch_size=batch_size, shuffle=False), 
                        total=n_step, desc='Epoch[{}/{}]'.format(epoch + 1, num_epochs), leave=False):

            X = tl.prepro.pad_sequences(X)
            _target_seqs = tl.prepro.sequences_add_end_id(Y, end_id=end_id)
            _target_seqs = tl.prepro.pad_sequences(_target_seqs)
            _decode_seqs = tl.prepro.sequences_add_start_id(Y, start_id=start_id, remove_last=False)
            _decode_seqs = tl.prepro.pad_sequences(_decode_seqs)
            _target_mask = tl.prepro.sequences_get_mask(_target_seqs)
            ## Uncomment to view the data here
            # for i in range(len(X)):
            #     logger.info(i, [idx2word[id] for id in X[i]])
            #     logger.info(i, [idx2word[id] for id in Y[i]])
            #     logger.info(i, [idx2word[id] for id in _target_seqs[i]])
            #     logger.info(i, [idx2word[id] for id in _decode_seqs[i]])
            #     logger.info(i, _target_mask[i])
            #     logger.info(len(_target_seqs[i]), len(_decode_seqs[i]), len(_target_mask[i]))
            _, loss_iter = sess.run([train_op, loss], {encode_seqs: X, decode_seqs: _decode_seqs,
                            target_seqs: _target_seqs, target_mask: _target_mask})
            total_loss += loss_iter
            n_iter += 1

        # printing average loss after every epoch
        logger.info('Epoch [{}/{}]: loss {:.4f}'.format(epoch + 1, num_epochs, total_loss / n_iter))
        
        # inference after every epoch
        for seed in seeds:
            logger.info(f'Query > {seed}')
            for _ in range(5):
                sentence = inference(seed)
                logger.info(f' >  {sentence}')
        
        # saving the model
        tl.files.save_npz(net.all_params, name=MODEL_PATH, sess=sess)

    # session cleanup
    sess.close()

"""
Creates the LSTM Model
"""
def create_model(encode_seqs, decode_seqs, src_vocab_size, emb_dim, is_train=True, reuse=False):
    with tf.variable_scope("model", reuse=reuse):
        # for chatbot, you can use the same embedding layer,
        # for translation, you may want to use 2 seperated embedding layers
        with tf.variable_scope("embedding") as vs:
            net_encode = EmbeddingInputlayer(
                inputs = encode_seqs,
                
                vocabulary_size = src_vocab_size,
                embedding_size = emb_dim,
                name = 'seq_embedding')
            vs.reuse_variables()
            net_decode = EmbeddingInputlayer(
                inputs = decode_seqs,
                vocabulary_size = src_vocab_size,
                embedding_size = emb_dim,
                name = 'seq_embedding')
            
        x = retrieve_seq_length_op2(encode_seqs)
        y = retrieve_seq_length_op2(decode_seqs)
        logger.info(f'x : {x}')
        logger.info(f'y : {y}')
        net_rnn = Seq2Seq(net_encode, net_decode,
                cell_fn = tf.nn.rnn_cell.LSTMCell,
                n_hidden = emb_dim,
                # initializer = tf.random_uniform_initializer(0, 1),
                initializer = tf.random_uniform_initializer(-0.1, 0.1),
                encode_sequence_length = retrieve_seq_length_op2(encode_seqs),
                decode_sequence_length = retrieve_seq_length_op2(decode_seqs),
                initial_state_encode = None,
                dropout = (0.5 if is_train else None),
                n_layer = 3,
                return_seq_2d = True,
                name = 'seq2seq')

        net_out = DenseLayer(net_rnn, n_units=src_vocab_size, act=tf.identity, name='output')
    return net_out, net_rnn

"""
Initial Setup
"""
def initial_setup(data_corpus):
    data_corpus_path = f'{CURRENT_DIR}/data/{data_corpus}/'
    logger.info(f'data_corpus_path : {data_corpus_path}')
    metadata, idx_inf, idx_f = data.load_data(PATH=data_corpus_path)
    (trainX, trainY), (testX, testY), (validX, validY) = data.split_dataset(idx_inf, idx_f)
    trainX = tl.prepro.remove_pad_sequences(trainX.tolist())
    trainY = tl.prepro.remove_pad_sequences(trainY.tolist())
    testX = tl.prepro.remove_pad_sequences(testX.tolist())
    testY = tl.prepro.remove_pad_sequences(testY.tolist())
    validX = tl.prepro.remove_pad_sequences(validX.tolist())
    validY = tl.prepro.remove_pad_sequences(validY.tolist())
    logger.info('initial setup completed.')
    return metadata, trainX, trainY, testX, testY, validX, validY


def main():
    global inference, cleanup
    try:
        train()
        # inference, cleanup = train(False, 'mohaverekhan_v1', 128, 1, 0.001)

        if inference is not None:
            logger.info('Inference Mode')
            logger.info('--------------')
            while True:
                input_seq = input('Enter Query: ')
                logger.info(f'Enter Query: {input_seq}')
                sentence = inference(input_seq)
                logger.info(f' > {" ".join(sentence)}')
        logger.info('End of main')
    except KeyboardInterrupt:
        if cleanup is not None:
            logger.info('Cleanup')
            cleanup()
        logger.warning('Aborted!')
    except Exception as e:
        logger.exception(e)
        logger.error(' >> Error <<')

if os.path.isfile(MODEL_PATH):
    train()

if __name__ == '__main__':
    logger.info(f'this is main, {__name__}')
else:
    logger.info(f'this is not main, {__name__}')
    # main()
