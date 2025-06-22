import os
import requests
import json

# ==============================================================================
# KONFIGURASI - EDIT BAGIAN INI
# ==============================================================================
MOODLE_URL = "http://52.63.155.102"
COURSE_ID = 2
# PENTING: Gunakan ID dari TUGAS BARU untuk pengetesan pertama kali.
ASSIGNMENT_ID = 3 # Ganti dengan ID TUGAS BARU Anda

GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "dhanidnawans12": "dhanidnawans12@gmail.com",
    # Tambahkan mahasiswa lainnya di sini
}

# ==============================================================================
# LOGIKA SKRIP - Menggunakan Metode Gradebook
# ==============================================================================

# --- Langkah 1 & 2: Ambil variabel dan hitung nilai (Sama seperti sebelumnya) ---

MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')

if not MOODLE_TOKEN or not GITHUB_USERNAME:
    print("❌ MOODLE_TOKEN atau GITHUB_USERNAME belum diset di environment.")
    exit(1)

grade = 0
feedback = "Feedback belum tersedia."
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
    feedback = "Peringatan: Laporan tes tidak ditemukan."

# --- Langkah 3: Cari User ID Moodle (Sama seperti sebelumnya) ---
email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)
if not email:
    print(f"❌ Username {GITHUB_USERNAME} tidak ditemukan di GITHUB_TO_EMAIL_MAP.")
    exit(1)

print(f"Mencari user ID untuk email: {email}")
search_params = { 'wstoken': MOODLE_TOKEN, 'wsfunction': 'core_user_get_users', 'moodlewsrestformat': 'json', 'criteria[0][key]': 'email', 'criteria[0][value]': email }
user_id = None
try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=search_params)
    response.raise_for_status()
    users = response.json().get('users', [])
    if not users:
        print(f"❌ Tidak menemukan user Moodle dengan email {email}"); exit(1)
    user_id = users[0]['id']
    print(f"✅ Ditemukan user ID: {user_id} untuk email: {email}")
except Exception as e:
    print(f"❌ Error saat mencari user: {e}"); exit(1)

# --- Langkah 4 (BARU): Temukan Grade Item ID di Gradebook ---
print(f"Mencari ID item nilai di gradebook untuk tugas ID {ASSIGNMENT_ID}...")
grade_item_id = None
try:
    params = { 'wstoken': MOODLE_TOKEN, 'wsfunction': 'gradereport_user_get_grade_items', 'moodlewsrestformat': 'json', 'courseid': COURSE_ID }
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=params)
    response.raise_for_status()
    data = response.json()
    if 'exception' in data:
        print(f"❌ Error dari Moodle saat mencari grade item: {data}"); exit(1)
    
    # Loop untuk menemukan item yang cocok dengan assignment kita
    for item in data['usergrades'][0]['gradeitems']:
        if item.get('itemmodule') == 'assign' and str(item.get('iteminstance')) == str(ASSIGNMENT_ID):
            grade_item_id = item['id']
            print(f"✅ Ditemukan Grade Item ID: {grade_item_id} untuk tugas '{item['itemname']}'")
            break
            
    if not grade_item_id:
        print(f"❌ Tidak menemukan item nilai yang cocok untuk Assignment ID {ASSIGNMENT_ID} di dalam gradebook."); exit(1)

except Exception as e:
    print(f"❌ Error Kritis saat mencari grade item: {e}")
    if 'response' in locals(): print("Response dari server:", response.text)
    exit(1)

# --- Langkah 5 (BARU): Kirim Nilai Langsung ke Gradebook ---
if grade_item_id:
    print(f"Mengirimkan nilai {grade:.2f} langsung ke Gradebook untuk item ID {grade_item_id}...")
    params = {
        'wstoken': MOODLE_TOKEN,
        'wsfunction': 'core_grades_update_grades',
        'moodlewsrestformat': 'json',
        'source': 'GitHub_Autograder_V2',
        'courseid': COURSE_ID,
        'component': 'mod_assign',
        'activityid': ASSIGNMENT_ID,
        'grades[0][studentid]': user_id,
        'grades[0][grade]': grade,
        'grades[0][str_feedback]': feedback
    }
    try:
        response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", params=params)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get('status') is False:
             if 'exception' in data: print(f"❌ Error dari Moodle API saat update gradebook: {data}"); exit(1)
        print("✅ SUKSES FINAL! Nilai berhasil dikirim langsung ke Gradebook Moodle.")
    except Exception as e:
        print(f"❌ Error Kritis saat mengirim nilai ke gradebook: {e}")
        if 'response' in locals(): print("Response dari server:", response.text)
        exit(1)
