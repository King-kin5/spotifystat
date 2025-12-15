import spotipy
from spotipy.oauth2 import SpotifyOAuth
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
import time
import os
import sys
import io
from dotenv import load_dotenv

# Fix Unicode encoding issues on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

# Spotify API Configuration 
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')
SCOPE = 'user-read-recently-played'

# Google Sheets Configuration 
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'logger.json')
SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'Spotify Listening History')

def setup_spotify():
    """Initialize Spotify client with authentication"""
    if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
        raise ValueError("Missing Spotify credentials! Please check your .env file.")
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE
    ))
    return sp

def setup_google_sheets():
    """Initialize Google Sheets client"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE, 
        scopes=scopes
    )
    client = gspread.authorize(creds)
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.sheet1
        headers = worksheet.row_values(1)
        if not headers or headers[0] != 'Played At':
            worksheet.insert_row([
                'Played At', 'Track Name', 'Artist(s)', 
                'Album', 'Duration (ms)', 'Track ID', 'Genres'
            ], index=1)
            print("[OK] Headers added to spreadsheet")
        print(f"[OK] Connected to spreadsheet: '{SPREADSHEET_NAME}'")
        return worksheet
    except gspread.SpreadsheetNotFound:
        print(f"\n[ERROR] Spreadsheet '{SPREADSHEET_NAME}' not found!")
        print("\nPlease create the spreadsheet manually:")
        print("1. Go to https://sheets.google.com")
        print(f"2. Create a new blank spreadsheet")
        print(f"3. Rename it to: '{SPREADSHEET_NAME}'")
        print(f"4. Click 'Share' and add this email as Editor:")
        import json
        with open(GOOGLE_CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
            print(f"   {creds_data['client_email']}")
        print("\n5. Run this script again!\n")
        exit(1)

def get_artist_genres(sp, artist_id):
    """Get genres for an artist"""
    try:
        artist = sp.artist(artist_id)
        return ', '.join(artist['genres']) if artist['genres'] else 'Unknown'
    except Exception as e:
        print(f"Error fetching genres: {e}")
        return 'Unknown'

def get_recently_played(sp, worksheet):
    """Fetch recently played tracks and log to Google Sheets"""
    try:
        # Get today's date at midnight (start of day)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        results = sp.current_user_recently_played(limit=50)
        print(f"   Found {len(results['items'])} tracks from Spotify API")
        print(f"   Tracking only tracks played from: {today_start.strftime('%Y-%m-%d %H:%M:%S')}")
        if results['items']:
            print("\n   === DEBUG: Recent tracks from Spotify ===")
            for i, item in enumerate(results['items'][:5]):
                track = item['track']
                played_at = item['played_at']
                print(f"   {i+1}. '{track['name']}' by {track['artists'][0]['name']}")
                print(f"      Played at: {played_at}")
            print("   ==========================================\n")
        existing_data = worksheet.get_all_values()[1:]  
        existing_entries = set()
        print("   === DEBUG: Last entries in Google Sheet ===")
        for row in existing_data[-3:]:
            if len(row) >= 2:
                print(f"   '{row[1]}' at {row[0]}")
        print("   ==========================================\n")
        for row in existing_data:
            if len(row) >= 6:
                existing_entries.add(f"{row[0]}_{row[5]}")
        print(f"   Already logged: {len(existing_entries)} entries in sheet")
        new_tracks = []
        skipped_tracks = []
        old_tracks = [] 
        for item in reversed(results['items']):
            track = item['track']
            played_at = item['played_at']
            played_at_dt = datetime.fromisoformat(played_at.replace('Z', '+00:00'))
            # Skip tracks played before today
            if played_at_dt < today_start.replace(tzinfo=timezone.utc):
                old_tracks.append(f"{track['name']} at {played_at}")
                continue
            entry_key = f"{played_at}_{track['id']}"
            if entry_key in existing_entries:
                skipped_tracks.append(f"{track['name']} at {played_at}")
                continue
            artists = ', '.join([artist['name'] for artist in track['artists']])
            artist_id = track['artists'][0]['id'] if track['artists'] else None
            # Get genres (only for first artist to minimize API calls)
            genres = get_artist_genres(sp, artist_id) if artist_id else 'Unknown'
            row_data = [
                played_at,
                track['name'],
                artists,
                track['album']['name'],
                track['duration_ms'],
                track['id'],
                genres
            ]
            
            new_tracks.append(row_data)
        if old_tracks:
            print(f"\n   === Skipped {len(old_tracks)} tracks from before today ===")
            for old in old_tracks[:3]:
                print(f"   - {old}")
            if len(old_tracks) > 3:
                print(f"   ... and {len(old_tracks) - 3} more")
            print("   ==========================================\n")
        if skipped_tracks:
            print(f"\n   === DEBUG: Skipped {len(skipped_tracks)} duplicate tracks ===")
            for skip in skipped_tracks[:3]:
                print(f"   - {skip}")
            if len(skipped_tracks) > 3:
                print(f"   ... and {len(skipped_tracks) - 3} more")
            print("   ==========================================\n")
        if new_tracks:
            worksheet.append_rows(new_tracks)
            print(f"[OK] Logged {len(new_tracks)} new tracks")
            print("   New tracks added:")
            for track in new_tracks:
                print(f"   - {track[1]} at {track[0]}")
        else:
            print("[OK] No new tracks to log (all already in sheet)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def run_logger(interval_minutes=10):
    """Run the logger continuously"""
    print("Initializing Spotify Logger...")
    sp = setup_spotify()
    worksheet = setup_google_sheets()
    print(f"Logger started! Checking every {interval_minutes} minutes.")
    print("Press Ctrl+C to stop.\n")
    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] Checking for new tracks...")
            get_recently_played(sp, worksheet)
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\nLogger stopped by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            print("Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == "__main__":
    # Run once to test
    print("Initializing Spotify Logger...")
    sp = setup_spotify()
    worksheet = setup_google_sheets()
    print("Checking for new tracks...")
    get_recently_played(sp, worksheet)
    print("Script finished.")