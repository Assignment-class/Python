import os
import requests
import json

# ==============================================================================
# BAGIAN KONFIGURASI - MOHON ISI BAGIAN INI DENGAN DATA ANDA
# ==============================================================================

# 1. URL Moodle, ID Kursus, dan ID Tugas
# TODO: Untuk keamanan terbaik, sebaiknya pindahkan semua variabel ini ke GitHub Secrets.
MOODLE_URL = "http://52.63.155.102"
COURSE_ID = "2"      # Ganti dengan ID Kursus (Course) Moodle Anda
ASSIGNMENT_ID = "2"  # Ganti dengan ID Tugas (Assignment) Moodle Anda

# 2. Pemetaan Manual dari Username GitHub ke Email yang Terdaftar di Moodle
#    Ini adalah "buku telepon" atau jembatan penghubung kita.
#    Format: "UsernameDiGitHub": "email_yang_terdaftar_di_moodle@example.com"
GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    # --- TAMBAHKAN SEMUA MAHASISWA ANDA DI SINI ---
    "github_user_3": "email_moodle_3@example.com",
}

# ==============================================================================
# BAGIAN LOGIKA SKRIP - Sebaiknya tidak perlu diubah
# ==============================================================================

# --- Langkah 1: Ambil Variabel dari GitHub Actions Environment ---
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')

if not MOODLE_TOKEN or not GITHUB_USERNAME:
    print("Error: Variabel MOODLE_TOKEN atau GITHUB_USERNAME tidak ditemukan.")
    exit(1)

# --- Langkah 2: Hitung Nilai dari Hasil Tes ---
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
    
    feedback = f"Hasil Tes Otomatis:\n- Total Tes: {total_tests}\n- Lulus: {passed_tests}\n- Gagal: {failed_tests}\n\nNilai Anda: {grade:.2f}"
    print(f"Berhasil menghitung nilai: {grade}")

except FileNotFoundError:
    grade = 0
    feedback = "Gagal menjalankan tes. File `report.json` tidak ditemukan. Pastikan tes Anda berjalan dengan benar."
    print("Warning: File report.json tidak ditemukan, nilai diatur ke 0.")
except Exception as e:
    grade = 0
    feedback = f"Terjadi error saat memproses hasil tes: {e}"
    print(f"Error saat memproses report.json: {e}")

# --- Langkah 3: Cari User Moodle Berdasarkan Email ---
moodle_email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)

if not moodle_email:
    print(f"Error: Username GitHub '{GITHUB_USERNAME}' tidak ditemukan dalam pemetaan manual GITHUB_TO_EMAIL_MAP.")
    exit(1)

print(f"Mencari pengguna Moodle dengan email: {moodle_email}")

search_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'core_user_get_users',
    'moodlewsrestformat': 'json',
    'criteria[0][key]': 'email',
    'criteria[0][value]': moodle_email
}

moodle_user_id = None
try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
    response.raise_for_status()
    users = response.json().get('users', [])
    if not users:
        print(f"Error: Tidak ada pengguna Moodle yang ditemukan dengan email '{moodle_email}'.")
        exit(1)
    moodle_user_id = users[0]['id']
    print(f"Berhasil menemukan Moodle User ID: {moodle_user_id}")
except Exception as e:
    print(f"Error Kritis saat mencari user Moodle: {e}")
    if 'response' in locals():
        print("Response mentah dari server:", response.text)
    exit(1)

# --- Langkah 4: Kirim Nilai dan Feedback ke Moodle ---
if moodle_user_id:
    print(f"Mengirimkan nilai {grade:.2f} untuk user ID {moodle_user_id} ke tugas ID {ASSIGNMENT_ID}...")
    
  grade_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'mod_assign_save_grade',
    'moodlewsrestformat': 'json',
    'assignmentid': ASSIGNMENT_ID,
    'grades[0][userid]': moodle_user_id,
    'grades[0][grade]': grade,
    'grades[0][plugindata][assignfeedbackcomments_editor][text]': feedback,
    'grades[0][plugindata][assignfeedbackcomments_editor][format]': 1
    }

    try:
        response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", params=grade_params)
        response.raise_for_status()
        
        if 'exception' in response.json():
            print(f"Error dari Moodle API saat menyimpan nilai: {response.json()}")
            exit(1)
        else:
            print("Nilai dan feedback berhasil dikirim ke Moodle!")

    except Exception as e:
        print(f"Error Kritis saat mengirim nilai ke Moodle: {e}")
        if 'response' in locals():
            print("Response mentah dari server:", response.text)
        exit(1)
