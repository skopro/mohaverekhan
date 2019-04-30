#! /usr/bin/python
# -*- coding: utf8 -*-
"""Sequence to Sequence Learning for Twitter/Cornell Chatbot.

References
----------
http://suriyadeepan.github.io/2016-12-31-practical-seq2seq/
"""
import time 
import logging
import os

import numpy as np
import tensorflow as tf
import tensorlayer as tl

from tqdm import tqdm
from sklearn.utils import shuffle
from tensorlayer.layers import DenseLayer, EmbeddingInputlayer, Seq2Seq, retrieve_seq_length_op2

from . import data
# from mohaverekhan import utils

from mohaverekhan.models import Normalizer, Text, TextNormal
from mohaverekhan import cache


class MohaverekhanSeq2SeqNormalizer(Normalizer):

    class Meta:
        proxy = True

    sess_config = None
    inference, cleanup = None, None
    logger = logging.getLogger(__name__)
    current_dir = os.path.abspath(os.path.dirname(__file__))
    model_path = os.path.join(current_dir, 'model.npz')

    sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False)
    def __init__(self, *args, **kwargs):
        super(MohaverekhanSeq2SeqNormalizer, self).__init__(*args, **kwargs)
        # if os.path.isfile(self.model_path):
        #     self.train(True)
    

    """
    Training model

    inference_mode : Flag for INFERENCE mode
    data_corpus : Data corpus to use for training and inference
    batch_size : Batch size for training on minibatches
    num_epochs : Number of epochs for training
    learning_rate : Learning rate to use when training model
    """
    def train(self, inference_mode=False, batch_size=256, num_epochs=10, learning_rate=0.003):
        if self.cleanup is not None:
            self.cleanup()

        self.logger.info(f'> inference_mode : {inference_mode}')
        self.logger.info(f'> batch_size : {batch_size}')
        self.logger.info(f'> num_epochs : {num_epochs}')
        self.logger.info(f'> learning_rate : {learning_rate}')

        metadata, trainX, trainY, testX, testY, validX, validY = self.initial_setup()
        # Parameters
        src_len = len(trainX)
        tgt_len = len(trainY)
        self.logger.info(f'len(trainX) : {len(trainX)}')
        self.logger.info(f'len(trainY) : {len(trainY)}')
        self.logger.info(f'len(testX) : {len(testX)}')
        self.logger.info(f'len(testY) : {len(testY)}')
        self.logger.info(f'len(validX) : {len(validX)}')
        self.logger.info(f'len(validY) : {len(validY)}')
        assert src_len == tgt_len

        n_step = src_len // batch_size
        src_vocab_size = len(metadata['idx2w']) # 8002 (0~8001)
        self.logger.info(f"len(metadata['idx2w'] : {len(metadata['idx2w'])}")
        self.logger.info(f"len(metadata['w2idx'] : {len(metadata['w2idx'])}")
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
            self.logger.info(f'encode_seqs {[idx2word[id] for id in trainX[10]]}')
            self.logger.info(f'target_seqs {[idx2word[id] for id in target_seqs]}')
            self.logger.info(f'decode_seqs {[idx2word[id] for id in decode_seqs]}')
            self.logger.info(f'target_mask {target_mask}')
            self.logger.info(f'{len(target_seqs)} {len(decode_seqs)} {len(target_mask)}')

        # Init Session
        tf.reset_default_graph()
        sess = tf.Session(config=self.sess_config)
        # Training Data Placeholders
        encode_seqs = tf.placeholder(dtype=tf.int64, shape=[batch_size, None], name="encode_seqs")
        decode_seqs = tf.placeholder(dtype=tf.int64, shape=[batch_size, None], name="decode_seqs")
        target_seqs = tf.placeholder(dtype=tf.int64, shape=[batch_size, None], name="target_seqs")
        target_mask = tf.placeholder(dtype=tf.int64, shape=[batch_size, None], name="target_mask") 

        net_out, _ = self.create_model(encode_seqs, decode_seqs, src_vocab_size, emb_dim, is_train=True, reuse=False)
        net_out.print_params(False)

        self.logger.info(f' encode_seqs : {encode_seqs}')
        self.logger.info(f' decode_seqs : {decode_seqs}')
        self.logger.info(f' target_seqs : {target_seqs}')
        self.logger.info(f' target_mask : {target_mask}')
        self.logger.info(f' src_vocab_size : {src_vocab_size}')
        self.logger.info(f' emb_dim : {emb_dim}')
        # Inference Data Placeholders
        encode_seqs2 = tf.placeholder(dtype=tf.int64, shape=[1, None], name="encode_seqs")
        decode_seqs2 = tf.placeholder(dtype=tf.int64, shape=[1, None], name="decode_seqs")
        self.logger.info(f' encode_seqs2 : {encode_seqs2}')
        self.logger.info(f' decode_seqs2 : {decode_seqs2}')

        # encode_seqs2 = tf.placeholder(dtype=tf.int64, name="encode_seqs")
        # decode_seqs2 = tf.placeholder(dtype=tf.int64, name="decode_seqs")

        net, net_rnn = self.create_model(encode_seqs2, decode_seqs2, src_vocab_size, emb_dim, is_train=False, reuse=True)
        y = tf.nn.softmax(net.outputs)
        self.logger.info(f'net_rnn : {net_rnn}')
        self.logger.info(f'net.outputs : {net.outputs}')
        self.logger.info(f'net : {net}')
        self.logger.info(f'y : {y}')
        # Loss Function
        loss = tl.cost.cross_entropy_seq_with_mask(logits=net_out.outputs, target_seqs=target_seqs, 
                                                    input_mask=target_mask, return_details=False, name='cost')
        self.logger.info(f'loss : {loss}')

        # Optimizer
        train_op = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(loss)

        # Init Vars
        sess_run = sess.run(tf.global_variables_initializer())
        self.logger.info(f'sess_run : {sess_run}')

        # Load Model
        self.logger.info(f'model_path : {self.model_path}')
        load_and_assign_npz = tl.files.load_and_assign_npz(sess=sess, name=self.model_path, network=net)
        self.logger.info(f'load_and_assign_npz : {load_and_assign_npz}')

        """
        Inference using pre-trained model
        """
        def inference_function(seed):
            self.logger.info(f'> {seed}')
            seed_id = [word2idx.get(w, unk_id) for w in seed.split(" ")]
            
            # Encode and get state
            state = sess.run(net_rnn.final_state_encode,
                            {encode_seqs2: [seed_id]})
            # Decode, feed start_id and get first word [https://github.com/zsdonghao/tensorlayer/blob/master/example/tutorial_ptb_lstm_state_is_tuple.py]
            o, state = sess.run([y, net_rnn.final_state_decode],
                            {net_rnn.initial_state_decode: state,
                            decode_seqs2: [[start_id]]})
            w_id = tl.nlp.sample_top(o[0], top_k=1)
            w = idx2word[w_id]
            # Decode and feed state iteratively
            sentence = [w]
            for _ in range(len(seed_id) + 10): # max sentence length
                o, state = sess.run([y, net_rnn.final_state_decode],
                                {net_rnn.initial_state_decode: state,
                                decode_seqs2: [[w_id]]})
                w_id = tl.nlp.sample_top(o[0], top_k=1)
                w = idx2word[w_id]
                if w_id == end_id:
                    break
                sentence = sentence + [w]
            return " ".join([word for word in sentence if word is not '_'])

        def cleanup_function():
            # session cleanup
            sess.close()

        self.inference = inference_function
        self.cleanup = cleanup_function

        if inference_mode:
            self.logger.info('Test : خونه')
            sentence = self.inference('خونه')
            self.logger.info(f' > {sentence}')
            return

        seeds = ["بریم خونه",
                    "اونا میان",
                    "غذاش خیلی عالیه",
                    "نون",
                    "بازم ازش خرید میکنم، بهتریییییییییییییییییین منطقست.",
                    "چرا جدیدا اخر همه فیلما بی نتیجه تموم میشه الان تهش چی شد",
                    "اين دستگاه جزء اولين و شايد تنها سريه که تا الان از نسل چهارم سي پي يوهاي اينتل استفاده ميکنه"
                    ]
        for epoch in range(num_epochs):
            # try:
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
                #     self.logger.info(i, [idx2word[id] for id in X[i]])
                #     self.logger.info(i, [idx2word[id] for id in Y[i]])
                #     self.logger.info(i, [idx2word[id] for id in _target_seqs[i]])
                #     self.logger.info(i, [idx2word[id] for id in _decode_seqs[i]])
                #     self.logger.info(i, _target_mask[i])
                #     self.logger.info(len(_target_seqs[i]), len(_decode_seqs[i]), len(_target_mask[i]))
                _, loss_iter = sess.run([train_op, loss], {encode_seqs: X, decode_seqs: _decode_seqs,
                                target_seqs: _target_seqs, target_mask: _target_mask})
                total_loss += loss_iter
                n_iter += 1

            # printing average loss after every epoch
            self.logger.info('Epoch [{}/{}]: loss {:.4f}'.format(epoch + 1, num_epochs, total_loss / n_iter))
            
            # inference after every epoch
            for seed in seeds:
                # self.logger.info(f'Query > {seed}')
                # for _ in range(3):
                sentence = self.inference(seed)
                self.logger.info(f'> {sentence}')
            
            self.logger.info(f'> seq2seq model saved.')
            # saving the model
            tl.files.save_npz(net.all_params, name=self.model_path, sess=sess)
            # except Exception as e:
                # self.logger.exception(f'> Exception : {e}')
                # self.logger.info(f'> Seq2Seq training session destroyed.')
                # sess.close()
                # return
        self.logger.info(f'> Seq2Seq training session destroyed.')
        sess.close()


    def normalize(self, text_content):
        beg_ts = time.time()
        self.logger.info(f'>>> mohaverekhan-seq2seq-normalizer : \n{text_content}')
        text_content = cache.normalizers['mohaverekhan-replacement-normalizer']\
                            .normalize(text_content)
        self.logger.info(f'>> mohaverekhan-replacement-normalizer : \n{text_content}')

        text_content = self.inference(text_content)    
        end_ts = time.time()
        self.logger.info(f"> (Time)({end_ts - beg_ts:.6f})")
        self.logger.info(f'> Result : \n{text_content}')
        return text_content
        
    """
    Creates the LSTM Model
    """
    def create_model(self, encode_seqs, decode_seqs, src_vocab_size, emb_dim, is_train=True, reuse=False):
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
            self.logger.info(f'x : {x}')
            self.logger.info(f'y : {y}')
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
    def initial_setup(self):
        data_corpus_path = f'{self.current_dir}/'
        self.logger.info(f'data_corpus_path : {data_corpus_path}')
        metadata, idx_inf, idx_f = data.load_data(PATH=data_corpus_path)
        (trainX, trainY), (testX, testY), (validX, validY) = data.split_dataset(idx_inf, idx_f)
        trainX = tl.prepro.remove_pad_sequences(trainX.tolist())
        trainY = tl.prepro.remove_pad_sequences(trainY.tolist())
        testX = tl.prepro.remove_pad_sequences(testX.tolist())
        testY = tl.prepro.remove_pad_sequences(testY.tolist())
        validX = tl.prepro.remove_pad_sequences(validX.tolist())
        validY = tl.prepro.remove_pad_sequences(validY.tolist())
        self.logger.info('initial setup completed.')
        return metadata, trainX, trainY, testX, testY, validX, validY


    def process_data(self):
        data.process_data()

 
