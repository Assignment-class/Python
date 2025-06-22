import os
import requests
import json

# ==============================================================================
# BAGIAN KONFIGURASI - SILAKAN EDIT BAGIAN INI SESUAI KEBUTUHAN ANDA
# ==============================================================================

# 1. URL Moodle, ID Kursus, dan ID Tugas Anda
MOODLE_URL = "http://52.63.155.102"
COURSE_ID = 2
ASSIGNMENT_ID = 3 # Terakhir kali berhasil dengan ID 3

# 2. Pemetaan Manual Username GitHub ke Email Moodle
#    Lengkapi daftar ini dengan semua mahasiswa Anda.
#    Format: "UsernameDiGitHub": "email_yang_terdaftar_di_moodle@example.com"
GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    # --- TAMBAHKAN MAHASISWA LAIN DI SINI ---
    "github_user_lain": "email_lain@example.com",
}

# ==============================================================================
# BAGIAN LOGIKA SKRIP - Sebaiknya tidak perlu diubah lagi
# ==============================================================================

# --- Langkah 1: Ambil variabel dari environment GitHub Actions ---
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')

if not MOODLE_TOKEN:
    print("❌ Error: Secret MOODLE_TOKEN tidak ditemukan. Pastikan sudah diatur di Settings > Secrets and variables > Actions.")
    exit(1)
if not GITHUB_USERNAME:
    print("❌ Error: Variabel GITHUB_USERNAME tidak ditemukan.")
    exit(1)

# --- Langkah 2: Hitung nilai dari laporan tes ---
grade = 0
feedback = "Feedback belum tersedia."

try:
    with open('report.json') as f:
        report = json.load(f)
    
    total_tests = report['summary'].get('total', 0)
    passed_tests = report['summary'].get('passed', 0)
    failed_tests = total_tests - passed_tests
    
    if total_tests > 0:
        grade = (passed_tests / total_tests) * 100
    
    feedback = f"Hasil Tes Otomatis:\n- Total Tes: {total_tests}\n- Lulus: {passed_tests}\n- Gagal: {failed_tests}\n\nNilai Akhir: {grade:.2f}"
    print(f"✅ Berhasil menghitung nilai: {grade:.2f}")

except FileNotFoundError:
    grade = 0
    feedback = "Peringatan: Tidak ada tes yang dijalankan atau laporan tes (report.json) tidak ditemukan. Nilai diatur ke 0."
    print(f"⚠️ {feedback}")
except Exception as e:
    grade = 0
    feedback = f"Terjadi error saat memproses hasil tes: {e}"
    print(f"❌ Error saat memproses report.json: {e}")

# --- Langkah 3: Cari user di Moodle menggunakan email dari pemetaan manual ---
moodle_email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)

if not moodle_email:
    print(f"❌ Error: Username GitHub '{GITHUB_USERNAME}' tidak ditemukan dalam kamus GITHUB_TO_EMAIL_MAP.")
    exit(1)

print(f"Mencari pengguna Moodle dengan email: {moodle_email}")

search_params = { 'wstoken': MOODLE_TOKEN, 'wsfunction': 'core_user_get_users', 'moodlewsrestformat': 'json', 'criteria[0][key]': 'email', 'criteria[0][value]': moodle_email }
moodle_user_id = None
try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
    response.raise_for_status()
    users = response.json().get('users', [])
    if not users:
        print(f"❌ Error: Tidak ada pengguna Moodle yang ditemukan dengan email '{moodle_email}'.")
        exit(1)
    moodle_user_id = users[0]['id']
    print(f"✅ Ditemukan user ID: {moodle_user_id} untuk email: {moodle_email}")
except Exception as e:
    print(f"❌ Error Kritis saat mencari user Moodle: {e}")
    if 'response' in locals(): print("Response mentah dari server:", response.text)
    exit(1)

# --- Langkah 4: Kirim nilai dan feedback ke Moodle ---
if moodle_user_id:
    print(f"Mengirimkan nilai {grade:.2f} untuk user ID {moodle_user_id} ke tugas ID {ASSIGNMENT_ID}...")
    grade_params = { 'wstoken': MOODLE_TOKEN, 'wsfunction': 'mod_assign_save_grade', 'moodlewsrestformat': 'json', 'assignmentid': ASSIGNMENT_ID, 'userid': moodle_user_id, 'grade[grade]': grade, 'addattempt': 1, 'workflowstate': 'graded', 'applytoall': 1, 'plugindata[assignfeedbackcomments_editor][text]': feedback, 'plugindata[assignfeedbackcomments_editor][format]': 1 }
    try:
        response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", params=grade_params)
        response.raise_for_status()
        if 'exception' in response.json():
            print(f"❌ Error dari Moodle API saat menyimpan nilai: {response.json()}")
            exit(1)
        else:
            print("✅ SUKSES! Nilai dan feedback berhasil dikirim ke Moodle!")
    except Exception as e:
        print(f"❌ Error Kritis saat mengirim nilai ke Moodle: {e}")
        if 'response' in locals(): print("Response mentah dari server:", response.text)
        exit(1)
