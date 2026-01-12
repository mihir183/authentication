let loginMethod = "";

// ✅ Aadhaar selected by default on page load
document.addEventListener("DOMContentLoaded", () => {
    selectMethod("aadhaar");
});


function selectMethod(method) {
    loginMethod = method;

    ["aadhaarBox", "mobileBox", "emailBox"].forEach(id =>
        document.getElementById(id).classList.add("d-none")
    );

    document.getElementById(method + "Box").classList.remove("d-none");
}

function sendAadhaarOTP() {
    const aadhaarInput = document.getElementById("aadhaar").value.trim();

    if (!/^\d{12}$/.test(aadhaarInput)) {
        showMsg("❌ Aadhaar must be 12 digits", "danger");
        return;
    }

    fetch("https://6964c650e8ce952ce1f2f83e.mockapi.io/login")
        .then(res => res.json())
        .then(users => {
            console.log("Fetched users:", users);

            // ✅ Normalize both sides (IMPORTANT)
            const user = users.find(u =>
                String(u.aadhaar).trim() === String(aadhaarInput)
            );

            if (!user) {
                showMsg("❌ Aadhaar not registered", "danger");
                return;
            }

            const phone = String(user.phone || "").trim();

            if (!phone) {
                showMsg("❌ No mobile linked with Aadhaar", "danger");
                return;
            }

            console.log("Matched user:", user);

            // ✅ Send OTP to backend
            fetch("/auth/send-mobile-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    phone: phone,
                    name: user.name,
                    email: user.email,
                    aadhaar: user.aadhaar
                })
            })
                .then(res => res.json())
                .then(() => {
                    showMsg(
                        `✅ OTP sent to registered mobile ending ${phone.slice(-4)}`,
                        "success"
                    );
                    showOtp();
                })
                .catch(() => {
                    showMsg("❌ Failed to send OTP", "danger");
                });
        })
        .catch(err => {
            console.error(err);
            showMsg("❌ Unable to fetch Aadhaar records", "danger");
        });
}



function sendMobileOTP() {
    const phone = document.getElementById("mobile").value.trim();

    fetch("/auth/login/mobile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone })
    })
        .then(r => r.json())
        .then(d => {
            showMsg(d.message, d.success ? "success" : "danger");
            if (d.success) showOtp();
        });
}

function sendEmailOTP() {
    const email = document.getElementById("email").value.trim();

    fetch("/auth/login/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
    })
        .then(r => r.json())
        .then(d => {
            showMsg(d.message, d.success ? "success" : "danger");
            if (d.success) showOtp();
        });
}

function verifyOTP() {
    fetch("/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ otp: otp.value })
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

function showOtp() {
    document.getElementById("otpBox").classList.remove("d-none");
}

function showMsg(m, t) {
    const el = document.getElementById("msg");
    el.innerText = m;
    el.className = "text-" + t;
}
