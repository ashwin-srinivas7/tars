from pathlib import Path

import io
from flask import render_template, url_for, flash, redirect, request, abort, session, send_file
from flaskblog import app, db, bcrypt
from flaskblog.NLP.process_text import *
from flaskblog.NLP.twitter_data import get_tweets, get_hashtags, get_tweet_year_month
from flaskblog.utils import save_text_file, save_picture, get_file_contents, get_dataframe, get_download_csv
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, TextFileUploadForm, TwitterForm
from flaskblog.models import User, Post, FileUpload
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd


# --------- CONTAINS ROUTE INFO FOR THE COMPLETE WEBSITE ------------ #


@app.route("/")
@app.route("/home")
def home():
    # posts = list(Post.query.all())  # get all posts from DB
    return render_template('home.html')


@app.route("/")
@app.route("/all_posts")
def all_posts():
    posts = list(Post.query.all())  # get all posts from DB
    return render_template('all_posts.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # check if user is already logged in
        return redirect(url_for('home'))

    # create instance of RegistrationForm
    form = RegistrationForm()

    # validate form
    if form.validate_on_submit():
        # hash password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # create instance of user with required attributes
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)

        # add the user to the current db session
        db.session.add(user)

        # commit changes so that it gets saved to the db
        db.session.commit()

        # once done, flash the message
        flash("Welcome {} - Your account has been created. You may log in now.".format(form.username.data), 'success')
        '''
        success code is used to specify the type of message to be flashed - this is a bootstrap input. Other options - 
        'danger' for unsuccessful flashes
        '''
        return redirect(url_for('login'))

    return render_template('register.html', title='Sign Up', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # check if user is already logged in
        return redirect(url_for('home'))

    # create instance of LoginForm
    form = LoginForm()

    # validate form
    if form.validate_on_submit():

        # retrieve user with specified email from DB
        user = User.query.filter_by(email=form.email.data).first()

        # check if email and password are valid
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)  # login the user
            flash('You\'ve been logged in', 'info')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))  # ternary condition
        else:
            flash('Please check email/ password and try again', 'danger')

    return render_template('login.html', title='Log In', form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash('You\'ve been logged out', 'info')
    return redirect(url_for('home'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    # create instance of UpdateAccountForm
    form = UpdateAccountForm()

    # validate form
    if form.validate_on_submit():  # for POST method

        if form.picture.data:  # check if picture is attached in the form

            # save picture in the specified path in the server and get modified name of the picture
            picture_new_name = save_picture(form_picture=form.picture.data, directory='profile_pics')
            print(form.picture.data)
            # update the name of the picture file in the DB
            current_user.image_file = picture_new_name

        # update username and email of current_user from form data
        current_user.username = form.username.data
        current_user.email = form.email.data

        # commit changes to DB
        db.session.commit()

        # flash message
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))  # redirect is used to avoid re-submission of form data

    elif request.method == 'GET':  # for GET method

        # auto-populate the form with current_users's data
        form.username.data = current_user.username
        form.email.data = current_user.email

    # get name of image file
    image_file = url_for('static', filename='profile_pics/{}'.format(current_user.image_file))

    return render_template('account.html', title='My Account',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, user_id=current_user.id)

        # add the user to the current db session
        db.session.add(post)

        # commit changes so that it gets saved to the db
        db.session.commit()

        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))

    return render_template('create_post.html', title='New Post', form=form, legend='Create New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post, legend='New Post')


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:  # check if author is the current_user before giving permission to edit post
        abort(403)  # 403 - HTTP code for unauthorized access

    # create the form
    form = PostForm()

    if form.validate_on_submit():  # if data is submitted through the form - for POST method
        # update the title and content from form
        post.title = form.title.data
        post.content = form.content.data

        # commit changes to DB
        db.session.commit()

        # flash message
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))  # redirect is used to avoid re-submission of form data

    elif request.method == 'GET':  # for GET method
        # auto-populate form with existing values
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    # get the post with post_id
    post = Post.query.get_or_404(post_id)

    # check if author is the current_user before giving permission to edit post
    if post.author != current_user:
        abort(403)  # 403 - HTTP code for unauthorized access

    # delete this post
    db.session.delete(post)
    db.session.commit()

    flash('Your post has been deleted!', 'info')
    return redirect(url_for('home'))


@app.route("/upload", methods=['GET', 'POST'])
@login_required
def user_upload():
    # create instance of TextFileUploadForm
    form = TextFileUploadForm()

    # validate form
    if form.validate_on_submit():
        filename = save_text_file(form.text_file.data)
        textfile = FileUpload(user_id=current_user.id, text_file=filename)
        db.session.add(textfile)
        db.session.commit()
        flash('File uploaded!', 'success')

        return redirect(url_for('top_n_grams'))
    return render_template('upload.html', title='Upload Text File', form=form, legend='Upload File')


@app.route("/top-n-grams", methods=['GET', 'POST'])
@login_required
def top_n_grams():
    # fetch most recent filename from DB for current user
    file_name = FileUpload.query.filter_by(user_id=current_user.id).all()[-1].text_file

    # get contents of file
    data = get_file_contents(file_name)

    # convert data into data-frame
    df_data = get_dataframe(data)

    # get top n bi-grams
    df_bigrams = get_top_bigrams(df_data)

    session["df_bigrams_upload"] = df_bigrams.to_csv(index=False, header=True, sep=",")

    return render_template('topics.html', title='Topics', data=df_bigrams)


@app.route("/download-bigrams-upload", methods=["POST"])
@login_required
def download_bigrams():
    # Get the CSV data as a string from the session
    csv = session["df_bigrams_upload"] if "df_bigrams_upload" in session else ""

    return get_download_csv(file=csv, f_name="bigrams")


@app.route("/download-topics-upload", methods=["POST"])
@login_required
def download_topics():
    dict_phrases = session["df_phrases"] if "df_phrases" in session else ""
    df_phrases = pd.DataFrame(dict_phrases)
    df_topics = get_main_topics(df_phrases)
    csv = df_topics.to_csv(index=False, header=True, sep=",")

    return get_download_csv(file=csv, f_name="topics")


@app.route("/twitter-search", methods=['GET', 'POST'])
@login_required
def twitter_search():
    form = TwitterForm()

    if form.validate_on_submit():
        session['text_query'] = str(form.text_query.data)
        df_tweets = get_tweets(text_query=str(form.text_query.data),
                               count=int(form.count.data))

        # store raw tweets in session for later access
        tweet_dict = df_tweets.to_dict('list')
        session['tweet_dict'] = tweet_dict

        # store raw tweets csv in session
        session["df_tweets"] = df_tweets.to_csv(index=False, header=True, sep=",")
        num_records = len(df_tweets)

        # get min and max dates
        tweet_min_date = min(df_tweets['datetime']).date()
        session['tweet_min_date'] = tweet_min_date

        tweet_max_date = max(df_tweets['datetime']).date()
        session['tweet_max_date'] = tweet_max_date

        # hashtag analysis
        df_hashtag_count = get_hashtags(df_tweets)

        # store hashtags in session
        dict_hashtag_count = df_hashtag_count.to_dict('list')
        session['dict_hashtag_count'] = dict_hashtag_count

        # save barplot in session
        df_hashtag_count_20 = df_hashtag_count.head(20)
        df_hashtag_count_20 = df_hashtag_count_20.sort_values(by='count')
        barplot_fname = save_barplot(df_hashtag_count_20)
        session['barplot_fname'] = barplot_fname

        # twitter timeline in session
        df_tweet_timeline = df_tweets[['id', 'datetime']]
        df_tweet_timeline['year_month'] = df_tweet_timeline['datetime'].apply(get_tweet_year_month)
        print(df_tweet_timeline.head())
        df_tweet_timeline = df_tweet_timeline.groupby(['year_month']).count().reset_index()[['year_month', 'id']]
        print(df_tweet_timeline.head(5))
        lineplot_fname = save_lineplot(df_tweet_timeline)
        session['lineplot_fname'] = lineplot_fname

        num_unique_words = session['num_unique_words'] if 'num_unique_words' in session else ""

        return render_template('download_tweets.html', title='Download Tweets', num_records=num_records,
                               search_query=form.text_query.data, num_words=num_unique_words,
                               barplot_fname=barplot_fname, lineplot_fname=lineplot_fname,
                               tweet_max_date=tweet_max_date, tweet_min_date=tweet_min_date)

    return render_template('get_tweets.html', title='Search Twitter', form=form, legend='Search Twitter')


@app.route("/download-tweets", methods=["POST"])
@login_required
def download_tweets():
    # Get the CSV data as a string from the session
    csv = session["df_tweets"] if "df_tweets" in session else ""

    return get_download_csv(file=csv, f_name="tweets")


@app.route("/get-top-bigrams", methods=["GET", "POST"])
@login_required
def get_top_bigrams_tweets():
    # get raw tweets from session
    tweet_dict = session['tweet_dict'] if 'tweet_dict' in session else ""
    df_tweets = pd.DataFrame(tweet_dict)

    df_tweets = df_tweets[['id', 'text']]
    df_tweets.columns = ['id', 'data']
    # get top-n-phrases
    df_bigrams = get_top_bigrams(df_tweets)

    # save dict of top bigrams in session
    dict_bigrams = df_bigrams.to_dict('list')
    session['dict_bigrams'] = dict_bigrams

    # get wordcloud from session
    wc_filename = session['wc_filename'] if 'wc_filename' in session else ""

    print(request.referrer)
    return render_template('top_bigrams.html', title='Top bi-grams', wordcloud_fname=wc_filename)


@app.route("/download-top-bigrams", methods=["GET", "POST"])
@login_required
def download_top_bigrams_tweets():
    # get top bigrams from session
    dict_bigrams = session['dict_bigrams'] if 'dict_bigrams' in session else ""
    df_bigrams = pd.DataFrame(dict_bigrams)

    csv = df_bigrams.to_csv(index=False, header=True, sep=",")

    return get_download_csv(file=csv, f_name="top-n-phrases")


@app.route("/pyLDAVis", methods=["GET", "POST"])
@login_required
def get_topics_tweets():
    # get phrases from session
    dict_phrases = session["dict_phrases"] if "dict_phrases" in session else ""
    df_phrases = pd.DataFrame(dict_phrases)

    # get topic & viz
    df_topics, vis_filename = get_main_topics(df_phrases)
    dict_topics = df_topics.to_dict('list')
    session['dict_topics'] = dict_topics
    vis_path = os.path.join(app.root_path, 'static\lda_vis', vis_filename)

    with open(vis_path, 'r') as file:
        data = file.read()

    return "{}".format(data)


@app.route("/download-topics-tweets", methods=["GET", "POST"])
@login_required
def download_topics_tweets():
    dict_topics = session['dict_topics'] if 'dict_topics' in session else ""
    df_topics = pd.DataFrame(dict_topics)
    csv = df_topics.to_csv(index=False, header=True, sep=",")

    return get_download_csv(file=csv, f_name="topics")


@app.route("/download_top-n-hashtags", methods=["GET", "POST"])
@login_required
def download_hashtags():
    dict_hashtag_count = session['dict_hashtag_count'] if 'dict_hashtag_count' in session else ""
    df_hashtag_count = pd.DataFrame(dict_hashtag_count)
    csv = df_hashtag_count.to_csv(index=False, header=True, sep=",")

    return get_download_csv(file=csv, f_name="top_hashtags")


@app.route("/tweet-analysis", methods=["GET", "POST"])
@login_required
def get_tweet_analysis_page():
    num_records = len(pd.DataFrame(session['tweet_dict']))
    print(num_records)
    search_query = session['text_query'] if 'text_query' in session else ""
    num_unique_words = session['num_unique_words'] if 'num_unique_words' in session else ""
    barplot_fname = session['barplot_fname'] if 'barplot_fname' in session else ""
    tweet_min_date = session['tweet_min_date'] if 'tweet_min_date' in session else ""
    tweet_max_date = session['tweet_max_date'] if 'tweet_max_date' in session else ""
    lineplot_fname = session['lineplot_fname'] if 'lineplot_fname' in session else ""

    return render_template('download_tweets.html', title='Download Tweets', num_records=num_records,
                           search_query=search_query, num_words=num_unique_words,
                           barplot_fname=barplot_fname, lineplot_fname=lineplot_fname,
                           tweet_max_date=tweet_max_date, tweet_min_date=tweet_min_date)
