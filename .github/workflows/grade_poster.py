import os
import requests
import json

# ==============================================================================
# KONFIGURASI - EDIT BAGIAN INI
# ==============================================================================
MOODLE_URL = "http://52.63.155.102"
ASSIGNMENT_ID = 3 # Ganti dengan ID TUGAS BARU untuk pengetesan

GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "dhanidnawans12": "dhanidnawans12@gmail.com",
    # Tambahkan mahasiswa lainnya di sini
}

# ==============================================================================
# LOGIKA SKRIP - Jangan diubah kecuali Anda tahu apa yang dilakukan
# ==============================================================================

# Ambil token & username GitHub dari environment
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')

# Validasi awal
if not MOODLE_TOKEN or not GITHUB_USERNAME:
    print("❌ MOODLE_TOKEN atau GITHUB_USERNAME belum diset di environment.")
    exit(1)

email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)
if not email:
    print(f"❌ Username {GITHUB_USERNAME} tidak ditemukan di GITHUB_TO_EMAIL_MAP.")
    exit(1)

# Langkah 1: Ambil user ID dari email
print(f"Mencari user ID untuk email: {email}")
search_params = { 'wstoken': MOODLE_TOKEN, 'wsfunction': 'core_user_get_users', 'moodlewsrestformat': 'json', 'criteria[0][key]': 'email', 'criteria[0][value]': email }
try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
    response.raise_for_status()
    users = response.json().get('users', [])
    if not users:
        print(f"❌ Tidak menemukan user Moodle dengan email {email}")
        exit(1)
    user_id = users[0]['id']
    print(f"✅ Ditemukan user ID: {user_id} untuk email: {email}")
except Exception as e:
    print(f"❌ Error saat mencari user: {e}")
    if 'response' in locals(): print("Response dari server:", response.text)
    exit(1)


# Langkah 2: Hitung nilai dari report.json
grade = 0
feedback = "Gagal menjalankan tes atau tidak ada file tes."
try:
    with open('report.json') as f:
        report = json.load(f)
    total = report['summary'].get('total', 0)
    passed = report['summary'].get('passed', 0)
    if total > 0: grade = (passed / total) * 100
    feedback = f"Hasil tes otomatis: {passed}/{total} tes lulus."
    print(f"✅ Nilai berhasil dihitung: {grade:.2f}")
except FileNotFoundError:
    print("⚠️ report.json tidak ditemukan, nilai diatur ke 0.")
except Exception as e:
    print(f"❌ Error saat memproses nilai: {e}")


# Langkah 3: Kirim nilai ke Moodle
print(f"Mengirimkan nilai {grade:.2f} untuk user {user_id} ke tugas {ASSIGNMENT_ID}...")
grade_params = { 'wstoken': MOODLE_TOKEN, 'wsfunction': 'mod_assign_save_grade', 'moodlewsrestformat': 'json', 'assignmentid': ASSIGNMENT_ID, 'userid': user_id, 'grade[grade]': grade, 'addattempt': 0, 'workflowstate': 'graded', 'applytoall': 0, 'plugindata[assignfeedbackcomments_editor][text]': feedback, 'plugindata[assignfeedbackcomments_editor][format]': 1 }
try:
    response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", params=grade_params)
    response.raise_for_status()
    if 'exception' in response.json():
        print(f"❌ Error dari Moodle saat menyimpan nilai: {response.json()}")
        exit(1)
    print("✅ SUKSES FINAL! Nilai berhasil dikirim ke Moodle.")
except Exception as e:
    print(f"❌ Error kritis saat mengirim nilai: {e}")
    if 'response' in locals(): print("Response dari server:", response.text)
    exit(1)
