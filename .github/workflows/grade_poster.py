import os
import requests
import json

# --- 1. Ambil Username GitHub ---
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', '')

# --- 2. Pemetaan Manual GitHub ke Email ---
# Tambahkan semua mahasiswa Anda di sini
GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "github_username_mahasiswa_lain": "email_moodle_mahasiswa_lain@example.com",
    # Tambahkan mahasiswa lainnya di baris baru
}

# Dapatkan email dari pemetaan
moodle_email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)

if not moodle_email:
    print(f"Error: Username GitHub '{GITHUB_USERNAME}' tidak ditemukan dalam pemetaan manual.")
    exit(1)

print(f"Mencari pengguna Moodle dengan email: {moodle_email}")

# --- 3. Dapatkan Moodle User ID dari Email ---
# Siapkan parameter untuk API Moodle
MOODLE_URL = "http://52.63.155.102" # Ganti jika perlu
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN') # Pastikan secret MOODLE_TOKEN masih ada

rest_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'core_user_get_users',
    'moodlewsrestformat': 'json',
    'criteria[0][key]': 'email', # KITA MENCARI BERDASARKAN EMAIL
    'criteria[0][value]': moodle_email
}

try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=rest_params)
    response.raise_for_status()
    users = response.json().get('users', [])
    if not users:
        print(f"Error: User Moodle dengan email '{moodle_email}' tidak ditemukan.")
        exit(1)
    moodle_user_id = users[0]['id']
    print(f"Berhasil menemukan Moodle User ID: {moodle_user_id}")
except Exception as e:
    print(f"Error saat mencari user Moodle: {e}")
    if 'response' in locals():
        print("Response dari server:", response.text)
    exit(1)

# --- Sisanya sama (logika penilaian dan pengiriman nilai) ---
# ... (kode untuk membaca report.json dan mengirim nilai tetap sama) ...
# Pastikan Anda masih memiliki logika untuk mengirimkan nilai (mod_assign_save_grade)
# Jika Anda butuh kode lengkapnya lagi, beri tahu saya.

# --- 4. Kirim Nilai ke Moodle ---
rest_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'mod_assign_save_grade',
    'moodlewsrestformat': 'json',
    'assignmentid': ASSIGNMENT_ID,
    'userid': moodle_user_id,
    'grade[grade]': grade,
    'addattempt': 1,
    'workflowstate': 'graded',
    'applytoall': 1,
    'plugindata[assignfeedbackcomments_editor][text]': feedback,
    'plugindata[assignfeedbackcomments_editor][format]': 1 # 1 for HTML
}

try:
    response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", params=rest_params)
    response.raise_for_status()
    # Cek apakah ada error dari Moodle API
    if 'exception' in response.json():
        print(f"Error dari Moodle API saat menyimpan nilai: {response.json()}")
    else:
        print("Nilai berhasil dikirim ke Moodle.")
        
except Exception as e:
    print(f"Error saat mengirim nilai ke Moodle: {e}")
    print("Response:", response.text)
    exit(1)
