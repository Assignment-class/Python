import os
import requests
import json

# --- 1. Ambil Variabel dari Environment ---
MOODLE_URL = os.environ['MOODLE_URL']
MOODLE_TOKEN = os.environ['MOODLE_TOKEN']
COURSE_ID = os.environ['MOODLE_COURSE_ID']
ASSIGNMENT_ID = os.environ['MOODLE_ASSIGNMENT_ID']
GITHUB_USERNAME = os.environ['GITHUB_USERNAME']

# --- 2. Baca Hasil Tes dan Hitung Skor ---
try:
    with open('report.json') as f:
        report = json.load(f)
    
    total_tests = report['summary']['total']
    passed_tests = report['summary'].get('passed', 0)
    
    # Kalkulasi nilai (0-100)
    grade = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    feedback = f"Hasil Tes:\nTotal: {total_tests}\nLulus: {passed_tests}\nGagal: {total_tests - passed_tests}"

except FileNotFoundError:
    grade = 0
    feedback = "Gagal menjalankan tes. File report.json tidak ditemukan."

print(f"Calculated Grade for {GITHUB_USERNAME}: {grade}")
print(f"Feedback: {feedback}")

# --- 3. Dapatkan Moodle User ID dari Username GitHub ---
# Di Moodle, custom user profile field untuk 'github_username' harus dibuat terlebih dahulu
# Site admin -> Users -> User profile fields -> Add new profile field (text input)
# dengan shortname 'githubusername'

rest_params = {
    'wstoken': MOODLE_TOKEN,
    'wsfunction': 'core_user_get_users',
    'moodlewsrestformat': 'json',
    'criteria[0][key]': 'profile_githubusername', # Ganti dengan shortname field Anda
    'criteria[0][value]': GITHUB_USERNAME
}

try:
    response = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=rest_params)
    response.raise_for_status()
    users = response.json()['users']
    if not users:
        print(f"Error: User Moodle dengan username GitHub '{GITHUB_USERNAME}' tidak ditemukan.")
        exit(1)
    moodle_user_id = users[0]['id']
    print(f"Found Moodle User ID: {moodle_user_id}")

except Exception as e:
    print(f"Error saat mencari user Moodle: {e}")
    print("Response:", response.text)
    exit(1)

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
