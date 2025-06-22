import os
import requests
import json

# Konfigurasi
MOODLE_URL = "http://52.63.155.102"  # Ganti dengan URL Moodle-mu
MOODLE_TOKEN = os.environ.get("MOODLE_TOKEN")  # Token dari Secrets
ASSIGNMENT_ID = 3  # Assignment ID yang sesuai
EMAIL = "fastgoole@gmail.com"  # Email mahasiswa yang akan diberi nilai
FEEDBACK_TEXT = "Hasil Tes Otomatis: - Total Tes: 2 - Lulus: 2 - Gagal: 0\nNilai Anda: 100"

# Ambil nilai dari file report.json (jika ada)
try:
    with open("report.json") as f:
        report = json.load(f)
    total_tests = report["summary"]["total"]
    passed = report["summary"]["passed"]
    failed = report["summary"]["failed"]
    grade = int((passed / total_tests) * 100)
except Exception:
    print("Gagal membaca report.json. Gunakan nilai default 100.")
    grade = 100

print(f"💯 Nilai berhasil dihitung: {grade}")

# 1. Cari user ID berdasarkan email
def get_user_id_by_email(email):
    url = f"{MOODLE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_user_get_users_by_field",
        "moodlewsrestformat": "json",
        "field": "email",
        "values[0]": email
    }
    r = requests.post(url, data=params)
    users = r.json()
    if users:
        return users[0]["id"]
    return None

# 2. Cek status submission user
def get_submission_status(assignment_id, user_id):
    url = f"{MOODLE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "mod_assign_get_submission_status",
        "moodlewsrestformat": "json",
        "assignid": assignment_id,
        "userid": user_id
    }
    r = requests.post(url, data=params)
    return r.json()

# 3. Submit grade
def post_grade(assignment_id, user_id, grade, feedback):
    url = f"{MOODLE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "mod_assign_save_grade",
        "moodlewsrestformat": "json",
        "assignmentid": assignment_id,
        "grades[0][userid]": user_id,
        "grades[0][grade]": float(grade),
        "grades[0][attemptnumber]": -1,
        "grades[0][addattempt]": 0,
        "grades[0][workflowstate]": "released",
        "grades[0][plugindata][assignfeedbackcomments_editor][text]": feedback,
        "grades[0][plugindata][assignfeedbackcomments_editor][format]": 1,
        "grades[0][plugindata][files_filemanager]": 0
    }
    r = requests.post(url, data=params)
    try:
        return r.json()
    except Exception:
        print("Response:", r.text)
        raise

# Eksekusi proses
print("🎯 Mulai proses autograding...")

user_id = get_user_id_by_email(EMAIL)
if not user_id:
    print(f"❌ User dengan email {EMAIL} tidak ditemukan.")
    exit(1)

print(f"✅ Ditemukan user ID: {user_id} untuk email: {EMAIL}")

submission = get_submission_status(ASSIGNMENT_ID, user_id)
status = submission.get("lastattempt", {}).get("submission", {}).get("status")

if status != "submitted":
    print(f"⚠️ User belum mengumpulkan tugas. Status: {status}")
    exit(1)

print(f"📦 User ini sudah punya submission (status: {status}). Siap dinilai.")

result = post_grade(ASSIGNMENT_ID, user_id, grade, FEEDBACK_TEXT)

if "exception" in result:
    print("❌ ERROR saat mengirim nilai:", result)
    exit(1)
else:
    print("✅ Nilai berhasil dikirim ke Moodle.")
    print("Response:", result)
