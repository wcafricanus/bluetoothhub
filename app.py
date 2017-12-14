import time
from flask import Flask, request, render_template, redirect, url_for, Response, json
from flask_login import LoginManager, login_user, login_required, logout_user
from forms import SignupForm
from hub.HubConnection import HubConnection
from models.user import User

app = Flask(__name__)
app.secret_key = 'secretkeyhereplease'

login_manager = LoginManager()
login_manager.init_app(app)

device_data_stack = list()


@app.route('/')
def index():
    return "Welcome to Flask"


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('signup.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            if User.objects(email=form.email.data).first():
                return "Email address already exists"
            else:
                new_user = User(form.email.data, form.password.data)
                new_user.save()
                login_user(new_user)
                return "User created!"
        else:
            return "Form didn't validate"


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('login.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            user = User.objects(email=form.email.data).first()
            if user:
                if user.password == form.password.data:
                    login_user(user)
                    return "User logged in"
                else:
                    return "Wrong password"
            else:
                return "user doesn't exist"
    else:
        return "form not validated"


@app.route('/protected')
@login_required
def protected():
    return render_template("deviceview.html")


app.hub = HubConnection()
app.hub_data_listener = app.hub.data_listener()
app.data = "{}"


@app.route("/stream")
def stream():
    def eventStream():
        while True:
            device_data_stack.append(next(app.hub_data_listener))
            time.sleep(1)
            while len(device_data_stack) > 0:
                app.data = json.dumps(device_data_stack.pop())
            yield "data: " + app.data + "\n\n"

    return Response(eventStream(), mimetype="text/event-stream")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return "Logged out"


@login_manager.user_loader
def load_user(email):
    return User.objects(email=email).first()


if __name__ == '__main__':
    app.run(port=5000, host='localhost')
