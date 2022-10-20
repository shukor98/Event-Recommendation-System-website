from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import User, Post, RSVP #, Recommend
from . import db

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

views = Blueprint("views", __name__)

@views.route("/")
@views.route("/home")
@login_required
def home():
    posts = Post.query.all()
    return render_template("home.html", user=current_user, posts=posts)

@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        text = request.form.get('text')

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(text=text, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('create_post.html', user=current_user)

@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash('Post does not exist.', category='error')
    elif current_user.id != post.author:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted!', category='success')

    return redirect(url_for('views.home'))

@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exist.', category='error')
        return redirect(url_for('views.home'))

    posts = Post.query.filter_by(author=user.id).all()
    return render_template("posts.html", user=current_user, posts=posts, username=username)

@views.route("/rsvp/<post_id>" )#, methods=['POST'])
@login_required
def rsvp(post_id):
    post = Post.query.filter_by(id=post_id).first()
    rsvp = RSVP.query.filter_by(author=current_user.id, post_id=post_id).first()

    if not post:
        #flash('Post does not exist.', category='error')
        return jsonify({'error':'Post does not exist.'}, 400)
    elif rsvp:
        db.session.delete(rsvp)
        db.session.commit()
    else:
        rsvp = RSVP(author=current_user.id, post_id=post_id)
        db.session.add(rsvp)
        db.session.commit()

    return redirect(url_for('views.home'))
    #return jsonify({"rsvp":len(post.rsvp), "rsvped":current_user.id in map(lambda x: x.author, post.rsvp)})


'''
bermulanya model utk recommendation system
'''

# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, inspect, func

#engine = create_engine('sqlite:////home/shukor/Desktop/FYP/recommendation/website/database.db')
engine = create_engine('sqlite:///website/database.db')
engine.connect()
session=Session(engine)

@views.route("/recomm/<user_id>")
@login_required
def recomm(user_id):
    user = User.query.filter_by(id=user_id).first()
    rsvp_check = RSVP.query.filter_by(author=current_user.id).first()

    if not user:
        flash('No user with that username exist.', category='error')
        return redirect(url_for('views.home'))
    if not rsvp_check:
        flash('You dont have any recommendation, like any post first.', category='error')
        return redirect(url_for('views.home'))

    query = session.query(RSVP)
    rsvp = pd.read_sql(query.statement, session.bind)

    for i in range(len(rsvp)):
        rsvp['rsvp_value'] = 1

    df_rsvp = rsvp.pivot(index='author', columns='post_id', values='rsvp_value')
    df_rsvp_dummy = df_rsvp.copy().fillna(0)

    item_similarity_df = df_rsvp_dummy.corr(method='pearson')

    def get_similar_post(post_id, rsvp):
        similar_score = item_similarity_df[post_id]*(rsvp)#-2.5)
        similar_score = similar_score.sort_values(ascending=False)

        return similar_score

    query = session.query("post_id from RSVP where author ="+user_id)
    user_data = pd.read_sql(query.statement, session.bind)

    user_data_df = pd.DataFrame(data=user_data)
    for i in range(len(user_data_df)):
        user_data_df['rsvp_value'] = 1

    user_data_list = user_data_df.to_records(index=False)
    result = list(user_data_list)

    similar_post = pd.DataFrame()

    for post,rsvp in result:
        similar_post = similar_post.append(get_similar_post(post,rsvp), ignore_index=True)

    recommend_value = list(similar_post.sum())
    recommend = pd.DataFrame()

    index = similar_post.sum().sort_values(ascending=False).head(5).index
    #index = index.head()

    #query = session.query(Post)
    #post = pd.read_sql(query.statement, session.bind)
    #posts_recommend = pd.DataFrame()

    #count = 1

    #for i in index:

    #    for j in range(len(post)+1):
    #        if j == i :
    #            query = session.query("* from post where id="+str(i))
    #            post_query = pd.read_sql(query.statement, session.bind)
    #            posts_recommend = posts_recommend.append(post_query)

                #recomm = Recommend.query.filter_by(author=current_user.id, post_id = j)#.first()

                #if not recomm:
                #    recommend = Recommend(user=current_user.id, post_id=j, rank= count)
                #    db.session.add(recommend)
                #    db.session.commit()
                #else:
                #    recommend.rank= count
                #    db.session.commit()

    #    count = count+1

    #count = 0
    #posts_recommend = posts_recommend.reset_index(drop=True)

                #recommend = Recommend(post_id=posts['id'], text=posts['text'], date_created=posts['date_created'], author=posts['author'])
                #recommend = Recommend(post_id=post_query['id'], text=post_query['text'], author=post_query['author'])
                #date_created=post_query['date_created']
                #db.session.add(recommend)
                #db.session.commit()

    ## convert dataframe in sqlite
    #posts.to_sql('Recommend', engine, if_exists='append', index=False)
    #recommends = Recommend.query.filter_by(author=current_user.id)
    #return posts_recommend.to_html()
    posts = Post.query.all()
    return render_template("recommendation.html", user=current_user, posts=posts, rsvp=index, username=current_user.username)