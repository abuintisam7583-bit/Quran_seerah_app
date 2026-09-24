import sqlite3

DB_NAME = "database.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS surahs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER UNIQUE NOT NULL,
    name_ar TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_am TEXT,
    revelation_type TEXT,
    verse_count INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    surah_id INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,
    arabic_text TEXT NOT NULL,
    translation_en TEXT,
    translation_am TEXT,
    FOREIGN KEY (surah_id) REFERENCES surahs(id),
    UNIQUE(surah_id, verse_number)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    verse_id INTEGER NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (verse_id) REFERENCES verses(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reading_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    surah_id INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (surah_id) REFERENCES surahs(id)
)
""")

conn.commit()
conn.close()

print("Quran database created successfully!")
