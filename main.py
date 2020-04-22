from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql
pymysql.install_as_MySQLdb()
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
import math

with open("config.json","r") as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)

app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)


class Contacts(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg       = db.Column(db.String(120), nullable=False)
    date      = db.Column(db.String(12), nullable=True)
    email     = db.Column(db.String(20), nullable=False)

class Movies(db.Model):
    id                    = db.Column(db.Integer, primary_key=True)
    movie_title           = db.Column(db.String(100), nullable=False)
    director_name         = db.Column(db.String(100), nullable=False)
    movie_budget          = db.Column(db.Integer, nullable=False)
    world_wide_collection = db.Column(db.Integer, nullable=False)
    image                 = db.Column(db.String(100), nullable=True)
    movie_info            = db.Column(db.String(100), nullable=True)
    slug                  = db.Column(db.String(100), nullable=True)

################################################## home #####################################
@app.route("/")
def home():
    # flash("welcome to the world of technology", "success")
    # flash("This is Wajid Shaikh", "danger")

    # pagination logic
    # first - previous = blank
    #       - next = next + 1
    # middle- previous = previous - 1
    #       - next = next + 1
    # last  - previous = previous - 1
    #       - next = blank


    posts = Movies.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    # [0:params['no_of_posts']]

    page = request.args.get('page')
    if( not str(page).isnumeric()):
        page = 1
    page = int(page)

    posts = posts[(page - 1)*int(params['no_of_posts']) : (page - 1)*int(params['no_of_posts']) + int(params['no_of_posts'])]

    if(page == 1):
        prev = "#"
        next = "/?page="+ str(page + 1)
    elif(page == last):
        prev = "/?page="+ str(page - 1)
        next = "#"
    else:
        prev = "/?page="+ str(page - 1)
        next = "/?page="+ str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

########################################### about #############################################
@app.route("/about")
def about():
    return render_template('about.html', params=params)

########################################## contact ###########################################
@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email)
        db.session.add(entry)
        db.session.commit()

        # mail.send_message('New message from ' + name,
        #                   sender=email,
        #                   recipients = [params['gmail-user']],
        #                   body = message + "\n" + phone
        #                   )
        flash("Thankyou for contacting us ...", "success")
    return render_template('contact.html', params=params)

########################################## Post ###############################################
@app.route("/post/<string:post_slug>", methods = ["GET"])
def post_route(post_slug):
    post = Movies.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

########################################## Edit ##############################################
@app.route("/edit/<string:id>", methods = ['GET', 'POST'])
def edit(id):
    # if not ('user' in session and session['user'] == params['admin_user']):
    #     return redirect('/dashboard')

    if('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            movie_title           = request.form.get('movie_title')
            director_name         = request.form.get('director_name')
            movie_budget          = request.form.get('movie_budget')
            world_wide_collection = request.form.get('world_wide_collection')
            movie_info            = request.form.get('movie_info')
            slug                  = request.form.get('slug')
            f = request.files['image']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            image = f.filename
            if id == '0':
                post = Movies(movie_title=movie_title, director_name=director_name, movie_budget=movie_budget, world_wide_collection=world_wide_collection, image = image, movie_info=movie_info, slug=slug)
                db.session.add(post)
                db.session.commit()
            else:
                post = Movies.query.filter_by(id=id).first()
                post.movie_title           = movie_title
                post.director_name         = director_name
                post.movie_budget          = movie_budget
                post.world_wide_collection = world_wide_collection
                post.movie_info            = movie_info
                post.slug                  = slug
                post.image                 = image
                db.session.commit()
                return redirect('/edit/'+id)
                
        post = Movies.query.filter_by(id=id).first()
        return render_template('edit.html', params=params, post=post, id=id)
    # return render_template('edit.html', params=params, post=post)
###################################### dashboard ###############################################
@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if('user' in session and session['user'] == params['admin_user']):
        posts = Movies.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get('username')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            # set the session variable
            session['user'] = username
            posts = Movies.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)

# @app.route("/uploader", methods = ['GET', 'POST'])
# def uploader():
#     if request.method == 'POST':
#         f = request.files['image']
#         f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
#         return "Uploaded Successfully"

#################################### logout ###################################################
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

################################### delete ####################################################
@app.route("/delete/<string:id>", methods = ['GET', 'POST'])
def delete(id):
    if('user' in session and session['user'] == params['admin_user']):
        post = Movies.query.filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


app.run(debug=True)