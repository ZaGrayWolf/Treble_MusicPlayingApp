import mysql.connector
import hashlib
import re
import bcrypt
import json


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="MySQL_Abhuday",
            database="DBMS_Project"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


def verify_password(hashed_password, user_password):
    try:
        return bcrypt.checkpw(user_password.encode(), hashed_password.encode())
    except Exception:
        return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()


def validate_password(password):
    return (
            len(password) >= 8 and
            re.search(r"\d", password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )


def user_exists(username):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM Users WHERE name = %s", (username,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def signup_user(name, password, sub_type):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Users (name, password, subscription_type, date_joined) VALUES (%s, %s, %s, CURDATE())",
                    (name, hash_password(password), sub_type))
        conn.commit()
        return True
    except Exception as e:
        print(f"Signup error: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def login_user(name, password):
    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, password FROM Users WHERE name = %s", (name,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row and verify_password(row['password'], password):
        return row['user_id']
    return None


def get_user_name(uid):
    conn = get_db_connection()
    if not conn:
        return "User"

    cur = conn.cursor()
    cur.execute("SELECT name FROM Users WHERE user_id = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else "User"


def get_user_profile(uid):
    conn = get_db_connection()
    if not conn:
        return {"name": "User", "subscription_type": "Unknown", "date_joined": "Unknown"}

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT name, subscription_type, date_joined FROM Users WHERE user_id = %s", (uid,))
    profile = cur.fetchone()
    cur.close()
    conn.close()
    return profile


def change_password(uid, new_pass):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        cur.execute("UPDATE Users SET password = %s WHERE user_id = %s", (hash_password(new_pass), uid))
        conn.commit()
        return True
    except Exception as e:
        print(f"Password change error: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def update_subscription(uid, subscription_type):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        cur.execute("UPDATE Users SET subscription_type = %s WHERE user_id = %s",
                    (subscription_type, uid))
        conn.commit()
        return True
    except Exception as e:
        print(f"Subscription update error: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def delete_user(uid):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        # Nested delete query for PlaylistSongs
        cur.execute("""
            DELETE FROM PlaylistSongs
            WHERE playlistId IN (
                SELECT playlistId
                FROM Playlists
                WHERE userId = %s
            )
        """, (uid,))

        # Nested delete query for Playlists
        cur.execute("""
            DELETE FROM Playlists
            WHERE userId = %s
        """, (uid,))

        # Delete user
        cur.execute("DELETE FROM Users WHERE user_id = %s", (uid,))
        conn.commit()
        return True
    except Exception as e:
        print(f"User deletion error: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_top_songs(limit=5):
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    try:
        cur.callproc('GetTopSongs', (limit,))  # Call stored procedure
        result = []
        for res in cur.stored_results():
            result = res.fetchall()
        return result
    except Exception as e:
        print(f"Error fetching top songs: {e}")
        return []
    finally:
        cur.close()
        conn.close()




def get_recent_songs(limit=5):
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT Title, releaseDate FROM Songs ORDER BY releaseDate DESC LIMIT %s", (limit,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_all_genres():
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT genreName FROM Genres")
    genres = cur.fetchall()
    cur.close()
    conn.close()
    return genres


def get_songs(search_query=None):
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    if search_query:
        query = "SELECT song_id, Title, audioFile, thumbnail FROM Songs WHERE Title LIKE %s"
        cursor.execute(query, (f"%{search_query}%",))
    else:
        query = "SELECT song_id, Title, audioFile, thumbnail FROM Songs"
        cursor.execute(query)

    songs = cursor.fetchall()
    cursor.close()
    conn.close()
    return songs


def get_all_song_titles():
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT song_id, Title FROM Songs")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_song_id_by_title(title):
    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor()
    cur.execute("SELECT song_id FROM Songs WHERE Title = %s", (title,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def playlist_exists(user_id, name):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM Playlists WHERE userId = %s AND name = %s", (user_id, name))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def create_playlist(user_id, name):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Playlists (userId, name) VALUES (%s, %s)", (user_id, name))
        conn.commit()
        return True
    except Exception as e:
        print(f"Create playlist error: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_user_playlists(user_id):
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT 
                p.playlistId,
                p.name,
                (SELECT COUNT(*) FROM PlaylistSongs ps WHERE ps.playlistId = p.playlistId) AS song_count
            FROM Playlists p
            WHERE p.userId = %s
        """, (user_id,))
        playlists = cur.fetchall()
        return playlists
    except Exception as e:
        print(f"Error fetching user playlists: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def add_song_to_playlist(playlist_id, song_id):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        # Check if playlist and song exist using nested queries
        cur.execute("""
            INSERT INTO PlaylistSongs (playlistId, songId)
            SELECT %s, %s
            WHERE EXISTS (SELECT 1 FROM Playlists WHERE playlistId = %s)
              AND EXISTS (SELECT 1 FROM Songs WHERE song_id = %s)
        """, (playlist_id, song_id, playlist_id, song_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Add to playlist error: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def search_songs(search_query, genre=None):
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    try:
        if genre:
            cur.execute("""
                SELECT s.song_id, s.Title, s.audioFile, s.thumbnail
                FROM Songs s
                WHERE s.Title LIKE %s
                  AND s.genreId IN (
                      SELECT g.genreId
                      FROM Genres g
                      WHERE g.genreName = %s
                  )
            """, (f"%{search_query}%", genre))
        else:
            cur.execute("SELECT song_id, Title, audioFile, thumbnail FROM Songs WHERE Title LIKE %s", (f"%{search_query}%",))
        songs = cur.fetchall()
        return songs
    except Exception as e:
        print(f"Error searching songs: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def batch_insert_songs(song_data):
    conn = get_db_connection()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        cur.callproc('BatchInsertSongs', (json.dumps(song_data),))  # Pass JSON data
        conn.commit()
        return True
    except Exception as e:
        print(f"Batch insert error: {e}")
        return False
    finally:
        cur.close()
        conn.close()
