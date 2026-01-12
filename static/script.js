function toggleOtpMethod() {
    const method = document.getElementById("otpMethod").value;
    document.getElementById("sendMobileOtpBtn").classList.add("d-none");
    document.getElementById("sendEmailOtpBtn").classList.add("d-none");

    if (method === "mobile") {
        document.getElementById("sendMobileOtpBtn").classList.remove("d-none");
    }
    if (method === "email") {
        document.getElementById("sendEmailOtpBtn").classList.remove("d-none");
    }
}

function validateCommonFields() {
    let name = nameEl.value.trim();
    let email = emailEl.value.trim();
    let mobile = mobileEl.value.trim();
    let aadhaar = aadhaarEl.value.trim();

    // -------------------------
    // Name validation
    // -------------------------
    if (!name) {
        showMsg("❌ Name is required", "danger");
        return false;
    }

    // -------------------------
    // Email regex validation
    // -------------------------
    const emailRegex = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;
    // If you want ANY email, use:
    // const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(email)) {
        showMsg("❌ Please enter a valid Gmail address", "danger");
        return false;
    }

    // -------------------------
    // Mobile auto-format (+91)
    // -------------------------
    mobile = mobile.replace(/\s+/g, "");

    if (!mobile.startsWith("+")) {
        if (/^\d{10}$/.test(mobile)) {
            mobile = "+91" + mobile;
            mobileEl.value = mobile; // update input
        } else {
            showMsg("❌ Enter a valid 10-digit mobile number", "danger");
            return false;
        }
    }

    if (!/^\+91\d{10}$/.test(mobile)) {
        showMsg("❌ Mobile must be in format +911234567890", "danger");
        return false;
    }

    // -------------------------
    // Aadhaar validation
    // -------------------------
    if (!/^\d{12}$/.test(aadhaar)) {
        showMsg("❌ Aadhaar must be 12 digits", "danger");
        return false;
    }

    return true;
}


function sendMobileOTP() {
    if (!validateCommonFields()) return;

    fetch("/auth/send-mobile-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(getPayload())
    })
        .then(r => r.json())
        .then(d => {
            showMsg(d.message, "success");
            showOtpBox();
        });
}

function sendEmailOTP() {
    if (!validateCommonFields()) return;

    fetch("/auth/send-email-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(getPayload())
    })
        .then(r => r.json())
        .then(d => {
            showMsg(d.message, "success");
            showOtpBox();
        });
}

function verifyOTP() {
    fetch("/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            phone: mobileEl.value.trim(),
            otp: otpEl.value.trim()
        })
    })
        .then(r => r.json())
        .then(d => {
            if (d.success) {
                localStorage.setItem("user", JSON.stringify(d.user));
                window.location.href = "/home";
            } else {
                showMsg(d.message, "danger");
            }
        });
}

function getPayload() {
    return {
        name: nameEl.value.trim(),
        email: emailEl.value.trim(),
        phone: mobileEl.value.trim(),
        aadhaar: aadhaarEl.value.trim()
    };
}

function showOtpBox() {
    document.getElementById("otpBox").classList.remove("d-none");
}

function showMsg(msg, type) {
    const m = document.getElementById("msg");
    m.innerText = msg;
    m.className = "text-" + type;
}

const nameEl = document.getElementById("name");
const emailEl = document.getElementById("email");
const mobileEl = document.getElementById("mobile");
const aadhaarEl = document.getElementById("aadhaar");
const otpEl = document.getElementById("otp");
