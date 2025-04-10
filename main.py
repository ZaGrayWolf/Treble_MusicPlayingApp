import streamlit as st
import os
import db

# Setup
AUDIO_DIR = os.path.join(os.getcwd(), "songs")
COVER_DIR = os.path.join(os.getcwd(), "covers")
st.set_page_config(page_title="Mellows", layout="wide")

# Theme setup
if "theme" not in st.session_state:
    st.session_state["theme"] = "Dark"

theme = st.sidebar.radio("🎨 Theme", ["Dark", "Light"], index=0 if st.session_state["theme"] == "Dark" else 1)
st.session_state["theme"] = theme

def apply_theme(theme):
    dark = """
    <style>
        body, .css-18e3th9, .css-1d391kg, .stApp {
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }
        .stButton>button {
            background-color: #21262d;
            color: #ffffff;
        }
        .stTextInput>div>div>input {
            background-color: #21262d;
            color: white;
        }
    </style>
    """

    light = """
    <style>
        body, .css-18e3th9, .css-1d391kg, .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        .stButton>button {
            background-color: #f0f2f6;
            color: #000000;
        }
        .stTextInput>div>div>input {
            background-color: #f0f2f6;
            color: black;
        }
    </style>
    """

    st.markdown(dark if theme == "Dark" else light, unsafe_allow_html=True)

apply_theme(st.session_state["theme"])

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# ---------- Auth Section ----------
def login():
    st.title("🔐 Login")
    name = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user_id = db.login_user(name, password)
        if user_id:
            st.session_state["user_id"] = user_id
            st.success("✅ Login Successful!")
            st.rerun()
        else:
            st.error("❌ Invalid Credentials")

def signup():
    st.title("📝 Sign Up")
    name = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    subscription_type = st.selectbox("Subscription Type", ["Free", "Premium"])
    if st.button("Sign Up"):
        if db.user_exists(name):
            st.error("❌ Username already exists.")
        else:
            if db.signup_user(name, password, subscription_type):
                user_id = db.login_user(name, password)
                if user_id:
                    st.session_state["user_id"] = user_id
                    st.success("✅ Signed up and logged in successfully!")
                    st.rerun()
            else:
                st.error("❌ Sign Up Failed. Try again.")

# ---------- Main App ----------
if st.session_state["user_id"] is None:
    auth_choice = st.radio("Select an option", ["Login", "Sign Up"])
    if auth_choice == "Login":
        login()
    else:
        signup()

else:
    st.sidebar.title("🎶 Treble")
    page = st.sidebar.radio("Go to", ["Home", "Browse", "Playlists", "Logout"])

    if page == "Home":
        st.title("🎧 Welcome to Mellows")

        user_name = db.get_user_name(st.session_state["user_id"])  # create this function in db.py
        st.markdown(f"## Hello, **{user_name}** 👋")
        st.write("Let the music play. Here's what's hot right now:")

        st.subheader("🔥 Trending Songs")
        trending = db.get_top_songs(limit=5)  # you can define based on play_count or dummy data
        for song in trending:
            st.markdown(f"🎵 **{song['Title']}**")

        st.subheader("🆕 New Releases")
        recent = db.get_recent_songs(limit=5)
        for song in recent:
            st.markdown(f"🗓️ {song['Title']} — Released on {song['releaseDate']}")

        st.subheader("🎶 Explore Genres")
        genres = db.get_all_genres()
        st.write(", ".join([genre['genreName'] for genre in genres]))

    elif page == "Browse":
        st.title("🎼 Browse Music")

        if "selected_song_id" not in st.session_state:
            st.session_state.selected_song_id = None

        search_query = st.text_input("🔎 Search for a song")
        songs = db.get_songs(search_query)

        if not songs:
            st.info("No songs found.")
        else:
            cols_per_row = 4
            rows = [songs[i:i + cols_per_row] for i in range(0, len(songs), cols_per_row)]

            for row in rows:
                cols = st.columns(cols_per_row)
                for col, song in zip(cols, row):
                    song_id = song["song_id"]
                    title = song["Title"]
                    audio_file = song.get("audioFile")
                    thumbnail = song.get("thumbnail")

                    audio_path = os.path.join("songs", audio_file) if audio_file else None
                    thumbnail_path = os.path.join("covers", thumbnail) if thumbnail else None

                    with col:
                        if st.button(f"▶️ {title}", key=f"play_{song_id}"):
                            st.session_state.selected_song_id = song_id

                        if thumbnail_path and os.path.exists(thumbnail_path):
                            st.image(thumbnail_path, width=150)
                        else:
                            st.image("https://via.placeholder.com/150x150.png?text=No+Cover", width=150)

                        if st.session_state.selected_song_id == song_id:
                            if audio_path and os.path.exists(audio_path):
                                with open(audio_path, "rb") as f:
                                    audio_bytes = f.read()
                                    st.audio(audio_bytes, format="audio/mp3")

                            else:
                                st.warning("Audio file not found.")

    elif page == "Playlists":
        st.title("📂 Your Playlists")

        # Create new playlist
        new_playlist_name = st.text_input("Create a New Playlist")
        if st.button("Create Playlist"):
            if new_playlist_name.strip() == "":
                st.error("❌ Playlist name cannot be empty.")
            elif db.playlist_exists(st.session_state["user_id"], new_playlist_name):
                st.error("❌ A playlist with this name already exists.")
            else:
                if db.create_playlist(st.session_state["user_id"], new_playlist_name):
                    st.success(f"✅ Playlist '{new_playlist_name}' Created!")
                    st.rerun()
                else:
                    st.error("❌ Failed to Create Playlist")

        # Display user's playlists
        user_playlists = db.get_user_playlists(st.session_state["user_id"])
        if user_playlists:
            all_songs = db.get_all_song_titles()
            song_titles = [song['Title'] for song in all_songs]

            for playlist in user_playlists:
                st.subheader(playlist["name"])
                selected_song = st.selectbox(
                    f"Search & Add Song to '{playlist['name']}'",
                    song_titles,
                    key=f"select_{playlist['playlistId']}"
                )

                if st.button(f"Add '{selected_song}' to {playlist['name']}", key=f"add_{playlist['playlistId']}"):
                    song_id = db.get_song_id_by_title(selected_song)
                    if song_id and db.add_song_to_playlist(playlist["playlistId"], song_id):
                        st.success("✅ Song Added to Playlist!")
                    else:
                        st.error("❌ Failed to Add Song")
        else:
            st.info("You have no playlists. Create one above.")

    elif page == "Logout":
        st.session_state["user_id"] = None
        st.rerun()
