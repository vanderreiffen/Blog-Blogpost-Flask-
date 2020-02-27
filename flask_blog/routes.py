from flask import Flask, escape, request, render_template,url_for, flash, redirect, abort
from flask_blog import app, db, bcrypt, mail
from flask_blog.forms import RegistrationForm, LoginForm, PostForm, RequestResetForm, ResetPasswordForm
from flask_blog.models import User,Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message



@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    posts= Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
    return render_template( 'home.html', posts =posts)

@app.route('/about')
def about():
    return render_template( 'about.html',title='About')


@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data , email =form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to login!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html',title='Register',form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user,remember=form.remember.data)
            next_page =request.args.get('next')
            return  redirect (next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email / pass','danger')
    return render_template('login.html',title='Login',form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/account')
@login_required
def account():
    image_file = url_for('static', filename='profile_pic/' + current_user.image_file)
    return render_template('account.html',title='Account', image_file= image_file)


@app.route('/post/new',methods=['GET','POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data , content=form.content.data, author =current_user)
        db.session.add(post)
        db.session.commit()

        flash('Your post has been created', 'sucess')
        return redirect(url_for('home'))
    return render_template('create_post.html',title='New Post', form = form, legend='New Post')

@app.route('/post/<post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route('/post/<int:post_id>/update', methods=['GET','POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash ('Your post has beeen updated', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        
    return render_template('create_post.html',title='Update Post', form = form, legend='Update Post')
    
@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash ('Your post has beeen deleted', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts= Post.query.filter_by(author=user)\
            .order_by(Post.date_posted.desc())\
            .paginate(page=page, per_page=3)
    return render_template( 'user_posts.html', posts =posts, user=user)



def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token',token=token, _external=True)}

If you did not make this request then simply ignore this email.
'''

@app.route('/reset_password',methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html',title='Reset Password', form=form)


@app.route('/reset_password/<token>',methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user= User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your has been updated! You are now able to login!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html',title='Reset Password', form=form)
