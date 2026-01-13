from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests, random, time, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from twilio.rest import Client

# ---------------------------
# Setup
# ---------------------------
load_dotenv()
app = Flask(__name__)
CORS(app)

MOCKAPI_BASE_URL = os.getenv("MOCKAPI_BASE_URL")
OTP_EXPIRY = 300

# Twilio
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

# Email
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

otp_store = {}

# ---------------------------
# Helpers
# ---------------------------
def generate_otp():
    return str(random.randint(100000, 999999))


def send_sms(phone, otp):
    twilio_client.messages.create(
        body=f"Your OTP is {otp}. Valid for 5 minutes.",
        from_=TWILIO_PHONE,
        to=phone
    )


def send_email(email, otp):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = email
    msg["Subject"] = "Your OTP"
    msg.attach(MIMEText(f"Your OTP is {otp}", "plain"))

    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


def save_otp(key, user):
    otp_store[key] = {
        "otp": generate_otp(),
        "expires": time.time() + OTP_EXPIRY,
        "user": user
    }
    return otp_store[key]["otp"]

# ---------------------------
# Pages
# ---------------------------
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
    data = request.json
    phone = data.get("phone")

    if not phone:
        return jsonify({
            "success": False,
            "message": "Mobile number is required"
        }), 400

    url = f"{MOCKAPI_BASE_URL}/login"
    users = requests.get(url).json()

    # ❌ If already registered → error
    if any(u.get("phone") == phone for u in users):
        return jsonify({
            "success": False,
            "message": "Mobile number already registered"
        }), 409

    # ✅ Create TEMP user (NOT saved)
    temp_user = {
        "name": data.get("name"),
        "email": data.get("email"),
        "phone": phone,
        "aadhaar": data.get("aadhaar")
    }

    # Generate & store OTP with temp user
    otp = save_otp(phone, temp_user)
    send_sms(phone, otp)

    return jsonify({
        "success": True,
        "message": "OTP sent to mobile"
    })

# ---------------------------
# Login Routes
# ---------------------------
@app.route("/auth/login/aadhaar", methods=["POST"])
def login_aadhaar():
    aadhaar = request.json.get("aadhaar")

    users = requests.get(f"{MOCKAPI_BASE_URL}/login").json()
    user = next((u for u in users if u.get("aadhaar") == aadhaar), None)

    if not user:
        return jsonify({"success": False, "message": "Aadhaar not registered"})

    otp = save_otp(user["phone"], user)
    send_sms(user["phone"], otp)

    return jsonify({"success": True, "message": "OTP sent to registered mobile"})

#login send mobile otp
@app.route("/auth/login/mobile", methods=["POST"])
def login_mobile():
    phone = request.json.get("phone")

    users = requests.get(f"{MOCKAPI_BASE_URL}/login").json()
    user = next((u for u in users if u.get("phone") == phone), None)

    if not user:
        return jsonify({"success": False, "message": "Mobile not registered"})

    otp = save_otp(phone, user)
    send_sms(phone, otp)

    return jsonify({"success": True, "message": "OTP sent to mobile"})

@app.route("/auth/send-email-otp", methods=["POST"])
def send_email_otp():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    url = f"{MOCKAPI_BASE_URL}/login"
    users = requests.get(url).json()

    # ❌ If already registered → error
    if any(u.get("email") == email for u in users):
        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    # ✅ TEMP user (NOT saved yet)
    temp_user = {
        "name": data.get("name"),
        "email": email,
        "phone": data.get("phone"),
        "aadhaar": data.get("aadhaar")
    }

    # Generate & store OTP with temp user
    otp = save_otp(email, temp_user)
    send_email(email, otp)

    return jsonify({
        "success": True,
        "message": "OTP sent to email"
    })


#login email sendOtp

@app.route("/auth/login/email", methods=["POST"])
def login_email():
    email = request.json.get("email")

    users = requests.get(f"{MOCKAPI_BASE_URL}/login").json()
    user = next((u for u in users if u.get("email") == email), None)

    if not user:
        return jsonify({"success": False, "message": "Email not registered"})

    otp = save_otp(email, user)
    send_email(email, otp)

    return jsonify({"success": True, "message": "OTP sent to email"})

# ---------------------------
# Verify OTP (ONLY ONE)
# ---------------------------
@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    otp = request.json.get("otp")

    if not otp:
        return jsonify({
            "success": False,
            "message": "OTP is required"
        }), 400

    for key, record in list(otp_store.items()):
        if record["otp"] == otp:

            # ❌ Expired
            if time.time() > record["expires"]:
                otp_store.pop(key)
                return jsonify({
                    "success": False,
                    "message": "OTP expired"
                })

            user = record["user"]

            # ✅ Save to MockAPI AFTER verification
            url = f"{MOCKAPI_BASE_URL}/login"
            users = requests.get(url).json()

            if not any(u.get("phone") == user["phone"] for u in users):
                user = requests.post(url, json=user).json()

            otp_store.pop(key)

            return jsonify({
                "success": True,
                "message": "OTP verified successfully",
                "user": user
            })

    return jsonify({
        "success": False,
        "message": "Invalid OTP"
    })

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
