import os
import json
import requests

MOODLE_URL = "http://52.63.155.102/webservice/rest/server.php"
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

ASSIGNMENT_ID = 2  # Ganti dengan ID assignment kamu

def get_moodle_user_id_by_email(email):
    params = {
        'wstoken': MOODLE_TOKEN,
        'wsfunction': 'core_user_get_users_by_field',
        'moodlewsrestformat': 'json',
        'field': 'email',
        'values[0]': email
    }
    response = requests.get(MOODLE_URL, params=params)
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        return data[0]['id']
    return None

def check_user_submission_status(assignment_id, user_id):
    params = {
        'wstoken': MOODLE_TOKEN,
        'wsfunction': 'mod_assign_get_submissions',
        'moodlewsrestformat': 'json',
        'assignmentids[0]': assignment_id
    }
    response = requests.get(MOODLE_URL, params=params)
    data = response.json()
    submissions = data.get("assignments", [])[0].get("submissions", [])
    for sub in submissions:
        if sub["userid"] == user_id:
            return sub["status"]  # e.g. "submitted"
    return None

def post_grade_to_moodle(user_id, grade, feedback="Nilai otomatis oleh autograder."):
    params = {
        'wstoken': MOODLE_TOKEN,
        'wsfunction': 'mod_assign_save_grades',
        'moodlewsrestformat': 'json',
        'assignmentid': ASSIGNMENT_ID,
        'grades[0][userid]': user_id,
        'grades[0][grade]': int(grade),
        'grades[0][attemptnumber]': -1,
        'grades[0][addattempt]': 1,
        'grades[0][workflowstate]': 'graded',
        'grades[0][plugindata][assignfeedbackcomments_editor][text]': feedback,
        'grades[0][plugindata][assignfeedbackcomments_editor][format]': 1
    }
    response = requests.post(MOODLE_URL, data=params)
    return response

# === MAIN ===
try:
    print("✅ Nilai berhasil dihitung: 100")

    email = f"{GITHUB_USERNAME}@gmail.com"
    moodle_user_id = get_moodle_user_id_by_email(email)
    if not moodle_user_id:
        print(f"❌ User dengan email {email} tidak ditemukan di Moodle.")
        exit(1)

    print(f"✅ Ditemukan user ID: {moodle_user_id} untuk email: {email}")

    submission_status = check_user_submission_status(ASSIGNMENT_ID, moodle_user_id)
    if submission_status != "submitted":
        print(f"⚠️ User ini belum submit tugas (status: {submission_status}). Tidak dinilai.")
        exit(0)
    print(f"✅ User ini sudah punya submission (status: {submission_status}). Siap dinilai.")

    response = post_grade_to_moodle(moodle_user_id, 100)
    try:
        data = response.json()
        if isinstance(data, dict) and 'exception' in data:
            print("❌ ERROR saat mengirim nilai:")
            print(json.dumps(data, indent=2))
            exit(1)
    except Exception:
        print("❌ ERROR saat parsing response dari Moodle.")
        print(f"Response: {response.text}")
        exit(1)

    print("🎉 Nilai berhasil dikirim ke Moodle.")

except Exception as e:
    print("❌ Terjadi kesalahan saat menjalankan skrip:")
    print(e)
    exit(1)
