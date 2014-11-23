#!/usr/bin/env python
#coding: utf-8
import logging
import os
import os.path
import re

import gensim.corpora
import nltk
import nltk.corpus
import nltk.data
from nltk.tokenize import RegexpTokenizer

from skim import logging_to_console
from skim.configuration import STORAGE_ROOT
from skim.entries import entries_root


logger = logging.getLogger()


def topics_path():
    path = os.path.join(STORAGE_ROOT, 'topics')
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def dictionary_filename():
    return os.path.join(topics_path(), 'corpus.dict')

def corpus_matrix_filename():
    return os.path.join(topics_path(), 'corpus.mm')

def tfidf_filename():
    return os.path.join(topics_path(), 'tfidf')

def lsi_filename():
    return os.path.join(topics_path(), 'lsi.model')

def lda_filename():
    return os.path.join(topics_path(), 'lda.model')

def hdp_filename():
    return os.path.join(topics_path(), 'hdp.model')

def ensure_nltk_data():
    nltk_data_storage = os.path.join(STORAGE_ROOT, 'nltk')
    if not os.path.exists(nltk_data_storage):
        os.makedirs(nltk_data_storage)
    if nltk_data_storage not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_storage)

    if not os.path.exists(os.path.join(nltk_data_storage, 'tokenizers', 'punkt')):
        nltk.download('punkt', download_dir=nltk_data_storage)

    if not os.path.exists(os.path.join(nltk_data_storage, 'corpora', 'stopwords')):
        nltk.download('stopwords', download_dir=nltk_data_storage)

code_pattern = re.compile(r'`[^\n]+?`')
url_pattern = re.compile(r'(https?://+[\w\d/\-_\.&?=%]+)')
number_pattern = re.compile(r'([\+\-]?\d+(\.\d+)?)')
word_pattern = re.compile(r'[a-zA-Z0-9\'\-]+')
tokenizer = RegexpTokenizer('|'.join(pattern.pattern for pattern in
                                     [code_pattern, url_pattern, number_pattern, word_pattern]))

class SkimCorpus(object):
    def __iter__(self):
        stopwords = set(nltk.corpus.stopwords.words('english'))
        for root, _, filenames in os.walk(entries_root()):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                with open(full_path, 'r') as entry_file:
                    title = entry_file.readline().strip()
                    entry_file.readline()  # skip URL
                    body = entry_file.read()

                    tokens = tokenizer.tokenize(title + '\n' + body)
                    tokens = [token.lower() for token in tokens if token not in stopwords]
                    tokens = [token for token in tokens if not url_pattern.match(token)]
                    tokens = [token for token in tokens if not number_pattern.match(token)]
                    yield full_path, tokens

if __name__ == '__main__':
    logging_to_console(logging.getLogger(''))
    ensure_nltk_data()

    corpus_reader = SkimCorpus()

    if os.path.exists(dictionary_filename()):
        dictionary = gensim.corpora.Dictionary.load(dictionary_filename())
    else:
        dictionary = gensim.corpora.Dictionary((tokens for _, tokens in corpus_reader))
        dictionary.save(dictionary_filename())

    if not os.path.exists(corpus_matrix_filename()):
        documents = [dictionary.doc2bow(tokens) for _, tokens in corpus_reader]
        gensim.corpora.MmCorpus.serialize(corpus_matrix_filename(), documents)
    corpus = gensim.corpora.MmCorpus(corpus_matrix_filename())
    logger.info(corpus)

    import gensim.models
    if not os.path.exists(tfidf_filename()):
        tfidf = gensim.models.TfidfModel(corpus, normalize=False)
        tfidf.save(tfidf_filename())
    else:
        tfidf = gensim.models.TfidfModel.load(tfidf_filename())
    logger.info(tfidf)

    tfidf_corpus = tfidf[corpus]

    NUM_TOPICS = 50

    import gensim.models.lsimodel
    if not os.path.exists(lsi_filename()):
        lsi = gensim.models.LsiModel(tfidf_corpus, id2word=dictionary, num_topics=NUM_TOPICS)
        lsi.save(lsi_filename())
    else:
        lsi = gensim.models.LsiModel.load(lsi_filename())
    logger.info(lsi)
    #lsi.print_debug(20)

    # import gensim.models.ldamodel
    # if not os.path.exists(lda_filename()):
    #     lda = gensim.models.LdaModel(corpus, id2word=dictionary, num_topics=NUM_TOPICS)
    #     lda.save(lda_filename())
    # else:
    #     lda = gensim.models.LdaModel.load(lda_filename())
    # logger.info(lda)
    # lda.print_topics(NUM_TOPICS)

    import gensim.similarities
    index_filename = os.path.join(topics_path(), 'similarity')
    if not os.path.exists(index_filename):
        index = gensim.similarities.Similarity(index_filename, lsi[tfidf_corpus], NUM_TOPICS)
        index.save(index_filename)
    else:
        index = gensim.similarities.Similarity.load(index_filename)

    documents = [filename for filename, _ in corpus_reader]

    index.num_best = 25

    query = 'bitcoin litecoin'
    query_doc = dictionary.doc2bow(query.lower().split())
    query_vec = lsi[tfidf[query_doc]]
    print('Results for %r' % query)
    for document, similarity in index[query_vec]:
        print(similarity, documents[document])

