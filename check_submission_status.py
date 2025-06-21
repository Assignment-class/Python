import os
import requests

# KONFIGURASI
MOODLE_URL = "http://52.63.155.102"
ASSIGNMENT_ID = 2

GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "dhanidnawans12": "dhanidnawans12@gmail.com",
    # Tambahkan lainnya jika perlu
}

# Ambil token & username GitHub dari environment
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')

if not MOODLE_TOKEN or not GITHUB_USERNAME:
    print("❌ MOODLE_TOKEN atau GITHUB_USERNAME belum diset di environment.")
    exit(1)

if GITHUB_USERNAME not in GITHUB_TO_EMAIL_MAP:
    print(f"❌ Username {GITHUB_USERNAME} tidak ditemukan di GITHUB_TO_EMAIL_MAP.")
    exit(1)

email = GITHUB_TO_EMAIL_MAP[GITHUB_USERNAME]

# Langkah 1: Ambil user ID dari email
search_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'core_user_get_users',
    'moodlewsrestformat': 'json',
    'criteria[0][key]': 'email',
    'criteria[0][value]': email
}

response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
users = response.json().get('users', [])
if not users:
    print(f"❌ Tidak menemukan user dengan email {email}")
    exit(1)

user_id = users[0]['id']
print(f"✅ Ditemukan user ID: {user_id} untuk email: {email}")

# Langkah 2: Cek status submission
status_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'mod_assign_get_submission_status',
    'moodlewsrestformat': 'json',
    'assignid': ASSIGNMENT_ID,
    'userid': user_id
}

response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", data=status_params)
data = response.json()

if 'exception' in data:
    print("❌ Error dari Moodle:", data)
    exit(1)

submission = data.get('lastattempt', {}).get('submission', {})
if submission and submission.get('status') in ['submitted', 'draft']:
    print(f"✅ User ini sudah punya submission (status: {submission.get('status')}). Siap dinilai.")
else:
    print(f"⚠️ User ini BELUM memiliki submission pada assignment ID {ASSIGNMENT_ID}.")
    print("📝 Minta mahasiswa login & submit dulu ke assignment.")
