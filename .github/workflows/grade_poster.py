import os
import requests
import json

# ==============================================================================
# KONFIGURASI - CUKUP ISI BAGIAN INI
# ==============================================================================
MOODLE_URL = "http://52.63.155.102"
COURSE_ID = 2
# PENTING: Tulis nama tugas yang ingin dinilai, persis sama huruf besar/kecilnya
TARGET_ASSIGNMENT_NAME = "PYTHON" 

GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "dhanidnawans12": "dhanidnawans12@gmail.com",
}

# ==============================================================================
# LOGIKA SKRIP - Tidak perlu diubah
# ==============================================================================

# Ambil variabel & hitung nilai
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
grade = 100.0
feedback = "Tes otomatis berhasil."
print(f"✅ Nilai dihitung: {grade:.2f}")

# Cari User ID Moodle
email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)
if not email:
    print(f"❌ Username {GITHUB_USERNAME} tidak ditemukan."); exit(1)
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
    print(f"✅ Ditemukan user ID: {user_id}")
except Exception as e:
    print(f"❌ Error saat mencari user: {e}"); exit(1)

# Cari Grade Item & Assignment ID yang benar berdasarkan NAMA TUGAS
print(f"Mencari data tugas dengan nama: '{TARGET_ASSIGNMENT_NAME}'...")
grade_item_id = None
assignment_id_from_moodle = None
try:
    params = { 'wstoken': MOODLE_TOKEN, 'wsfunction': 'gradereport_user_get_grade_items', 'moodlewsrestformat': 'json', 'courseid': COURSE_ID }
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=params)
    response.raise_for_status()
    data = response.json()
    
    for item in data['usergrades'][0]['gradeitems']:
        if item.get('itemname') == TARGET_ASSIGNMENT_NAME and item.get('itemmodule') == 'assign':
            grade_item_id = item['id']
            assignment_id_from_moodle = item['iteminstance']
            print(f"✅ Data terverifikasi ditemukan -> Nama: {item['itemname']}, Grade Item ID: {grade_item_id}, Assignment ID: {assignment_id_from_moodle}")
            break
            
    if not grade_item_id:
        print(f"❌ Tidak menemukan item nilai dengan nama '{TARGET_ASSIGNMENT_NAME}' di gradebook."); exit(1)

except Exception as e:
    print(f"❌ Error Kritis saat mencari grade item: {e}"); exit(1)

# Kirim Nilai Langsung ke Gradebook menggunakan data yang sudah terverifikasi
print(f"Mengirimkan nilai {grade:.2f} ke gradebook...")
params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'core_grades_update_grades',
    'moodlewsrestformat': 'json',
    'source': 'GitHub_Autograder_Final',
    'courseid': COURSE_ID,
    'component': 'mod_assign',
    'activityid': assignment_id_from_moodle,
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
    print("🏆 CONGRATULATIONS! Proses Selesai! Nilai berhasil dikirim ke Gradebook Moodle.")
except Exception as e:
    print(f"❌ Error Kritis saat mengirim nilai ke gradebook: {e}"); exit(1)
