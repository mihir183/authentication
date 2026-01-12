from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests, random, time, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()
app = Flask(__name__)
CORS(app)

MOCKAPI_BASE_URL = os.getenv("MOCKAPI_BASE_URL")
OTP_EXPIRY = 300

# Twilio
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

# Email
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/auth/send-mobile-otp", methods=["POST"])
def send_mobile_otp():
    d = request.json
    otp = generate_otp()
    otp_store[d["phone"]] = {"otp": otp, "expires": time.time()+OTP_EXPIRY, "user": d}

    twilio_client.messages.create(
        body=f"Your OTP is {otp}",
        from_=TWILIO_PHONE,
        to=d["phone"]
    )
    return jsonify({"message": "OTP sent to mobile"})

@app.route("/auth/send-email-otp", methods=["POST"])
def send_email_otp():
    d = request.json
    otp = generate_otp()
    otp_store[d["phone"]] = {"otp": otp, "expires": time.time()+OTP_EXPIRY, "user": d}

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = d["email"]
    msg["Subject"] = "Your OTP"
    msg.attach(MIMEText(f"Your OTP is {otp}", "plain"))

    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

    return jsonify({"message": "OTP sent to email"})

@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    d = request.json
    record = otp_store.get(d["phone"])
    if not record or time.time() > record["expires"] or d["otp"] != record["otp"]:
        return jsonify({"success": False, "message": "Invalid or expired OTP"})

    user = record["user"]
    url = f"{MOCKAPI_BASE_URL}/login"
    users = requests.get(url).json()
    if not any(u["phone"] == user["phone"] for u in users):
        user = requests.post(url, json=user).json()

    otp_store.pop(d["phone"])
    return jsonify({"success": True, "user": user})

if __name__ == "__main__":
    app.run(debug=True)


def send_otp_common(key, user):
    otp = generate_otp()
    otp_store[key] = {
        "otp": otp,
        "expires": time.time()+OTP_EXPIRY,
        "user": user
    }
    return otp

@app.route("/auth/login/aadhaar", methods=["POST"])
def login_aadhaar():
    aadhaar = request.json.get("aadhaar")

    users = requests.get(f"{MOCKAPI_BASE_URL}/login").json()
    user = next((u for u in users if u["aadhaar"] == aadhaar), None)

    if not user:
        return jsonify({"success":False,"message":"Aadhaar not registered"})

    otp = send_otp_common(user["phone"], user)
    send_otp_sms(user["phone"], otp)

    return jsonify({"success":True,"message":"OTP sent to registered mobile"})

@app.route("/auth/login/mobile", methods=["POST"])
def login_mobile():
    phone = request.json.get("phone")

    users = requests.get(f"{MOCKAPI_BASE_URL}/login").json()
    user = next((u for u in users if u["phone"] == phone), None)

    if not user:
        return jsonify({"success":False,"message":"Mobile not registered"})

    otp = send_otp_common(phone, user)
    send_otp_sms(phone, otp)

    return jsonify({"success":True,"message":"OTP sent to mobile"})

@app.route("/auth/login/email", methods=["POST"])
def login_email():
    email = request.json.get("email")

    users = requests.get(f"{MOCKAPI_BASE_URL}/login").json()
    user = next((u for u in users if u["email"] == email), None)

    if not user:
        return jsonify({"success":False,"message":"Email not registered"})

    otp = send_otp_common(email, user)
    send_email_otp(email, otp)

    return jsonify({"success":True,"message":"OTP sent to email"})

