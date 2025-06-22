import os
import requests
import json

# ==============================================================================
# KONFIGURASI
# ==============================================================================
MOODLE_URL = "http://52.63.155.102"
COURSE_ID = "2"
ASSIGNMENT_ID = "3"

GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
}

# ==============================================================================
# AMBIL ENVIRONMENT VARIABEL
# ==============================================================================
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')

if not MOODLE_TOKEN or not GITHUB_USERNAME:
    print("❌ MOODLE_TOKEN atau GITHUB_USERNAME tidak ditemukan.")
    exit(1)

# ==============================================================================
# CARI EMAIL DAN USER ID MOODLE
# ==============================================================================
email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)
if not email:
    print(f"❌ Username GitHub '{GITHUB_USERNAME}' tidak ditemukan.")
    exit(1)

search_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'core_user_get_users',
    'moodlewsrestformat': 'json',
    'criteria[0][key]': 'email',
    'criteria[0][value]': email
}

try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
    response.raise_for_status()
    users = response.json().get('users', [])
    if not users:
        print(f"❌ Tidak ditemukan user dengan email {email}")
        exit(1)
    user_id = users[0]['id']
    print(f"✅ Ditemukan user ID: {user_id} untuk email: {email}")
except Exception as e:
    print(f"❌ Gagal mendapatkan user ID dari email. {e}")
    exit(1)

# ==============================================================================
# CEK STATUS SUBMISSION
# ==============================================================================

# ==============================================================================
# HITUNG NILAI
# ==============================================================================
grade = 0
feedback = "Belum ada hasil."

try:
    with open('report.json') as f:
        report = json.load(f)
    total = report['summary'].get('total', 0)
    passed = report['summary'].get('passed', 0)
    failed = total - passed
    grade = (passed / total) * 100 if total > 0 else 0
    feedback = f"Hasil Tes Otomatis:\n- Total Tes: {total}\n- Lulus: {passed}\n- Gagal: {failed}\n\nNilai Anda: {grade:.2f}"
    print(f"✅ Nilai berhasil dihitung: {grade}")
except:
    print("❌ Gagal membaca report.json. Nilai = 0.")

# ==============================================================================
# KIRIM NILAI KE MOODLE
# ==============================================================================
grade_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'mod_assign_save_grade',
    'moodlewsrestformat': 'json',
    'assignmentid': ASSIGNMENT_ID,
    'grades[0][userid]': user_id,
    'grades[0][grade]': grade,
    'grades[0][plugindata][assignfeedbackcomments_editor][text]': feedback,
    'grades[0][plugindata][assignfeedbackcomments_editor][format]': 1
}

response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", data=grade_params)
result = response.json()

if 'exception' in result:
    print(f"❌ Error dari Moodle API: {result}")
    exit(1)
else:
    print("✅ Nilai dan feedback berhasil dikirim ke Moodle.")
