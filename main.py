from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import datetime
from flask_login import login_user, login_required, LoginManager, current_user, logout_user, UserMixin, \
    AnonymousUserMixin
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL1")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.__init__(app)


# CONFIGURE TABLE
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(250), nullable=False, unique=False)
    name = db.Column(db.String(30), nullable=False, unique=False)
    blog_id = db.Column(db.Integer, nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)


db.create_all()


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class Login(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


@app.route('/')
def get_all_posts():
    posts_array = []
    posts = db.session.query(BlogPost).all()
    for post in posts:
        posts_array.append(post)

    return render_template("index.html",
                           all_posts=posts_array)


@app.route("/post/<int:index>", methods=["POST", "GET"])
def show_post(index):
    requested_post = BlogPost.query.get(index)
    form = CommentForm()
    if request.method == "POST":
        try:
            name = current_user.name
        except:
            return redirect(url_for("login"))
        else:
            comment = form.comment.data
            new_comment = Comment(comment=comment, name=name, blog_id=int(index))
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for("show_post", index=index))

    elif request.method == "GET":
        comments = Comment.query.filter_by(blog_id=int(index))
        return render_template("post.html", post=requested_post, form=form, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/newpost", methods=["POST", "GET"])
def new_post():
    form = CreatePostForm()

    if request.method == "POST":
        blog_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            author=form.author.data,
            img_url=form.img_url.data,
            date=f"{datetime.now().month}-{datetime.now().day}-{datetime.now().year}"
        )
        db.session.add(blog_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form)


@app.route("/edit/id/<int:id>", methods=["POST", "GET"])
def edit(id):
    form = CreatePostForm()
    post = BlogPost.query.get(id)

    if request.method == "GET":
        form.title.data = post.title
        form.subtitle.data = post.subtitle
        form.body.data = post.body
        form.author.data = post.author
        form.img_url.data = post.img_url
        return render_template("edit.html", form=form, id=id)

    elif request.method == "POST":
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        post.author = form.author.data
        post.img_url = form.img_url.data
        db.session.commit()
        return redirect(url_for('get_all_posts'))


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        hash_password = generate_password_hash(password=form.password.data,
                                               salt_length=8)

        new_user = User(email=form.email.data,
                        name=form.name.data,
                        password=hash_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("get_all_posts"))

    elif request.method == "GET":
        return render_template("register.html", form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = Login()

    if request.method == "POST":
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if check_password_hash(pwhash=user.password, password=password):
            login_user(user=user)
            return redirect(url_for("get_all_posts"))

    elif request.method == "GET":
        return render_template(template_name_or_list="login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    login_user()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
