import os
import requests
import json

# ----------------------------------------
# KONFIGURASI - EDIT SESUAI MOODLE ANDA
# ----------------------------------------
MOODLE_URL = "http://52.63.155.102"
COURSE_ID = "2"
ASSIGNMENT_ID = "2"

GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "dhaniadi": "dhaniadi@gmail.com",
    # Tambah mahasiswa lain jika perlu
}

# ----------------------------------------
# AMBIL ENVIRONMENT VARIABLES
# ----------------------------------------
MOODLE_TOKEN = os.environ.get("MOODLE_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")

if not MOODLE_TOKEN or not GITHUB_USERNAME:
    print("❌ ERROR: MOODLE_TOKEN atau GITHUB_USERNAME tidak tersedia di environment.")
    exit(1)

# ----------------------------------------
# HITUNG NILAI DARI report.json
# ----------------------------------------
grade = 0
feedback = "Feedback tidak tersedia."

try:
    with open("report.json") as f:
        report = json.load(f)
        total = report["summary"]["total"]
        passed = report["summary"]["passed"]
        failed = total - passed

        if total > 0:
            grade = round((passed / total) * 100)
        feedback = f"Hasil Tes Otomatis:\n- Total Tes: {total}\n- Lulus: {passed}\n- Gagal: {failed}\n\nNilai Anda: {grade}"
        print(f"✅ Nilai berhasil dihitung: {grade}")
except FileNotFoundError:
    feedback = "❌ File report.json tidak ditemukan."
except Exception as e:
    feedback = f"❌ Gagal memproses report.json: {str(e)}"

# ----------------------------------------
# CARI USER MOODLE BERDASARKAN EMAIL
# ----------------------------------------
email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)

if not email:
    print(f"❌ ERROR: Username '{GITHUB_USERNAME}' tidak ditemukan di GITHUB_TO_EMAIL_MAP.")
    exit(1)

search_params = {
    "wstoken": MOODLE_TOKEN,
    "wsfunction": "core_user_get_users",
    "moodlewsrestformat": "json",
    "criteria[0][key]": "email",
    "criteria[0][value]": email,
}

try:
    res = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
    users = res.json().get("users", [])
    if not users:
        print(f"❌ Tidak ada user dengan email {email}")
        exit(1)
    user_id = users[0]["id"]
    print(f"✅ Ditemukan user ID: {user_id} untuk email: {email}")
except Exception as e:
    print(f"❌ ERROR saat mencari user: {e}")
    exit(1)

# ----------------------------------------
# CEK APAKAH USER SUDAH SUBMIT
# ----------------------------------------
submission_check_params = {
    "wstoken": MOODLE_TOKEN,
    "wsfunction": "mod_assign_get_submissions",
    "moodlewsrestformat": "json",
    "assignmentids[0]": ASSIGNMENT_ID,
}

try:
    res = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=submission_check_params)
    submissions = res.json().get("assignments", [])[0]["submissions"]

    user_submission = next((s for s in submissions if s["userid"] == user_id), None)

    if not user_submission or user_submission["status"] != "submitted":
        print("❌ User belum melakukan submission (status != submitted).")
        exit(1)

    print(f"✅ User ini sudah punya submission (status: submitted). Siap dinilai.")
except Exception as e:
    print(f"❌ ERROR saat cek submission: {e}")
    exit(1)

# ----------------------------------------
# KIRIM NILAI KE MOODLE
# ----------------------------------------
grade_params = {
    "wstoken": MOODLE_TOKEN,
    "wsfunction": "mod_assign_save_grade",
    "moodlewsrestformat": "json",
    "grades[0][userid]": user_id,
    "grades[0][grade]": int(grade),
    "grades[0][plugindata][assignfeedbackcomments_editor][text]": feedback,
    "grades[0][plugindata][assignfeedbackcomments_editor][format]": 1,
    "assignmentid": ASSIGNMENT_ID
}

try:
    res = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", data=grade_params)
    res_data = res.json()

    if "exception" in res_data:
        print(f"❌ Error dari Moodle API: {res_data}")
        exit(1)

    print("✅ Nilai dan feedback berhasil dikirim ke Moodle!")
except Exception as e:
    print(f"❌ ERROR saat mengirim nilai: {e}")
    exit(1)
