import sqlite3

DATABASE = "database.db"
QURAN_FILE = "data/quran-simple.txt"

conn = sqlite3.connect(DATABASE)

inserted = 0

with open(QURAN_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split("|", 2)

        if len(parts) != 3:
            continue

        surah_number, verse_number, arabic_text = parts

        surah = conn.execute(
            "SELECT id FROM surahs WHERE number = ?",
            (int(surah_number),)
        ).fetchone()

        if surah is None:
            print("Surah not found:", surah_number)
            continue

        conn.execute(
            """
            INSERT INTO verses
            (surah_id, verse_number, arabic_text)
            VALUES (?, ?, ?)
            """,
            (
                surah[0],
                int(verse_number),
                arabic_text
            )
        )

        inserted += 1

conn.commit()
conn.close()

print("Arabic verses imported:", inserted)
