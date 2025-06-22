import os
import requests
import json

# ==============================================================================
# KONFIGURASI: URL Moodle dan Mapping Username GitHub -> Email Moodle
# ==============================================================================

MOODLE_URL = "http://52.63.155.102"
COURSE_ID = "2"
ASSIGNMENT_ID = "2"

GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "github_user_3": "email_moodle_3@example.com",
}

# ==============================================================================
# LOGIKA
# ==============================================================================

MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')

if not MOODLE_TOKEN or not GITHUB_USERNAME:
    print("❌ ERROR: MOODLE_TOKEN atau GITHUB_USERNAME tidak ditemukan di environment.")
    exit(1)

# Langkah 1: Hitung Nilai
grade = 0
feedback = "Feedback belum tersedia."

try:
    with open('report.json') as f:
        report = json.load(f)

    total_tests = report['summary'].get('total', 0)
    passed_tests = report['summary'].get('passed', 0)
    failed_tests = total_tests - passed_tests

    if total_tests > 0:
        grade = int((passed_tests / total_tests) * 100)

    feedback = f"Hasil Tes Otomatis:\n- Total Tes: {total_tests}\n- Lulus: {passed_tests}\n- Gagal: {failed_tests}\n\nNilai Anda: {grade}"
    print(f"✅ Nilai berhasil dihitung: {grade}")

except FileNotFoundError:
    feedback = "❌ Gagal: File report.json tidak ditemukan."
    print(feedback)
    exit(1)

# Langkah 2: Dapatkan Email Moodle
moodle_email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)
if not moodle_email:
    print(f"❌ ERROR: Username GitHub '{GITHUB_USERNAME}' tidak ditemukan di GITHUB_TO_EMAIL_MAP.")
    exit(1)

# Langkah 3: Cari User ID Moodle dari Email
search_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'core_user_get_users',
    'moodlewsrestformat': 'json',
    'criteria[0][key]': 'email',
    'criteria[0][value]': moodle_email
}

try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
    response.raise_for_status()
    users = response.json().get('users', [])
    if not users:
        print(f"❌ ERROR: Tidak ada user dengan email {moodle_email}.")
        exit(1)
    moodle_user_id = users[0]['id']
    print(f"✅ Ditemukan user ID: {moodle_user_id} untuk email: {moodle_email}")
except Exception as e:
    print(f"❌ ERROR saat mencari user: {e}")
    exit(1)

# Langkah 4: Cek apakah user sudah mengumpulkan tugas
check_submission_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'mod_assign_get_submission_status',
    'moodlewsrestformat': 'json',
    'assignid': ASSIGNMENT_ID,
    'userid': moodle_user_id,
}

resp = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=check_submission_params)
status_json = resp.json()
if 'exception' in status_json:
    print("❌ ERROR saat cek submission:", status_json)
    exit(1)

submission_status = status_json.get("lastattempt", {}).get("submission", {}).get("status")
if submission_status != "submitted":
    print(f"⚠️ User ini belum mengumpulkan tugas. Status: {submission_status}")
    exit(1)
else:
    print(f"✅ User ini sudah punya submission (status: {submission_status}). Siap dinilai.")

# Langkah 5: Kirim Nilai ke Moodle
grade_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'mod_assign_save_grades',
    'moodlewsrestformat': 'json',
    'assignmentid': ASSIGNMENT_ID,
    'applytoall': 0,
    'grades[0][userid]': moodle_user_id,
    'grades[0][grade]': grade,
    'grades[0][attemptnumber]': -1,
    'grades[0][addattempt]': 1,
    'grades[0][workflowstate]': 'released',
    'grades[0][plugindata][assignfeedbackcomments_editor][text]': feedback,
    'grades[0][plugindata][assignfeedbackcomments_editor][format]': 1,
    'grades[0][plugindata][files_filemanager]': 0
}

try:
    response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", data=grade_params)
    response.raise_for_status()
    result = response.json()
    if 'exception' in result:
        print(f"❌ Error dari Moodle API: {result}")
        exit(1)
    else:
        print("✅ Nilai dan feedback berhasil dikirim ke Moodle.")
except Exception as e:
    print(f"❌ ERROR saat mengirim nilai: {e}")
    if 'response' in locals():
        print("Response:", response.text)
    exit(1)
