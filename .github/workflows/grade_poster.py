import os
import requests
import json

# ==============================================================================
# KONFIGURASI - Pastikan ini sudah benar
# ==============================================================================
MOODLE_URL = "http://52.63.155.102"
COURSE_ID = 2
ASSIGNMENT_ID = 3 # Kita set ke 3 sesuai kasus Anda

GITHUB_TO_EMAIL_MAP = {
    "DhaniDS": "fastgoole@gmail.com",
    "dhanidnawans12": "dhanidnawans12@gmail.com",
}

# ==============================================================================
# LOGIKA SKRIP
# ==============================================================================

# Langkah 1 & 2: Ambil variabel dan hitung nilai
MOODLE_TOKEN = os.environ.get('MOODLE_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
grade = 100.0 # Kita set manual ke 100 untuk tes
feedback = "Tes investigasi."

# Langkah 3: Cari User ID Moodle
email = GITHUB_TO_EMAIL_MAP.get(GITHUB_USERNAME)
if not email:
    print(f"❌ Username {GITHUB_USERNAME} tidak ditemukan.")
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

# --- Langkah 4 (INVESTIGASI): Ambil dan Cetak Data Gradebook ---
print(f"Mencari ID item nilai di gradebook untuk tugas ID {ASSIGNMENT_ID}...")
grade_item_id = None
try:
    params = { 'wstoken': MOODLE_TOKEN, 'wsfunction': 'gradereport_user_get_grade_items', 'moodlewsrestformat': 'json', 'courseid': COURSE_ID }
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=params)
    response.raise_for_status()
    data = response.json()

    # ==========================================================================
    # BAGIAN DEBUG UTAMA - MENCETAK DATA MENTAH
    # ==========================================================================
    print("\n--- [DEBUG] DATA GRADEBOOK MENTAH DARI MOODLE ---")
    print(json.dumps(data, indent=2)) # Mencetak JSON dengan format yang mudah dibaca
    print("--- [DEBUG] AKHIR DARI DATA MENTAH ---\n")
    # ==========================================================================

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

# --- Langkah 5: Kirim Nilai (Untuk saat ini, kita bisa lewati agar fokus pada debug) ---
print("ℹ️ Proses investigasi selesai. Langkah pengiriman nilai dilewati untuk saat ini.")
