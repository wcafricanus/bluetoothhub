import time
from flask import render_template, json, Response, request, redirect, flash
from flask_login import login_required, login_user, logout_user

from app import app, login_manager, device_data_stack
from forms import SignupForm, LoginForm
from models.user import User
from models.device import Device


@app.route('/')
@login_required
def index():
    flash('Welcome to Heart Monitor! you will be redirected shortly.')
    return redirect('/protected')


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return redirect('/login')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('signup.html', form=form, page_title='Sign Up')
    elif request.method == 'POST':
        if form.validate_on_submit():
            if User.objects(email=form.email.data).first():
                return "Email address already exists"
            else:
                new_user = User(form.email.data, form.password.data, form.display_name.data)
                new_user.save()
                login_user(new_user)
                return redirect('/protected')
        else:
            return render_template('signup.html', form=form, page_title='Sign Up')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
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
    return render_template("overview.html")


def append_owner(device_dict):
    for key in device_dict:
        device = Device.objects(mac=key).first()
        if device is not None:
            if device.owner is not None:
                device_dict[key].update({'owner':device.owner.display_name})


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
            append_owner(scanned_device_list)
            append_owner(connected_device_list)
            data_dict = {'scanned': scanned_device_list, 'connected': connected_device_list,
                         'heart_rate': app.heart_rate_dict}
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
    # add device into database if not added before
    if not Device.objects(mac=mac).first():
        device = Device(mac=mac, owner=User.objects().first())
        device.save()
    result = app.hub.connectDevice(mac)
    return json.dumps({'success': result}), 200, {'ContentType': 'application/json'}


@app.route("/disconnect_device", methods=['GET', 'POST'])
def disconnect_device():
    mac = request.form['connected']
    result = app.hub.disconnectDevice(mac)
    return json.dumps({'success': result}), 200, {'ContentType': 'application/json'}


@app.route("/start_measure_hr", methods=['GET', 'POST'])
def start_measure_hr():
    mac = request.form['connected']
    # register the heart_rate associated with this mac addr. to be listened
    app.heart_rate_dict[mac] = None

    result = app.hub.startMeasureHeartRate(mac)
    return json.dumps({'success': result}), 200, {'ContentType': 'application/json'}


@app.route("/stop_measure_hr", methods=['GET', 'POST'])
def stop_measure_hr():
    mac = request.form['connected']
    # unregister the heart_rate associated with this mac addr. to be listened
    if mac in app.heart_rate_dict:
        app.heart_rate_dict.pop(mac)
    result = app.hub.stopMeasureHeartRate(mac)
    return json.dumps({'success': result}), 200, {'ContentType': 'application/json'}