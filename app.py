import json
import os
from data.seerah_data import SEERAH, SEERAH_LANGUAGES, SEERAH_UI

from flask import Flask, render_template, redirect, request
import sqlite3

app = Flask(__name__)

# 604-page Quran mapping
QURAN_JUZ_MAPPING_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "quran_juz_mapping.json"
)

with open(QURAN_JUZ_MAPPING_FILE, "r", encoding="utf-8") as f:
    QURAN_JUZ_MAPPING = json.load(f)

QURAN_PAGE_MAPPING_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "quran_page_mapping.json"
)

with open(QURAN_PAGE_MAPPING_FILE, "r", encoding="utf-8") as f:
    QURAN_PAGE_MAPPING = json.load(f)



DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def remove_arabic_diacritics(text):
    if not text:
        return ""
    diacritics = "ًٌٍَُِّْـٰٱ"
    return "".join(
        character for character in text
        if character not in diacritics
    )


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/quran")
def quran():
    conn = get_db()

    surahs = conn.execute("""
        SELECT *
        FROM surahs
        ORDER BY number
    """).fetchall()

    progress = conn.execute("""
        SELECT
            reading_progress.*,
            surahs.number AS surah_number,
            surahs.name_en AS surah_name,
            verses.id AS verse_id
        FROM reading_progress
        JOIN surahs
            ON surahs.id = reading_progress.surah_id
        JOIN verses
            ON verses.surah_id = reading_progress.surah_id
            AND verses.verse_number = reading_progress.verse_number
        WHERE reading_progress.user_id IS NULL
        ORDER BY reading_progress.updated_at DESC,
                 reading_progress.id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    return render_template(
        "quran.html",
        surahs=surahs,
        progress=progress
    )



@app.route("/quran/page/<int:page_number>")
def quran_page(page_number):
    if page_number < 1 or page_number > 604:
        return "Quran page not found", 404

    page_mapping = QURAN_PAGE_MAPPING.get(str(page_number), [])

    if not page_mapping:
        return "Quran page data not found", 404

    conn = get_db()

    verses = []

    for item in page_mapping:
        verse = conn.execute("""
            SELECT
                v.id,
                v.surah_id,
                v.verse_number,
                v.arabic_text,
                v.translation_en,
                v.translation_am,
                s.number AS surah_number,
                s.name_en AS surah_name_en
            FROM verses v
            JOIN surahs s ON s.id = v.surah_id
            WHERE s.number = ?
              AND v.verse_number = ?
        """, (item["surah"], item["verse"])).fetchone()

        if verse:
            verses.append(verse)

    conn.close()

    if not verses:
        return "No verses found for this Quran page", 404

    return render_template(
        "quran_page.html",
        verses=verses,
        page_number=page_number,
        total_pages=604
    )

@app.route("/juz")
def juz():
    return render_template(
        "juz.html",
        juzs=QURAN_JUZ_MAPPING
    )


@app.route("/quran/juz/<int:juz_number>")
def quran_juz(juz_number):
    if juz_number < 1 or juz_number > 30:
        return "Juz not found", 404

    juz_info = QURAN_JUZ_MAPPING.get(str(juz_number))

    if not juz_info:
        return "Juz data not found", 404

    conn = get_db()
    verses = []

    for surah, verse_range in juz_info["verse_mapping"].items():
        start, end = map(int, verse_range.split("-"))

        rows = conn.execute("""
            SELECT
                v.id,
                v.surah_id,
                v.verse_number,
                v.arabic_text,
                v.translation_en,
                v.translation_am,
                s.number AS surah_number,
                s.name_en AS surah_name_en
            FROM verses v
            JOIN surahs s ON s.id = v.surah_id
            WHERE s.number = ?
              AND v.verse_number BETWEEN ? AND ?
            ORDER BY v.verse_number
        """, (int(surah), start, end)).fetchall()

        verses.extend(rows)

    conn.close()

    if not verses:
        return "No verses found for this Juz", 404

    previous_juz = juz_number - 1 if juz_number > 1 else None
    next_juz = juz_number + 1 if juz_number < 30 else None

    return render_template(
        "juz_reader.html",
        verses=verses,
        juz_number=juz_number,
        juz_info=juz_info,
        previous_juz=previous_juz,
        next_juz=next_juz
    )


@app.route("/quran-search")
def quran_search():
    query = request.args.get("q", "").strip()

    language = request.args.get("lang", "en")

    allowed_languages = {
        "en": "English",
        "am": "Amharic",
        "om": "Afaan Oromo",
        "aa": "Afar",
        "so": "Somali"
    }

    if language not in allowed_languages:
        language = "en"

    results = []

    if query:
        conn = get_db()

        rows = conn.execute("""
            SELECT
                verses.id,
                verses.surah_id,
                verses.verse_number,
                verses.arabic_text,
                verses.translation_en,
                verses.translation_am,
                surahs.number AS surah_number,
                surahs.name_en AS surah_name
            FROM verses
            JOIN surahs
                ON surahs.id = verses.surah_id
            ORDER BY surahs.number, verses.verse_number
        """).fetchall()

        translation_rows = conn.execute("""
            SELECT language_code, verse_id, text
            FROM translations
            WHERE language_code IN ('om', 'aa', 'so')
        """).fetchall()

        translation_map = {}

        for row in translation_rows:
            translation_map[(row["language_code"], row["verse_id"])] = row["text"]

        normalized_query = remove_arabic_diacritics(query)
        query_lower = query.lower()

        for row in rows:

            arabic = remove_arabic_diacritics(
                row["arabic_text"] or ""
            )

            english = row["translation_en"] or ""
            amharic = row["translation_am"] or ""

            om = translation_map.get(
                ("om", row["id"]), ""
            )

            aa = translation_map.get(
                ("aa", row["id"]), ""
            )

            so = translation_map.get(
                ("so", row["id"]), ""
            )

            selected_translation = ""

            if language == "en":
                selected_translation = english

            elif language == "am":
                selected_translation = amharic

            elif language == "om":
                selected_translation = om

            elif language == "aa":
                selected_translation = aa

            elif language == "so":
                selected_translation = so

            translation_match = (
                query_lower in selected_translation.lower()
            )

            arabic_match = (
                normalized_query in arabic
            )

            if arabic_match or translation_match:

                results.append({
                    "id": row["id"],
                    "surah_id": row["surah_id"],
                    "verse_number": row["verse_number"],
                    "arabic_text": row["arabic_text"],
                    "translation_en": english,
                    "translation_am": amharic,
                    "translation_om": om,
                    "translation_aa": aa,
                    "translation_so": so,
                    "translation": selected_translation,
                    "surah_number": row["surah_number"],
                    "surah_name": row["surah_name"]
                })

            if len(results) >= 100:
                break

        conn.close()

    return render_template(
        "quran_search.html",
        query=query,
        results=results,
        selected_language=language,
        language_name=allowed_languages[language]
    )

@app.route("/quran/<int:surah_number>")
def quran_reader(surah_number):
    language = request.args.get("lang", "en")
    show_tafsir = request.args.get("tafsir", "0") == "1"

    allowed_languages = {
        "en": "English",
        "am": "Amharic",
        "om": "Afaan Oromo",
        "aa": "Afar",
        "so": "Somali"
    }

    if language not in allowed_languages:
        language = "en"

    conn = get_db()

    surah = conn.execute("""
        SELECT *
        FROM surahs
        WHERE number = ?
    """, (surah_number,)).fetchone()

    if surah is None:
        conn.close()
        return "Surah not found", 404

    verses = conn.execute("""
        SELECT
            verses.*,
            CASE
                WHEN bookmarks.id IS NOT NULL THEN 1
                ELSE 0
            END AS is_bookmarked,
            COALESCE(bookmarks.note, '') AS bookmark_note
        FROM verses
        LEFT JOIN bookmarks
            ON bookmarks.verse_id = verses.id
            AND bookmarks.user_id IS NULL
        WHERE verses.surah_id = ?
        ORDER BY verses.verse_number
    """, (surah["id"],)).fetchall()

    translation_map = {}

    if language in ("om", "aa", "so"):
        rows = conn.execute("""
            SELECT verse_id, text
            FROM translations
            WHERE language_code = ?
        """, (language,)).fetchall()

        translation_map = {
            row["verse_id"]: row["text"]
            for row in rows
        }

    tafsir_map = {}

    if show_tafsir:
        rows = conn.execute("""
            SELECT verse_id, text
            FROM tafsir
            WHERE tafsir_key = ?
        """, ("arabic_moyassar",)).fetchall()

        tafsir_map = {
            row["verse_id"]: row["text"]
            for row in rows
        }

    previous_surah = conn.execute("""
        SELECT *
        FROM surahs
        WHERE number = ?
    """, (surah_number - 1,)).fetchone()

    next_surah = conn.execute("""
        SELECT *
        FROM surahs
        WHERE number = ?
    """, (surah_number + 1,)).fetchone()

    progress = conn.execute("""
        SELECT
            reading_progress.*,
            surahs.number AS current_surah_number,
            surahs.name_en AS current_surah_name
        FROM reading_progress
        JOIN surahs ON reading_progress.surah_id = surahs.id
        WHERE reading_progress.user_id IS NULL
        ORDER BY reading_progress.updated_at DESC, reading_progress.id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    return render_template(
        "quran_reader.html",
        surah=surah,
        verses=verses,
        previous_surah=previous_surah,
        next_surah=next_surah,
        progress=progress,
        selected_language=language,
        language_name=allowed_languages[language],
        translation_map=translation_map,
        show_tafsir=show_tafsir,
        tafsir_map=tafsir_map
    )


@app.route("/reading-stats")
def reading_stats():
    conn = get_db()

    total_verses = conn.execute(
        "SELECT COUNT(*) FROM verses"
    ).fetchone()[0]

    total_bookmarks = conn.execute(
        "SELECT COUNT(*) FROM bookmarks WHERE user_id IS NULL"
    ).fetchone()[0]

    total_notes = conn.execute("""
        SELECT COUNT(*)
        FROM bookmarks
        WHERE user_id IS NULL
        AND note IS NOT NULL
        AND TRIM(note) != ''
    """).fetchone()[0]

    total_progress = conn.execute("""
        SELECT COUNT(*)
        FROM reading_progress
        WHERE user_id IS NULL
    """).fetchone()[0]

    reading_days = conn.execute("""
        SELECT COUNT(DISTINCT DATE(updated_at))
        FROM reading_progress
        WHERE user_id IS NULL
    """).fetchone()[0]

    today_read = conn.execute("""
        SELECT COUNT(*)
        FROM reading_progress
        WHERE user_id IS NULL
        AND DATE(updated_at) = DATE('now', 'localtime')
    """).fetchone()[0] > 0

    progress = conn.execute("""
        SELECT
            reading_progress.surah_id,
            reading_progress.verse_number,
            surahs.number AS current_surah_number,
            surahs.name_en AS current_surah_name
        FROM reading_progress
        JOIN surahs ON reading_progress.surah_id = surahs.id
        WHERE reading_progress.user_id IS NULL
        ORDER BY reading_progress.updated_at DESC, reading_progress.id DESC
        LIMIT 1
    """).fetchone()

    progress_percent = 0
    surahs_completed = 0

    if progress:
        completed = conn.execute("""
            SELECT COALESCE(SUM(verse_count), 0)
            FROM surahs
            WHERE id < ?
        """, (progress["surah_id"],)).fetchone()[0]

        completed += progress["verse_number"]
        progress_percent = round(
            (completed / total_verses) * 100, 1
        ) if total_verses else 0

        surahs_completed = conn.execute("""
            SELECT COUNT(*)
            FROM surahs
            WHERE id < ?
        """, (progress["surah_id"],)).fetchone()[0]

        current_surah = conn.execute("""
            SELECT verse_count
            FROM surahs
            WHERE id = ?
        """, (progress["surah_id"],)).fetchone()

        if current_surah and progress["verse_number"] >= current_surah["verse_count"]:
            surahs_completed += 1

    conn.close()

    return render_template(
        "reading_stats.html",
        total_verses=total_verses,
        total_bookmarks=total_bookmarks,
        total_notes=total_notes,
        total_progress=total_progress,
        progress_percent=progress_percent,
        surahs_completed=surahs_completed,
        reading_days=reading_days,
        today_read=today_read,
        current_surah_name=progress["current_surah_name"] if progress else None,
        current_surah_number=progress["current_surah_number"] if progress else None,
        current_verse_number=progress["verse_number"] if progress else None,
    )


@app.route("/bookmarks")
def bookmarks():
    conn = get_db()

    bookmarks = conn.execute("""
        SELECT
            bookmarks.id AS bookmark_id,
            bookmarks.note AS note,
            verses.id AS verse_id,
            verses.verse_number,
            verses.arabic_text,
            verses.translation_en,
            verses.translation_am,
            surahs.number AS surah_number,
            surahs.name_en AS surah_name
        FROM bookmarks
        JOIN verses ON bookmarks.verse_id = verses.id
        JOIN surahs ON verses.surah_id = surahs.id
        WHERE bookmarks.user_id IS NULL
        ORDER BY bookmarks.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "bookmarks.html",
        bookmarks=bookmarks
    )



@app.route("/bookmark/<int:verse_id>", methods=["POST"])
def bookmark_verse(verse_id):
    conn = get_db()

    verse = conn.execute("""
        SELECT id, surah_id
        FROM verses
        WHERE id = ?
    """, (verse_id,)).fetchone()

    if verse is None:
        conn.close()
        return "Verse not found", 404

    existing = conn.execute("""
        SELECT id
        FROM bookmarks
        WHERE verse_id = ?
        AND user_id IS NULL
    """, (verse_id,)).fetchone()

    if existing:
        conn.execute("""
            DELETE FROM bookmarks
            WHERE id = ?
        """, (existing["id"],))
    else:
        conn.execute("""
            INSERT INTO bookmarks (user_id, verse_id)
            VALUES (NULL, ?)
        """, (verse_id,))

    conn.commit()

    surah = conn.execute("""
        SELECT number
        FROM surahs
        WHERE id = ?
    """, (verse["surah_id"],)).fetchone()

    conn.close()




    return redirect(
        f"/quran/{surah['number']}#verse-{verse_id}"
    )  
@app.route("/remove-bookmark/<int:bookmark_id>", methods=["POST"])
def remove_bookmark(bookmark_id):
    conn = get_db()

    conn.execute("""
        DELETE FROM bookmarks
        WHERE id = ?
    """, (bookmark_id,))

    conn.commit()
    conn.close()

    return redirect("/bookmarks")

@app.route("/save-note/<int:verse_id>", methods=["POST"])
def save_note(verse_id):
    note = request.form.get("note", "").strip()

    conn = get_db()

    verse = conn.execute("""
        SELECT id, surah_id
        FROM verses
        WHERE id = ?
    """, (verse_id,)).fetchone()

    if verse is None:
        conn.close()
        return "Verse not found", 404

    existing = conn.execute("""
        SELECT id
        FROM bookmarks
        WHERE verse_id = ?
        AND user_id IS NULL
    """, (verse_id,)).fetchone()

    if existing:
        conn.execute("""
            UPDATE bookmarks
            SET note = ?
            WHERE id = ?
        """, (note, existing["id"]))
    else:
        conn.execute("""
            INSERT INTO bookmarks (user_id, verse_id, note)
            VALUES (NULL, ?, ?)
        """, (verse_id, note))

    conn.commit()

    surah = conn.execute("""
        SELECT number
        FROM surahs
        WHERE id = ?
    """, (verse["surah_id"],)).fetchone()

    conn.close()

    return redirect(f"/quran/{surah['number']}#verse-{verse_id}")


@app.route("/save-progress/<int:verse_id>", methods=["POST"])
def save_progress(verse_id):
    conn = get_db()

    verse = conn.execute("""
        SELECT id, surah_id, verse_number
        FROM verses
        WHERE id = ?
    """, (verse_id,)).fetchone()

    if verse is None:
        conn.close()
        return "Verse not found", 404

    conn.execute("""
        DELETE FROM reading_progress
        WHERE user_id IS NULL
    """)

    conn.execute("""
        INSERT INTO reading_progress
        (user_id, surah_id, verse_number, updated_at)
        VALUES (NULL, ?, ?, CURRENT_TIMESTAMP)
    """, (
        verse["surah_id"],
        verse["verse_number"]
    ))

    conn.commit()

    surah = conn.execute("""
        SELECT number
        FROM surahs
        WHERE id = ?
    """, (verse["surah_id"],)).fetchone()

    conn.close()

    return redirect(
        f"/quran/{surah['number']}#verse-{verse_id}"
    )

@app.route("/seerah")
def seerah():
    lang = request.args.get("lang", "en")

    if lang not in SEERAH_LANGUAGES:
        lang = "en"

    return render_template(
        "seerah.html",
        chapters=SEERAH,
        lang=lang,
        languages=SEERAH_LANGUAGES,
        ui=SEERAH_UI[lang]
    )



@app.route("/seerah/<int:chapter_id>")
def seerah_chapter(chapter_id):
    lang = request.args.get("lang", "en")

    if lang not in SEERAH_LANGUAGES:
        lang = "en"

    if chapter_id not in SEERAH:
        return "Seerah chapter not found", 404

    chapter = SEERAH[chapter_id]

    if lang not in chapter:
        lang = "en"

    chapter_data = chapter[lang]

    previous_id = chapter_id - 1 if chapter_id > 1 else None
    next_id = chapter_id + 1 if chapter_id < 11 else None

    return render_template(
        "seerah_chapter.html",
        chapter=chapter_data,
        chapter_id=chapter_id,
        previous_id=previous_id,
        next_id=next_id,
        lang=lang,
        languages=SEERAH_LANGUAGES,
        ui=SEERAH_UI[lang]
    )


@app.route("/search")
def search():
    return "Search section - coming soon"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
