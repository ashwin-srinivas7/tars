"""
Utils.py module contains the utility functions for text processing with NLP
Contains function definitions for process_text.py

"""
from flask import session, url_for
from flaskblog.NLP.helpers import *
import os
from flaskblog import app
import unidecode
import re
import string
import pandas as pd
import spacy
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud
import matplotlib

import matplotlib.pyplot as plt
import secrets
import gensim
from gensim.models import CoherenceModel
import pyLDAvis.gensim

matplotlib.use('Agg')       # for displaying large vis files


# main code
stop_words = get_stopwords()

nlp = spacy.load('en_core_web_sm')


def get_bigrams(corpus, n=20):
    vec = CountVectorizer(ngram_range=(2, 3)).fit(corpus)
    bag_of_words = vec.transform(corpus)
    sum_words = bag_of_words.sum(axis=0)
    words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    return words_freq[:n]


def get_sentences_df(df_test):
    df_test['sentences'] = df_test['data'].apply(get_sentences)
    df_sentence_list = pd.DataFrame.from_records(df_test['sentences'].tolist()).stack().reset_index(level=1,
                                                                                                    drop=True).rename(
        'sentences')
    df_test = df_test.drop('sentences', axis=1).join(df_sentence_list).reset_index(drop=True)[['sentences']]
    return df_test


allowed_pos_tags = ['NOUN', 'VERB', 'PROPN']


# function to clean the review_text
def cleanup_text(review):
    review = str(review)
    review = re.sub(r'https?://\S+', ' ', review)  # replace all URLs with space
    review = re.sub(r'#\S+', ' ', review)  # replace all hashtags with space
    review = re.sub(r'@\S+', ' ', review)  # replace all usernames with space

    # remove accents from words
    # review_clean = unicodedata.normalize('NFKD', review_clean).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    review = unidecode.unidecode(review)

    # replace punctuations with space
    list1 = [char for char in review]
    list2 = [' ' if char in string.punctuation else char for char in list1]
    words_list = ''.join(list2).split()

    # remove digits and special characters
    words_list = [re.sub("(\\d|\\W)+", " ", word) for word in words_list]

    # convert words to lower case
    words_list = [word.lower() for word in words_list]

    review = ' '.join(words_list)
    # filter words with POS filtering and lemmatize words
    review = nlp(review)
    review = ' '.join(
        [word.lemma_ if word.lemma_ != '-PRON-' else word.text for word in review if word.pos_ in allowed_pos_tags])

    words_list = review.split()

    # remove stop words
    review_clean = ' '.join([word for word in words_list if word not in stop_words])

    # remove extra whitespace
    review_clean = re.sub('  +', ' ', review_clean)

    review_clean = str(review_clean)
    return review_clean


def get_phrases(df_test):
    # tokenize the reviews
    df_test['tokens'] = df_test['clean_data'].apply(get_tokens)
    df_test = df_test[['tokens']]
    # tokens = list(df_test['tokens'])

    # Build the bigram and trigram models
    bigram = gensim.models.Phrases(df_test['tokens'], min_count=15, threshold=100)  # higher threshold fewer phrases.
    trigram = gensim.models.Phrases(bigram[df_test['tokens']], threshold=100)

    # Faster way to get a sentence clubbed as a trigram/bigram
    bigram_mod = gensim.models.phrases.Phraser(bigram)
    trigram_mod = gensim.models.phrases.Phraser(trigram)

    df_test['phrase'] = df_test['tokens'].apply(trigram_phrase, trigram_mod=trigram_mod, bigram_mod=bigram_mod)
    df_test = df_test[['phrase']]

    return df_test


def get_topics(df):
    df['tokens'] = df['phrase'].apply(get_tokens)
    df = df[['tokens']]
    id2word, bow_corpus, tfidf_corpus = transform_review(df)
    lda_model = gensim.models.ldamodel.LdaModel(corpus=bow_corpus,
                                                id2word=id2word,
                                                num_topics=7,
                                                random_state=100,
                                                update_every=1,
                                                chunksize=100,
                                                passes=10,
                                                alpha='auto',
                                                per_word_topics=True)

    # get topics from model and structure into dataframe
    topics_list = []
    for i in range(len(lda_model.print_topics())):
        topics_list.append(lda_model.print_topics()[i][1])

    final_topic_list = []
    for topic in topics_list:
        final_topic_list.append(clean_lda_topics(topic))

    df_topics = pd.DataFrame.from_records(final_topic_list).T

    return df_topics


def save_wordcloud(df_data):
    phrases = ''.join(list(df_data['phrase']))
    wordcloud = WordCloud(width=512, height=512, max_words=150, background_color="white").generate(phrases)
    filename = secrets.token_hex(8) + '.png'
    full_path = os.path.join(app.root_path, 'static/wordclouds', filename)
    wordcloud.to_file(full_path)
    return filename


def save_barplot(df_data):
    df_data = df_data.sort_values(by='count')
    filename = secrets.token_hex(8) + '.png'
    full_path = os.path.join(app.root_path, 'static/hashtags', filename)

    # plot the fig
    plt.figure(figsize=[12, 9])
    plt.barh(list(df_data['hashtags']), list(df_data['count']), color='grey')
    plt.xlabel('Total Count')
    plt.ylabel('Hashtags')
    plt.title('Top 20 hashtags')
    plt.savefig(full_path)
    return filename


def save_lineplot(df_data):
    filename = secrets.token_hex(8) + '.png'
    full_path = os.path.join(app.root_path, 'static/twitter_timeline', filename)
    plt.figure(figsize=[20, 5])
    plt.xlabel('YYYY-MM')
    plt.ylabel('# of Tweets')
    plt.plot(list(df_data['year_month']), list(df_data['id']), color='darkblue')
    plt.savefig(full_path)
    return filename


def save_pyldavis(vis):
    filename = secrets.token_hex(8) + '.html'
    full_path = os.path.join(app.root_path, 'static/lda_vis', filename)
    pyLDAvis.save_html(vis, full_path)
    return filename
