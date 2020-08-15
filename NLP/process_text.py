from flaskblog.NLP.utils import *
import pandas as pd
from flask import session
import pyLDAvis.gensim

df_temp = pd.DataFrame()


def get_top_bigrams(df):
    # stack data into sentences inside data-frame
    df_data = get_sentences_df(df)

    # clean up data
    df_data['clean_data'] = df_data['sentences'].apply(cleanup_text)
    df_data = df_data[['clean_data']]

    # get phrases
    df_data = get_phrases(df_data)

    # generate and save wordcloud
    filename = save_wordcloud(df_data)
    session['wc_filename'] = filename

    # store phrased data in session for later access
    dict_phrases = df_data.to_dict('list')
    session['dict_phrases'] = dict_phrases

    # get top n bigrams
    top_bigrams = get_bigrams(df_data['phrase'], 300)
    df_bigrams = pd.DataFrame(top_bigrams, columns=['Text', 'count'])

    return df_bigrams


def get_main_topics(df):
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
    vis = pyLDAvis.gensim.prepare(lda_model, bow_corpus, dictionary=id2word)
    vis_filename = save_pyldavis(vis)
    # get topics from model and structure into dataframe
    topics_list = []
    for i in range(len(lda_model.print_topics())):
        topics_list.append(lda_model.print_topics()[i][1])

    final_topic_list = []
    for topic in topics_list:
        final_topic_list.append(clean_lda_topics(topic))

    df_topics = pd.DataFrame.from_records(final_topic_list).T

    return df_topics, vis_filename
