import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import mysql.connector
import hashlib

# --- Config ---
SONG_DIR = "songs"
COVER_DIR = "covers"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "MySQL_Abhuday",
    "database": "DBMS_Project"
}


# --- DB Setup ---
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


# --- Extract cover and save it ---
def extract_cover_art(mp3_path, title):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                filename = f"{title.replace(' ', '_')}.jpg"
                path = os.path.join(COVER_DIR, filename)
                with open(path, "wb") as img:
                    img.write(tag.data)
                return filename
    except Exception as e:
        print(f"⚠️ No cover found for {title}: {e}")
    return None


# --- Insert into DB ---
def insert_song(title, artist_id, album_id, genre_id, release_date, audio_file, thumbnail):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Songs (Title, artistId, albumId, genre, releaseDate, audioFile, thumbnail)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, artist_id, album_id, genre_id, release_date, audio_file, thumbnail))
        conn.commit()
        print(f"✅ Inserted: {title}")
    except mysql.connector.Error as err:
        print(f"❌ Error inserting {title}: {err}")
    finally:
        cursor.close()
        conn.close()


# --- Bulk Process ---
def bulk_import():
    os.makedirs(COVER_DIR, exist_ok=True)

    for filename in os.listdir(SONG_DIR):
        if filename.endswith(".mp3"):
            title = os.path.splitext(filename)[0]
            mp3_path = os.path.join(SONG_DIR, filename)

            # Dummy values for now, update this to match your actual artist/album/genre IDs
            artist_id = 1
            album_id = 1
            genre_id = 2
            release_date = "2024-01-01"

            cover = extract_cover_art(mp3_path, title)
            insert_song(title, artist_id, album_id, genre_id, release_date, filename, cover)


if __name__ == "__main__":
    bulk_import()
