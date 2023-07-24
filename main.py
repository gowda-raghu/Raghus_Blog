from flask import Flask, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm
from flask_gravatar import Gravatar
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm,ContactForm
from functools import wraps
from flask import abort
from flask_gravatar import Gravatar


def admin_only(f):
    @wraps(f)
    def dec(*args,**kwargs):
        if current_user.id!=1:
            return abort(403)
        return f(*args,**kwargs)
    return dec

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager=LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id=db.Column(db.Integer,db.ForeignKey("user.id"))
    # author = db.Column(db.String(250), nullable=False)
    author=relationship('User',back_populates='posts')
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments=relationship("Comment",back_populates="parent_post")
# db.create_all()

class User(UserMixin,db.Model):
    __tablename__="user"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100),unique=True)
    password=db.Column(db.String(100))
    posts=relationship('BlogPost',back_populates='author')
    comments=relationship("Comment",back_populates="comment_author")

class Comment(UserMixin,db.Model):
    __tablename__="comments"
    id=db.Column(db.Integer,primary_key=True)
    text=db.Column(db.Text,nullable=False)
    author_id=db.Column(db.Integer,db.ForeignKey("user.id"))
    comment_author=relationship("User",back_populates="comments")
    post_id=db.Column(db.Integer,db.ForeignKey("blog_posts.id"))
    parent_post=relationship("BlogPost",back_populates="comments")

class Contact(UserMixin,db.Model):
    __table__name="contact"
    id=db.Column(db.Integer,primary_key=True)
    author_id=db.Column(db.Integer,db.ForeignKey("user.id"))
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100),nullable=False)
    phone=db.Column(db.String(15),nullable=False)
    message=db.Column(db.Text,nullable=False)


db.create_all()
# num_rows_deleted = db.session.query(Comment).delete()
# db.session.commit()
# num_rows_deleted = db.session.query(Contact).delete()
# db.session.commit()

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)



@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts,logged_in=current_user.is_authenticated)


@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        password=generate_password_hash(form.password.data,method='pbkdf2:sha256',salt_length=8)
        email=form.email.data
        name=form.name.data
        user=User.query.filter_by(email=email).first()
        if user:
            flash("User account already exists!")
            return redirect(url_for("login"))
        new_user=User(
            name=name,
            email=email,
            password=password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html",form=form)


@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data
        user=User.query.filter_by(email=email).first()
        if not user:
            flash("Email doesn't exist! Please register.")
            return redirect(url_for("register"))
        if check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for("get_all_posts"))
        else:
            flash("Password doesn't match! Please try again.")
            return redirect(url_for("login"))
    return render_template("login.html",form=form,logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['GET','POST'])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comments = Comment.query.all()
    form=CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Please login to comment!")
            return redirect(url_for("login"))
        text=form.body.data
        comment=Comment(
            text=text,
            author_id=current_user.id,
            post_id=post_id
            )
        db.session.add(comment)
        db.session.commit()
        return render_template("post.html", form=form,comments=comments,post=requested_post,logged_in=current_user.is_authenticated)
    return render_template("post.html", form=form,comments=comments,post=requested_post,logged_in=current_user.is_authenticated)


@app.route("/about")
def about():
    return render_template("about.html",logged_in=current_user.is_authenticated)


@app.route("/contact",methods=['GET','POST'])
def contact():
    form=ContactForm()
    if form.validate_on_submit():
        name=form.name.data
        email=form.email.data
        message=form.message.data
        phone=form.phone.data
        if not current_user.is_authenticated:
            flash("Please login to Contact!")
            return redirect(url_for("login"))
        cont= Contact(
            author_id=current_user.id,
            name=name,
            phone=phone,
            email=email,
            message=message
        )
        db.session.add(cont)
        db.session.commit()
        return redirect(url_for('contact'))




    return render_template("contact.html",form=form,logged_in=current_user.is_authenticated)


@app.route("/new-post",methods=['GET','POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            author_id=current_user.id,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,logged_in=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>",methods=['GET','POST'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author_id=post.author_id,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author_id = current_user.id
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form,logged_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000,debug=True)
    app.run(debug=True)