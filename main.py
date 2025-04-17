import streamlit as st
import os
import db
import qrcode
from io import BytesIO

AUDIO_DIR = os.path.join(os.getcwd(), "songs")
COVER_DIR = os.path.join(os.getcwd(), "covers")
st.set_page_config(page_title="Treble", layout="wide")

# Theme setup
if "theme" not in st.session_state:
    st.session_state["theme"] = "Dark"

theme = st.sidebar.radio("🎨 Theme", ["Dark", "Light"], index=0 if st.session_state["theme"] == "Dark" else 1)
st.session_state["theme"] = theme


def apply_theme(theme):
    if theme == "Dark":
        st.markdown(
            """
            <style>
                .stApp {
                    background-color: #121212;
                    color: #ffffff;
                    padding: 2rem;
                }
                .stButton>button {
                    font-weight: bold;
                    background-color: #5c5c5c;
                    color: white;
                }
                .stTextInput>div>div>input {
                    background-color: #2d2d2d;
                    color: white;
                }
                .stSelectbox>div>div>select {
                    background-color: #2d2d2d;
                    color: white;
                }
                .stRadio>div {
                    background-color: #2d2d2d;
                    padding: 10px;
                    border-radius: 5px;
                }
                .css-1adrfps {
                    background-color: #2d2d2d;
                }
                /* Sidebar styles */
                .css-1d391kg, .css-12oz5g7 {
                    background-color: #1e1e1e;
                }
                /* Headers */
                h1, h2, h3, h4, h5, h6 {
                    color: #ffffff !important;
                }
            </style>
            """, unsafe_allow_html=True
        )
    else:  # Light theme
        st.markdown(
            """
            <style>
                .stApp {
                    background-color: #ffffff;
                    color: #000000;
                    padding: 2rem;
                }
                .stButton>button {
                    font-weight: bold;
                    background-color: #f0f2f6;
                    color: black;
                }
                /* Headers */
                h1, h2, h3, h4, h5, h6 {
                    color: #000000 !important;
                }
            </style>
            """, unsafe_allow_html=True
        )


apply_theme(theme)

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None


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
        elif not db.validate_password(password):
            st.error("❌ Password must be 8+ characters with at least one number and special character.")
        else:
            if db.signup_user(name, password, subscription_type):
                user_id = db.login_user(name, password)
                st.session_state["user_id"] = user_id
                st.success("✅ Signed up and logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Sign Up Failed. Try again.")


# MAIN APP
if st.session_state["user_id"] is None:
    st.radio("Select an option", ["Login", "Sign Up"], key="auth_mode")
    if st.session_state["auth_mode"] == "Login":
        login()
    else:
        signup()

else:
    st.sidebar.title("🎶 Treble")
    page = st.sidebar.radio("Go to", ["Home", "Browse", "Playlists", "Profile", "Logout"])

    if page == "Home":
        st.title("🎧 Welcome to Treble")
        user_name = db.get_user_name(st.session_state["user_id"])
        st.markdown(f"## Hello, **{user_name}** 👋")

        st.subheader("🔥 Trending Songs")
        trending = db.get_top_songs(limit=12)  # Fetch enough songs for multiple rows

        # Display songs in a grid (3 songs per row)
        cols_per_row = 3
        rows = [trending[i:i + cols_per_row] for i in range(0, len(trending), cols_per_row)]

        for row in rows:
            cols = st.columns(cols_per_row)
            for col, song in zip(cols, row):
                with col:
                    st.markdown(f"**{song['Title']}**")

                    # Display thumbnail
                    thumbnail = song.get("thumbnail")
                    if thumbnail:
                        thumbnail_path = os.path.join("covers", thumbnail)
                        if os.path.exists(thumbnail_path):
                            st.image(thumbnail_path, width=150)
                        else:
                            st.image("https://via.placeholder.com/150x150.png?text=No+Cover", width=150)
                    else:
                        st.image("https://via.placeholder.com/150x150.png?text=No+Cover", width=150)

                    # Add audio playback
                    audio_file = song.get("audioFile")
                    if audio_file:
                        audio_path = os.path.join("songs", audio_file)
                        if os.path.exists(audio_path):
                            with open(audio_path, "rb") as f:
                                audio_bytes = f.read()
                                st.audio(audio_bytes, format="audio/mp3")
                        else:
                            st.warning("Audio file not found.")
                    else:
                        st.info("No audio file available for this song.")

        st.subheader("🆕 New Releases")
        recent = db.get_recent_songs(limit=5)
        for song in recent:
            st.markdown(f"🗓️ {song['Title']} — Released on {song['releaseDate']}")

        st.subheader("🎶 Genres")
        genres = db.get_all_genres()
        st.write(", ".join([g['genreName'] for g in genres]))

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

    elif page == "Profile":
        st.title("👤 Profile Settings")
        info = db.get_user_profile(st.session_state["user_id"])
        st.write(f"**Username**: {info['name']}")
        st.write(f"**Subscription**: {info['subscription_type']}")
        st.write(f"**Joined**: {info['date_joined']}")

        # Subscription tab with payment option
        st.subheader("💳 Subscription")

        if info['subscription_type'] == "Premium":
            st.success("You are currently on a Premium subscription!")
            if st.button("Cancel Premium"):
                if db.update_subscription(st.session_state["user_id"], "Free"):
                    st.success("Subscription downgraded to Free.")
                    st.rerun()
                else:
                    st.error("Failed to update subscription.")
        else:
            st.info("You are currently on a Free subscription.")
            if st.button("Upgrade to Premium"):
                st.session_state["show_payment"] = True

        # Show payment QR code
        if st.session_state.get("show_payment", False):
            st.subheader("📱 Payment")

            col1, col2 = st.columns([1, 1])

            with col1:
                # Create QR code for payment
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data("mellows:premium:payment:12.99:usd")
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")

                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_bytes = buffered.getvalue()

                st.image(img_bytes, caption="Scan to Pay $12.99/month", width=250)

            with col2:
                st.markdown("""
                ### Premium Benefits:
                - 🎵 **Ad-free listening**
                - 📱 **Offline downloads**
                - 🔊 **Higher audio quality**
                - 🎧 **Unlimited skips**

                **Price**: $12.99/month
                """)

                payment_id = st.text_input("Enter Payment Confirmation ID (received after payment)")

                if st.button("Confirm Payment"):
                    if payment_id.strip():
                        if db.update_subscription(st.session_state["user_id"], "Premium"):
                            st.success("Payment verified! Subscription upgraded to Premium.")
                            st.session_state["show_payment"] = False
                            st.rerun()
                        else:
                            st.error("Failed to update subscription.")
                    else:
                        st.warning("Please enter the confirmation ID.")

            if st.button("Cancel Payment"):
                st.session_state["show_payment"] = False
                st.rerun()

        st.subheader("🔒 Change Password")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            if db.validate_password(new_pass):
                db.change_password(st.session_state["user_id"], new_pass)
                st.success("Password updated!")
            else:
                st.error("❌ Must be 8+ chars, include number & special char.")

        st.subheader("⚙️ Account Settings")
        if st.button("Delete Account", type="primary", help="Warning: This action cannot be undone"):
            st.warning("Are you sure you want to delete your account? This cannot be undone.")
            confirm = st.button("Yes, Delete My Account")
            if confirm:
                if db.delete_user(st.session_state["user_id"]):
                    st.success("Account deleted successfully.")
                    st.session_state["user_id"] = None
                    st.rerun()
                else:
                    st.error("Failed to delete account.")

    elif page == "Logout":
        if st.button("Confirm Logout"):
            st.session_state["user_id"] = None
            st.rerun()
        else:
            st.warning("Are you sure you want to logout?")
