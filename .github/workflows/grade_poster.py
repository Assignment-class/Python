import os
import requests
import json

# ==============================================================================
# BAGIAN KONFIGURASI - MOHON ISI BAGIAN INI DENGAN DATA ANDA
# ==============================================================================

# 1. URL Moodle, ID Kursus, dan ID Tugas
MOODLE_URL = "http://52.63.155.102"
COURSE_ID = 2      # Sebaiknya gunakan angka, bukan string
ASSIGNMENT_ID = 5  # Sebaiknya gunakan angka, bukan string

# 2. Pemetaan Manual dari Username GitHub ke Email yang Terdaftar di Moodle
GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "dhanidds": "dhanidwinawans12@gmail.com",
    # --- TAMBAHKAN SEMUA MAHASISWA ANDA DI SINI ---
}

# ==============================================================================
# BAGIAN LOGIKA SKRIP - Sebaiknya tidak perlu diubah
# ==============================================================================

# --- Langkah 1: Ambil Variabel dari GitHub Actions Environment ---
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')

if not MOODLE_TOKEN or not GITHUB_USERNAME:
    print("❌ Error: Variabel MOODLE_TOKEN atau GITHUB_USERNAME tidak ditemukan.")
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
    print(f"✅ Berhasil menghitung nilai: {grade}")

except FileNotFoundError:
    grade = 0
    feedback = "Gagal menjalankan tes. File `report.json` tidak ditemukan. Pastikan tes Anda berjalan dengan benar."
    print("⚠️ Warning: File report.json tidak ditemukan, nilai diatur ke 0.")
except Exception as e:
    grade = 0
    feedback = f"Terjadi error saat memproses hasil tes: {e}"
    print(f"❌ Error saat memproses report.json: {e}")

# --- Langkah 3: Cari User Moodle Berdasarkan Email ---
moodle_email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)

if not moodle_email:
    print(f"❌ Error: Username GitHub '{GITHUB_USERNAME}' tidak ditemukan dalam pemetaan manual GITHUB_TO_EMAIL_MAP.")
    exit(1)

print(f"Mencari pengguna Moodle dengan email: {moodle_email}")

search_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'core_user_get_users',
    'moodlewsrestformat': 'json',
    'criteria[0][key]': 'email',
    'criteria[0][value]': moodle_email
}

user_id = None # <-- DIPERBAIKI: Nama variabel disamakan
try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
    response.raise_for_status()
    users = response.json().get('users', [])
    if not users:
        print(f"❌ Error: Tidak ada pengguna Moodle yang ditemukan dengan email '{moodle_email}'.")
        exit(1)
    user_id = users[0]['id'] # <-- DIPERBAIKI: Mengisi variabel user_id
    print(f"✅ Berhasil menemukan Moodle User ID: {user_id}")
except Exception as e:
    print(f"❌ Error Kritis saat mencari user Moodle: {e}")
    if 'response' in locals():
        print("Response mentah dari server:", response.text)
    exit(1)

# --- Langkah 4: Kirim Nilai dan Feedback ke Moodle ---
if user_id: # <-- DIPERBAIKI: Sekarang kondisi ini akan benar (true)
    print(f"Mengirimkan nilai {grade:.2f} (METODE BARU) untuk user {user_id} ke tugas {ASSIGNMENT_ID}...")
    
    grade_params = {
        'wstoken': MOODLE_TOKEN,
        'wsfunction': 'mod_assign_save_grade',
        'moodlewsrestformat': 'json',
        'assignmentid': ASSIGNMENT_ID,
        'userid': user_id, # <-- DIPERBAIKI: Menggunakan variabel user_id yang sudah terisi
        'grade': grade,
        'attemptnumber': -1,
        'addattempt': 0,
        'workflowstate': 'graded',
        'applytoall': 1,
        'plugindata[assignfeedbackcomments_editor][text]': feedback,
        'plugindata[assignfeedbackcomments_editor][format]': 1
    }

    try:
        response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", params=grade_params)
        response.raise_for_status()
        
        # Periksa jika ada 'exception' dalam respons JSON
        json_response = response.json()
        if isinstance(json_response, dict) and 'exception' in json_response:
            print(f"❌ Error dari Moodle API saat menyimpan nilai: {json_response}")
            exit(1)
        else:
            print("✅ SUKSES! Perintah berhasil dikirim ke Moodle. Silakan cek gradebook.")

    except Exception as e:
        print(f"❌ Error Kritis saat mengirim nilai: {e}")
        if 'response' in locals():
            print("Response mentah dari server:", response.text)
        exit(1)
