import sqlite3

DATABASE = "database.db"

TRANSLATIONS = {
    "translation_en": "data/english-sahih.txt",
    "translation_am": "data/amharic-sadiq.txt"
}

conn = sqlite3.connect(DATABASE)

updated_en = 0
updated_am = 0


def import_translation(column, filename):
    updated = 0

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split("|", 2)

            if len(parts) != 3:
                continue

            surah_number, verse_number, translation = parts

            result = conn.execute(
                f"""
                UPDATE verses
                SET {column} = ?
                WHERE surah_id = (
                    SELECT id
                    FROM surahs
                    WHERE number = ?
                )
                AND verse_number = ?
                """,
                (
                    translation,
                    int(surah_number),
                    int(verse_number)
                )
            )

            if result.rowcount == 1:
                updated += 1

    return updated


updated_en = import_translation(
    "translation_en",
    TRANSLATIONS["translation_en"]
)

updated_am = import_translation(
    "translation_am",
    TRANSLATIONS["translation_am"]
)

conn.commit()

print("English translations imported:", updated_en)
print("Amharic translations imported:", updated_am)

total = conn.execute(
    "SELECT COUNT(*) FROM verses"
).fetchone()[0]

english = conn.execute(
    "SELECT COUNT(*) FROM verses WHERE translation_en IS NOT NULL"
).fetchone()[0]

amharic = conn.execute(
    "SELECT COUNT(*) FROM verses WHERE translation_am IS NOT NULL"
).fetchone()[0]

print("Total Arabic verses:", total)
print("English translations:", english)
print("Amharic translations:", amharic)

conn.close()
