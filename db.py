import mysql.connector
import hashlib

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="******",
        database="*****"
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_exists(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Users WHERE name = %s", (username,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

def signup_user(name, password, subscription_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)

    query = "INSERT INTO Users (name, password, subscription_type, date_joined) VALUES (%s, %s, %s, CURDATE())"
    try:
        cursor.execute(query, (name, hashed_password, subscription_type))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def login_user(name, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)

    query = "SELECT user_id FROM Users WHERE name = %s AND password = %s"
    cursor.execute(query, (name, hashed_password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user[0] if user else None

def get_songs(search_query=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search_query:
        query = "SELECT song_id, Title, artistId, audioFile, thumbnail FROM Songs WHERE Title LIKE %s"
        cursor.execute(query, (f"%{search_query}%",))
    else:
        query = "SELECT song_id, Title, artistId, audioFile, thumbnail FROM Songs"
        cursor.execute(query)

    songs = cursor.fetchall()
    cursor.close()
    conn.close()
    return songs



def playlist_exists(user_id, playlist_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT 1 FROM Playlists WHERE userId = %s AND name = %s"
    cursor.execute(query, (user_id, playlist_name))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

def create_playlist(user_id, playlist_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO Playlists (userId, name) VALUES (%s, %s)"
    try:
        cursor.execute(query, (user_id, playlist_name))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_playlists(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT playlistId, name FROM Playlists WHERE userId = %s"
    cursor.execute(query, (user_id,))
    playlists = cursor.fetchall()
    cursor.close()
    conn.close()
    return playlists

def add_song_to_playlist(playlist_id, song_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO PlaylistSongs (playlistId, songId) VALUES (%s, %s)"
    try:
        cursor.execute(query, (playlist_id, song_id))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_all_song_titles():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT song_id, Title FROM Songs")
    songs = cursor.fetchall()
    cursor.close()
    conn.close()
    return songs

def get_song_id_by_title(title):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT song_id FROM Songs WHERE Title = %s", (title,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def get_user_name(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM Users WHERE user_id = %s", (user_id,))
    name = cursor.fetchone()
    cursor.close()
    conn.close()
    return name[0] if name else "User"

def get_top_songs(limit=5):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Title FROM Songs LIMIT %s", (limit,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_recent_songs(limit=5):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Title, releaseDate FROM Songs ORDER BY releaseDate DESC LIMIT %s", (limit,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_all_genres():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT genreName FROM Genres")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result
