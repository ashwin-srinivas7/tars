from flask import session
import GetOldTweets3 as got
import pandas as pd
import datetime
from sklearn.feature_extraction.text import CountVectorizer


def get_tweets(text_query,
               count=20,
               since=str(datetime.date.today() + datetime.timedelta(days=-10000)),
               until=str(datetime.date.today())
               ):
    text_query = str(text_query)
    count = int(count)
    tweet_criteria = got.manager.TweetCriteria().setQuerySearch(text_query) \
        .setMaxTweets(count) \
        .setSince(since) \
        .setUntil(until) \
        .setLang('en')
    tweets = got.manager.TweetManager.getTweets(tweet_criteria)

    # Creating list of chosen tweet data
    text_tweets = [[tweet.id, tweet.username, tweet.date, tweet.text, tweet.hashtags] for tweet in tweets]

    # structure results into dataframe
    df_tweets = pd.DataFrame()
    df_tweets['id'] = [int(tweet[0]) for tweet in text_tweets]
    df_tweets['username'] = [str(tweet[1]) for tweet in text_tweets]
    df_tweets['datetime'] = [tweet[2] for tweet in text_tweets]
    df_tweets['text'] = [tweet[3] for tweet in text_tweets]
    df_tweets['hashtags'] = [tweet[4].split() for tweet in text_tweets]

    # get number of unique words
    words_list = list(df_tweets['text'])
    cv = CountVectorizer()
    cv_fit = cv.fit_transform(words_list)
    session['num_unique_words'] = len(cv.get_feature_names())

    return df_tweets


def get_hashtags(df_tweets):
    df_tweets_hashtags = df_tweets[["id", "hashtags"]]
    df_hashtag_list = pd.DataFrame.from_records(df_tweets_hashtags['hashtags'].tolist()).stack().reset_index(
        level=1,
        drop=True).rename(
        'hashtags')
    df_tweets_hashtags = df_tweets_hashtags.drop('hashtags', axis=1).join(df_hashtag_list).reset_index(drop=True)[
        ['id', 'hashtags']].dropna(subset=['hashtags'])
    df_hashtag_count = df_tweets_hashtags.groupby(['hashtags']).count().reset_index()[['hashtags', 'id']]
    df_hashtag_count.columns = ['hashtags', 'count']
    df_hashtag_count.sort_values(by='count', ascending=False, inplace=True)
    return df_hashtag_count


def get_tweet_year_month(date_time):
    return str(date_time.date())[0:7]
