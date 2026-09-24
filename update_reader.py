from pathlib import Path

p = Path("templates/quran_reader.html")

html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ surah['name_en'] }} — Quran Seerah</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #f5f7f6;
    color: #222;
    font-family: Arial, sans-serif;
}

header {
    background: #123d2a;
    padding: 16px;
}

header a {
    color: white;
    text-decoration: none;
    font-weight: bold;
}

.container {
    max-width: 900px;
    margin: auto;
    padding: 18px;
}

.surah-header {
    background: white;
    border-radius: 18px;
    padding: 24px;
    text-align: center;
    margin-bottom: 18px;
    box-shadow: 0 4px 16px rgba(0,0,0,.06);
}

.surah-title {
    font-size: 30px;
    font-weight: bold;
    color: #123d2a;
}

.details {
    margin-top: 8px;
    color: #777;
}

.reader-controls {
    background: white;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,.06);
}

.control-group {
    margin-bottom: 14px;
}

.control-label {
    display: block;
    font-size: 13px;
    font-weight: bold;
    color: #555;
    margin-bottom: 7px;
}

select {
    width: 100%;
    padding: 13px;
    border: 1px solid #ddd;
    border-radius: 12px;
    background: white;
    font-size: 15px;
}

.tafsir-button {
    display: block;
    width: 100%;
    text-align: center;
    padding: 13px;
    border-radius: 12px;
    text-decoration: none;
    font-weight: bold;
    background: #123d2a;
    color: white;
}

.tafsir-button.off {
    background: #e9eeeb;
    color: #123d2a;
}

.verse {
    background: white;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 4px 16px rgba(0,0,0,.05);
    scroll-margin-top: 20px;
}

.verse-number {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #123d2a;
    color: white;
    border-radius: 50%;
    font-size: 13px;
    font-weight: bold;
    margin-bottom: 14px;
}

.arabic-text {
    direction: rtl;
    text-align: right;
    font-size: 29px;
    line-height: 2.2;
    margin-bottom: 20px;
    font-family: "Noto Naskh Arabic", "Amiri", serif;
}

.translation-box,
.tafsir-box {
    border-radius: 14px;
    padding: 15px;
    margin-top: 12px;
}

.translation-box {
    background: #f1f6f3;
    border-left: 4px solid #123d2a;
}

.tafsir-box {
    background: #fff8e7;
    border-left: 4px solid #c58b21;
}

.translation-label,
.tafsir-label {
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 7px;
}

.translation-label {
    color: #123d2a;
}

.tafsir-label {
    color: #9a6a08;
}

.translation-text {
    font-size: 16px;
    line-height: 1.7;
}

.tafsir-text {
    direction: rtl;
    text-align: right;
    font-size: 16px;
    line-height: 2;
}

.verse-actions {
    display: flex;
    gap: 8px;
    margin-top: 18px;
    flex-wrap: wrap;
}

.verse-actions form {
    flex: 1;
    min-width: 140px;
}

button {
    width: 100%;
    border: 0;
    padding: 11px;
    border-radius: 11px;
    font-weight: bold;
}

.bookmark-button {
    background: #e8f0eb;
    color: #123d2a;
}

.bookmark-button.bookmarked {
    background: #123d2a;
    color: white;
}

.progress-button {
    background: #f1f1f1;
    color: #444;
}

.navigation {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin: 25px 0;
}

.nav-button {
    flex: 1;
    display: block;
    text-align: center;
    background: #123d2a;
    color: white;
    text-decoration: none;
    padding: 13px;
    border-radius: 12px;
    font-weight: bold;
}

.nav-disabled {
    opacity: .35;
}

@media (max-width: 600px) {
    .container {
        padding: 12px;
    }

    .surah-title {
        font-size: 25px;
    }

    .arabic-text {
        font-size: 25px;
        line-height: 2;
    }

    .verse {
        padding: 16px;
    }

    .navigation {
        flex-direction: column;
    }
}
</style>
</head>

<body>

<header>
<a href="/quran">← Back to Surahs</a>
</header>

<main class="container">

<section class="surah-header">
<div class="surah-title">
{{ surah['name_en'] }}
</div>

<div class="details">
{{ surah['revelation_type'] }}
•
{{ surah['verse_count'] }} verses
</div>
</section>

<section class="reader-controls">

<div class="control-group">
<label class="control-label">Translation</label>

<select onchange="changeLanguage(this.value)">
<option value="en" {% if selected_language == 'en' %}selected{% endif %}>
English
</option>

<option value="am" {% if selected_language == 'am' %}selected{% endif %}>
Amharic
</option>

<option value="om" {% if selected_language == 'om' %}selected{% endif %}>
Afaan Oromo
</option>

<option value="aa" {% if selected_language == 'aa' %}selected{% endif %}>
Afar
</option>

<option value="so" {% if selected_language == 'so' %}selected{% endif %}>
Somali
</option>

<option disabled>
Tigrinya — Not available yet
</option>
</select>
</div>

<div class="control-group">
<span class="control-label">Tafsir</span>

{% if show_tafsir %}

<a href="/quran/{{ surah['number'] }}?lang={{ selected_language }}&tafsir=0"
class="tafsir-button">
📖 Tafsir: At-Tafsir Al-Muyassar — ON
</a>

{% else %}

<a href="/quran/{{ surah['number'] }}?lang={{ selected_language }}&tafsir=1"
class="tafsir-button off">
📖 Show Tafsir: At-Tafsir Al-Muyassar
</a>

{% endif %}
</div>

</section>

{% for verse in verses %}

<article class="verse" id="verse-{{ verse['id'] }}">

<div class="verse-number">
{{ verse['verse_number'] }}
</div>

<div class="arabic-text">
{{ verse['arabic_text'] }}
</div>

{% if selected_language == 'en' and verse['translation_en'] %}

<div class="translation-box">
<div class="translation-label">English</div>
<div class="translation-text">
{{ verse['translation_en'] }}
</div>
</div>

{% elif selected_language == 'am' and verse['translation_am'] %}

<div class="translation-box">
<div class="translation-label">Amharic</div>
<div class="translation-text">
{{ verse['translation_am'] }}
</div>
</div>

{% elif selected_language in ['om', 'aa', 'so'] and translation_map.get(verse['id']) %}

<div class="translation-box">
<div class="translation-label">{{ language_name }}</div>
<div class="translation-text">
{{ translation_map.get(verse['id']) }}
</div>
</div>

{% endif %}

{% if show_tafsir and tafsir_map.get(verse['id']) %}

<div class="tafsir-box">
<div class="tafsir-label">
At-Tafsir Al-Muyassar
</div>

<div class="tafsir-text">
{{ tafsir_map.get(verse['id']) }}
</div>
</div>

{% endif %}

<div class="verse-actions">

<form method="POST" action="/bookmark/{{ verse['id'] }}">

{% if verse['is_bookmarked'] %}

<button type="submit" class="bookmark-button bookmarked">
✅ Bookmarked
</button>

{% else %}

<button type="submit" class="bookmark-button">
🔖 Bookmark
</button>

{% endif %}

</form>

<form method="POST" action="/save-progress/{{ verse['id'] }}">

<button type="submit" class="progress-button">
📍 Save Progress
</button>

</form>

</div>

</article>

{% endfor %}

<div class="navigation">

{% if previous_surah %}

<a href="/quran/{{ previous_surah['number'] }}?lang={{ selected_language }}&tafsir={{ 1 if show_tafsir else 0 }}"
class="nav-button">
← Previous
</a>

{% else %}

<span class="nav-button nav-disabled">
← Previous
</span>

{% endif %}

{% if next_surah %}

<a href="/quran/{{ next_surah['number'] }}?lang={{ selected_language }}&tafsir={{ 1 if show_tafsir else 0 }}"
class="nav-button">
Next →
</a>

{% else %}

<span class="nav-button nav-disabled">
Next →
</span>

{% endif %}

</div>

</main>

<script>
function changeLanguage(language) {
    const params = new URLSearchParams(window.location.search);
    params.set("lang", language);
    params.set("tafsir", params.get("tafsir") || "0");

    window.location.href =
        "/quran/{{ surah['number'] }}?" + params.toString();
}

document.addEventListener("DOMContentLoaded", function () {

    const target = window.location.hash;

    if (target) {

        const element = document.querySelector(target);

        if (element) {

            setTimeout(function () {

                element.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });

                element.style.outline = "3px solid #123d2a";

                setTimeout(function () {
                    element.style.outline = "";
                }, 2000);

            }, 300);
        }
    }
});
</script>

</body>
</html>
'''

p.write_text(html)
print("READER PAGE UPDATED")
