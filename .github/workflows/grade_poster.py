import os
import requests
import json

# Konfigurasi
MOODLE_URL = "http://52.63.155.102"
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
ASSIGNMENT_ID = 3
EMAIL = "fastgoole@gmail.com"  # Email tetap yang digunakan

# Step 1: Ambil user ID dari email
def get_user_id_by_email(email):
    url = f"{MOODLE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_user_get_users",
        "moodlewsrestformat": "json",
        "criteria[0][key]": "email",
        "criteria[0][value]": email
    }
    resp = requests.get(url, params=params).json()
    users = resp.get("users")
    if users and len(users) > 0:
        return users[0]["id"]
    return None

# Step 2: Cek apakah user punya submission
def get_submission_status(assignment_id, user_id):
    url = f"{MOODLE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "mod_assign_get_submissions",
        "moodlewsrestformat": "json",
        "assignmentids[0]": assignment_id
    }
    resp = requests.get(url, params=params).json()
    for assignment in resp.get("assignments", []):
        for submission in assignment.get("submissions", []):
            if submission["userid"] == user_id:
                return submission["status"]
    return None

# Step 3: Hitung nilai dari report.json
def get_score_from_report():
    try:
        with open("report.json", "r") as f:
            report = json.load(f)
        passed = sum(1 for t in report["tests"] if t["outcome"] == "passed")
        failed = sum(1 for t in report["tests"] if t["outcome"] == "failed")
        total = passed + failed
        if total == 0:
            return 0, "Tidak ada tes ditemukan."
        score = round((passed / total) * 100)
        feedback = f"Hasil Tes Otomatis: - Total Tes: {total} - Lulus: {passed} - Gagal: {failed} - Nilai Anda: {score}"
        return score, feedback
    except Exception as e:
        return 0, f"Error membaca report.json: {str(e)}"

# Step 4: Kirim nilai ke Moodle
def post_grade(assignment_id, user_id, grade, feedback):
    url = f"{MOODLE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "mod_assign_save_grade",
        "moodlewsrestformat": "json",
        "assignmentid": assignment_id,
        "grades[0][userid]": user_id,
        "grades[0][grade]": grade,
        "grades[0][plugindata][assignfeedbackcomments_editor][text]": feedback,
        "grades[0][plugindata][assignfeedbackcomments_editor][format]": 1
    }
    resp = requests.post(url, data=params)
    try:
        return resp.json()
    except Exception:
        print("Response:", resp.text)
        raise

# Main process
if __name__ == "__main__":
    print("🎯 Mulai proses autograding...")

    grade, feedback = get_score_from_report()
    print(f"✅ Nilai berhasil dihitung: {grade}")

    user_id = get_user_id_by_email(EMAIL)
    if not user_id:
        print(f"❌ Tidak ditemukan user untuk email: {EMAIL}")
        exit(1)
    print(f"✅ Ditemukan user ID: {user_id} untuk email: {EMAIL}")

    status = get_submission_status(ASSIGNMENT_ID, user_id)
    if status != "submitted":
        print(f"⚠️ User ini belum mengumpulkan tugas. Status: {status}")
        exit(0)
    print(f"📦 User ini sudah punya submission (status: {status}). Siap dinilai.")

    try:
        result = post_grade(ASSIGNMENT_ID, user_id, grade, feedback)
        print("✅ Nilai berhasil dikirim ke Moodle.")
        print("Response:", result)
    except Exception as e:
        print("❌ ERROR saat mengirim nilai:", str(e))
        exit(1)
