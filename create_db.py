import sqlite3

# Create DB and table for students
conn = sqlite3.connect("students.db")
cursor = conn.cursor()

# Students table
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    fee_status TEXT,
    course TEXT
)
""")

# Insert sample students
students = [
    ("palak", "palak123", "Palak Srivastava", "Paid", "B.A. Economics"),
    ("harsh", "harsh123", "Harsh Dixit", "Pending", "B.Tech CSE"),
    ("neha", "neha123", "Neha Verma", "Paid", "B.Sc Physics")
]

cursor.executemany(
    "INSERT OR IGNORE INTO students (username, password, name, fee_status, course) VALUES (?, ?, ?, ?, ?)",
    students
)

# Timetable table
cursor.execute("""
CREATE TABLE IF NOT EXISTS timetables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT NOT NULL,
    day TEXT NOT NULL,
    schedule TEXT NOT NULL
)
""")

# Insert sample timetables (5 days classes + 2 holidays)
timetables = [
    # B.A. Economics
    ("B.A. Economics", "Monday", "9:00-10:00: Political Science, 10:00-11:00: Mathematics, 11:00-12:00: Economics"),
    ("B.A. Economics", "Tuesday", "9:00-10:00: History, 10:00-11:00: Economics, 11:00-12:00: English"),
    ("B.A. Economics", "Wednesday", "Holiday"),
    ("B.A. Economics", "Thursday", "9:00-10:00: Political Science, 10:00-11:00: Mathematics, 11:00-12:00: Economics"),
    ("B.A. Economics", "Friday", "9:00-10:00: History, 10:00-11:00: Economics, 11:00-12:00: English"),
    ("B.A. Economics", "Saturday", "Holiday"),
    
    # B.Tech CSE
    ("B.Tech CSE", "Monday", "9:00-10:00: Computer Networks, 10:00-11:00: Data Structures, 11:00-12:00: Physics"),
    ("B.Tech CSE", "Tuesday", "9:00-10:00: Algorithms, 10:00-11:00: Mathematics, 11:00-12:00: C Programming"),
    ("B.Tech CSE", "Wednesday", "9:00-10:00: Computer Networks, 10:00-11:00: Data Structures, 11:00-12:00: Physics"),
    ("B.Tech CSE", "Thursday", "9:00-10:00: Algorithms, 10:00-11:00: Mathematics, 11:00-12:00: C Programming"),
    ("B.Tech CSE", "Friday", "Holiday"),
    ("B.Tech CSE", "Saturday", "Holiday"),
    
    # B.Sc Physics
    ("B.Sc Physics", "Monday", "9:00-10:00: Mechanics, 10:00-11:00: Electromagnetism, 11:00-12:00: Chemistry"),
    ("B.Sc Physics", "Tuesday", "9:00-10:00: Optics, 10:00-11:00: Thermodynamics, 11:00-12:00: Mathematics"),
    ("B.Sc Physics", "Wednesday", "9:00-10:00: Mechanics, 10:00-11:00: Electromagnetism, 11:00-12:00: Chemistry"),
    ("B.Sc Physics", "Thursday", "9:00-10:00: Optics, 10:00-11:00: Thermodynamics, 11:00-12:00: Mathematics"),
    ("B.Sc Physics", "Friday", "Holiday"),
    ("B.Sc Physics", "Saturday", "Holiday"),
]

cursor.executemany(
    "INSERT OR IGNORE INTO timetables (course, day, schedule) VALUES (?, ?, ?)",
    timetables
)

conn.commit()
conn.close()
print("Database created with students and timetables!")
