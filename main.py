from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Table, ForeignKey, Integer
from typing import List
from sqlalchemy.orm import relationship, Mapped, mapped_column
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='wavatar',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(db.String(100), nullable=False)
    password: Mapped[str] = mapped_column(db.String(100), nullable=False)
    name: Mapped[str]= mapped_column(db.String(100), nullable=False)
    posts: Mapped[List['BlogPost']]=relationship(back_populates='author')
    comments: Mapped[List['Comment']] = relationship(back_populates='comment_author')
# with app.app_context():
#     db.create_all()


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title :Mapped[str] = mapped_column(db.String(250), unique=True, nullable=False)
    subtitle : Mapped[str] = mapped_column(db.String(250), nullable=False)
    date : Mapped[str] = mapped_column(db.String(250), nullable=False)
    body : Mapped[str] = mapped_column(db.Text, nullable=False)
    img_url : Mapped[str] = mapped_column(db.String(500), nullable=False)
    author_id:Mapped[int]= mapped_column(ForeignKey('users.id'))
    author:Mapped['User'] = relationship(back_populates='posts')
    # blogpost_comments: Mapped[List['Comment']]=relationship()
    blogpost_comments: Mapped[List['Comment']]=relationship(back_populates='blogypost')
# with app.app_context():
#     db.create_all()

class Comment(db.Model):
    __tablename__='comments'
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(db.String(30000), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    blogpost_id: Mapped[int] = mapped_column(ForeignKey('blog_posts.id'))
    comment_author: Mapped['User'] = relationship(back_populates= 'comments')
    blogypost: Mapped['BlogPost']=relationship(back_populates='blogpost_comments')
# with app.app_context():
#     db.create_all()
#

# x = BlogPost(
#             title="The Life of Cactus",
#             subtitle='Who knew that cacti lived such interesting lives.',
#             date='October 20, 2020',
#             body='<p>Cacti are adapted to live in very dry environments, '
# 'including the Atacama Desert, one of the driest places on Earth. Because of this, cacti show many adaptations '
#     'to conserve water. For example, almost all cacti are succulents, meaning they have thickened, fleshy parts adapted '
#     'to store water. Unlike many other succulents, '
#                      'the stem is the only part of most cacti where this vital process takes place. '
#     'Most species of cacti have lost true leaves, retaining only spines, which are highly modified leaves.</p>',
#             img_url='https://images.unsplash.com/photo-1530482054429-cc491f61333b?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1651&q=80',
#             author_id=1,
# )
# with app.app_context():
#     new_blogpost=x
#     db.session.add(new_blogpost)
#     db.session.commit()

with app.app_context():
    result=db.session.execute(db.select(User))
    users = result.scalars().all()
    emails_list=[user.email for user in users]
    print(users)
    print(emails_list)

def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.id!=1 or not current_user.is_authenticated:
            return abort(403)
        return function(*args, **kwargs)
    return wrapper_function

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        email=form.Email.data
        if email in emails_list:
            flash("You've already registered with that email address, login instead!")
            return redirect(url_for('login'))
        else:
            password=generate_password_hash(form.Password.data, method='pbkdf2:sha256', salt_length=8)
            print(password)
            with app.app_context():
                new_user=User(name=form.Name.data, password=password,email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        if form.Email.data in emails_list:
            with app.app_context():
                user = db.session.execute(db.select(User).where(User.email == form.Email.data)).scalar()
            if check_password_hash(user.password, form.Password.data) is True:
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash('The password is incorrect, please try again!')
                return redirect(url_for('login'))
        else:
            flash("This email doesn't exist, please try again!")
            return redirect(url_for('login'))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    form=CommentForm()
    if form.validate_on_submit():
        print(form.body.data)
        if current_user.is_authenticated:
            with app.app_context():
                new_comment = Comment(text=form.body.data, author_id=current_user.id, blogpost_id=post_id)
                db.session.add(new_comment)
                db.session.commit()
        else:
            flash("You need to log in or register to comment!")
            return redirect(url_for('login'))

    requested_post = BlogPost.query.get(post_id)
    print(requested_post)
    for comment in requested_post.blogpost_comments:
        print(comment.text)
        print(comment.comment_author.name)
    return render_template("post.html", post=requested_post, form=form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post")
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
