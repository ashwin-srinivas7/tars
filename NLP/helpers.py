"""
Helpers for NLP/utils.py module
"""
from nltk.corpus import stopwords
import gensim
from gensim import corpora, models
import re
import string


def get_sentences(text):
    """
    Function to tokenize text into sentences
    Input: The entire file
    Output: List of sentences in the review
    """
    text = str(text)
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)


def get_stopwords():
    stop_words = set(stopwords.words("english"))
    words_to_include = ['not', 'didn', "didn't", 'doesn', "doesn't", 'no']
    words_to_remove = ['would', 'should', 'could', 'the', 'i', 'u', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                       'k', 'l', 'm', 'n', 'o', 'p',
                       'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'ive']

    stop_words = [word for word in stop_words if word not in words_to_include]
    stop_words = set(stop_words)
    stop_words = list(stop_words.union(words_to_remove))
    return stop_words


def bigram_phrase(text, bigram_mod):
    """
    Funtion returns bi-gram phrases in the review
    Input - review, bigram model
    Output - list of bi-gram phrases
    """
    return bigram_mod[text]


def get_tokens(text):
    """
    Funtion to tokenize reviews
    Input - String of review text
    Output - List of tokens in the review
    """
    text = str(text)
    tokens = text.split()
    return tokens


def trigram_phrase(text, trigram_mod, bigram_mod):
    """
    Funtion returns tri-gram phrases in the review
    Input - review, trigram model and bigram model
    Output - List of tri-gram phrases in the review
    """
    return ' '.join(trigram_mod[bigram_mod[text]])


def clean_lda_topics(review):
    """
    Funtion to clean up the LDA output
    """
    words = review.split('+')
    # remove punctuation characters
    alphabets = [char for char in words if char not in string.punctuation]

    # join each word and then split at spaces
    words_list = "".join(alphabets).split()

    # remove numbers
    words_list = [re.sub("(\\d|\\W)+", "", word) for word in words_list]

    return words_list


def transform_review(df):
    """
    Funtion to transform token_list to BOW and TF-IDF Corpuses

    Input - DataFrame with tokenized reviews

    Returns - 1. dictionary (ID representation for each unique token)
              2. BOW Corpus
              3. TF-IDF Corpus
    """
    # assign each word in the corpus a unique ID
    id2word = gensim.corpora.Dictionary(df['tokens'])

    # apply filters to remove specified portion of words
    id2word.filter_extremes(no_below=15, no_above=0.6, keep_n=100000)

    # convert each review document into a BOW representation based on the above created dictionary
    bow_corpus = [id2word.doc2bow(doc) for doc in df['tokens']]

    # from BOW corpus, create a tf-idf model
    tfidf = models.TfidfModel(bow_corpus)

    # transform the entire corpus with TF-IDF scores
    tfidf_corpus = tfidf[bow_corpus]

    return id2word, bow_corpus, tfidf_corpus
