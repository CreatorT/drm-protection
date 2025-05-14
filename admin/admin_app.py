from flask import Flask, render_template, request, redirect, url_for, flash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY='replace-with-a-random-secret',
    SQLALCHEMY_DATABASE_URI='sqlite:///admin.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---
class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(128))

class HWID(db.Model):
    hwid = db.Column(db.String(64), primary_key=True)
    added_at = db.Column(db.DateTime, server_default=db.func.now())

# --- Admin UI ---
admin = Admin(app, name='License Admin', template_mode='bootstrap4')
admin.add_view(ModelView(HWID, db.session))

# --- Auth Routes ---
@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u = AdminUser.query.filter_by(username=request.form['username']).first()
        if u and check_password_hash(u.password_hash, request.form['password']):
            login_user(u)
            return redirect('/admin')
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__=='__main__':
    db.create_all()
    # Create default admin if none
    if not AdminUser.query.first():
        u = AdminUser(username='admin', password_hash=generate_password_hash('change-me'))
        db.session.add(u); db.session.commit()
    app.run(host='0.0.0.0', port=8000)
