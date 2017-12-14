import time
from flask import render_template, json, Response, request, redirect
from flask_login import login_required, login_user, logout_user

from app import app, login_manager, device_data_stack
from forms import SignupForm
from models.user import User


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
                return redirect('/protected')
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
                    return redirect('/protected')
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


@app.route("/stream")
def stream():
    def eventStream():
        while True:
            device_data_stack.append(next(app.hub_data_listener))
            connected_device_list = app.hub.getConnectedDeviceList()
            scanned_device_list = {}
            time.sleep(1)
            while len(device_data_stack) > 0:
                scanned_device_list = device_data_stack.pop()
            data_dict = {'scanned': scanned_device_list, 'connected': connected_device_list}
            app.data = json.dumps(data_dict)
            yield "data: " + app.data + "\n\n"

    return Response(eventStream(), mimetype="text/event-stream")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@login_manager.user_loader
def load_user(email):
    return User.objects(email=email).first()


@app.route("/connect_device", methods=['GET', 'POST'])
def connect_device():
    mac = request.form['scanned']
    result = app.hub.connectDevice(mac)
    return json.dumps({'success': result}), 200, {'ContentType': 'application/json'}


@app.route("/disconnect_device", methods=['GET', 'POST'])
def disconnect_device():
    mac = request.form['connected']
    result = app.hub.disconnectDevice(mac)
    return json.dumps({'success': result}), 200, {'ContentType': 'application/json'}
