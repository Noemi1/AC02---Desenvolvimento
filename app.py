import os
import pathlib
from google import auth

import requests
from flask import Flask, session, abort, redirect, request, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

import smtplib 
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "CodeSpecialist.com"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "255715985919-6rjumhu5881vldgqdkjh7i558o7h3cso.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    sendEmail(session['name'],session['email'], 'login')
    return redirect("/profile")


@app.route("/logout")
def logout():
    sendEmail(session['name'],session['email'], 'logout')
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    authenticate =  session['name'] if 'google_id' in session else False
    return render_template('index.html', auth=authenticate)


@app.route("/profile")
@login_is_required
def protected_area():
    name = session['name']
    authenticate =  session['name'] if 'google_id' in session else False
    return render_template('profile.html', name=name, auth=authenticate)

def sendEmail(nome, email, acao):
    host = 'smtp.gmail.com'
    port = '587'
    login = 'madarah.impacta@gmail.com'
    senha = 'ABCdef123-+.'

    server = smtplib.SMTP(host, port)
    server.ehlo()
    server.starttls()
    server.login(login, senha)

    body = f'Você fez {acao} com {nome} - {email}'
    subject = 'AC02 - Madarah SPTM'

    email_msg = MIMEMultipart()
    email_msg['From'] = login
    email_msg['To'] = email
    email_msg['Subject'] = subject
    email_msg.attach(MIMEText(body, 'Plain'))


    server.sendmail(
        email_msg['From'],
        email_msg['To'],
        email_msg.as_string()
    )
    server.quit()


if __name__ == "__main__":
    app.run(debug=True)
