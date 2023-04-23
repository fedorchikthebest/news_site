from flask import Flask, render_template, redirect, abort, request
from data import db_session
from data.users import User
from data.games import Games
from forms.user import RegisterForm
from forms.games import GamesForm
from forms.login_form import LoginForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import requests

login_manager = LoginManager()
app = Flask(__name__)
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'lJihdIUh12eIHUI34'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000


@app.route("/")
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(Games)
    return render_template("index.html", news=news)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = GamesForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = Games()
        news.title = form.title.data
        news.content = form.content.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect(f'/load_files/{current_user.id}')
    return render_template('news.html', title='Добавление игры',
                           form=form)


@app.route('/load_files/<int:id>', methods=['GET', 'POST'])
@login_required
def load_file(id):
    if request.method == 'POST':
        db_sess = db_session.create_session()
        news = db_sess.query(Games).filter(Games.id == id, Games.user == current_user).first()
        news.immage = request.files['immage'].read()
        news.torrent = request.files['torrent'].read()
        db_sess.merge(news)
        db_sess.commit()
        return redirect('/')
    return render_template('load_file.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = GamesForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(Games).filter(Games.id == id,
                                           Games.user == current_user
                                           ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(Games).filter(Games.id == id,
                                           Games.user == current_user
                                           ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            db_sess.commit()
            return redirect(f'/load_files/{id}')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование игры',
                           form=form
                           )


@app.route('/news_delete/<int:id>', methods=['GET'])
@login_required
def delete_news(id):
    form = GamesForm()
    db_sess = db_session.create_session()
    news = db_sess.query(Games).filter(Games.id == id, Games.user == current_user).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
        return redirect('/')
    else:
        abort(404)


@app.route('/game/<int:id>', methods=['GET'])
def render_game(id):
    form = GamesForm()
    db_sess = db_session.create_session()
    news = db_sess.query(Games).filter(Games.id == id).first()
    comments = requests.get(f'http://92.51.38.221:5000/api/{id}').json()
    comments_2 = []
    for i in comments:
        comments_2.append([list(i.keys())[0], list(i.values())[0]])
    if not news:
        abort(404)
    with open(f'./static/img/{id}.png', 'wb') as f:
        if news.immage is not None:
            f.write(news.immage)
    with open(f'./static/torrents/{id}.torrent', 'wb') as f:
        if news.torrent is not None:
            f.write(news.torrent)
    if news:
        return render_template('game.html', data=news, comments=comments_2)
    else:
        abort(404)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
