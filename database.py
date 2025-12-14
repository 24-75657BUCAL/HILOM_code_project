import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="hilom_db"
)

cursor = conn.cursor(dictionary=True)

query = """
SELECT 
    u.id AS user_id,
    u.name AS user_name,
    u.email AS user_email,
    u.created_at AS user_created,

    j.id AS journal_id,
    j.title AS journal_title,
    j.content AS journal_content,
    j.mood AS journal_mood,
    j.date AS journal_date,
    j.created_at AS journal_created,

    mh.id AS music_history_id,
    mh.song_title AS music_title,
    mh.mood AS music_mood,
    mh.timestamp AS music_timestamp,

    f.id AS favorite_id,
    f.song_title AS favorite_item,
    f.type AS favorite_type,

    lh.id AS login_event_id,
    lh.action AS login_action,
    lh.timestamp AS login_time,

    a.id AS appointment_id,
    a.hospital,
    a.doctor,
    a.schedule_date,
    a.time_slot,
    a.patient_name,
    a.age,
    a.contact,
    a.concern,
    a.status,
    a.created_at AS appointment_created

FROM hilom_db_users u
LEFT JOIN hilom_db_journals j ON u.id = j.user_id
LEFT JOIN hilom_db_music_history mh ON u.id = mh.user_id
LEFT JOIN hilom_db_favorites f ON u.id = f.user_id
LEFT JOIN hilom_db_login_history lh ON u.id = lh.user_id
LEFT JOIN hilom_db_appointments a ON u.id = a.user_id
ORDER BY u.id;
"""

cursor.execute(query)
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()
