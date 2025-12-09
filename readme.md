# Spotify Daily Logger

A Python script that logs your Spotify listening history to Google Sheets. Run it anytime to capture all tracks you've listened to today.

## Features

- Fetches ALL tracks played today (limited to last 50)
- Logs to Google Sheets automatically
- Avoids duplicates
- Includes track name, artist, album, duration, genres, and timestamp
- Run on-demand - no need to keep it running 24/7

## Prerequisites

- Python 3.7 or higher
- A Spotify account
- A Google account

## Installation

### 1. Install Required Packages

```bash
pip install spotipy gspread google-auth
```

### 2. Set Up Spotify API Credentials

#### Step 1: Create a Spotify App
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create app"**
4. Fill in the form:
   - **App name**: `Spotify Logger` (or any name you want)
   - **App description**: `Personal listening history logger`
   - **Redirect URI**: `http://127.0.0.1:8888/callback`
   - Check the box for **"I understand and agree..."**
5. Click **"Save"**

#### Step 2: Get Your Credentials
1. On your app's dashboard, click **"Settings"**
2. You'll see:
   - **Client ID** - Copy this
   - **Client Secret** - Click "View client secret" and copy it
3. Open `logger.py` and replace:
   ```python
   SPOTIPY_CLIENT_ID = 'your_client_id_here'
   SPOTIPY_CLIENT_SECRET = 'your_client_secret_here'
   ```

### 3. Set Up Google Sheets API Credentials

#### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top (or create account if new)
3. Click **"New Project"**
4. Enter project name: `Spotify Logger`
5. Click **"Create"**

#### Step 2: Enable Required APIs
1. In the left sidebar, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it and click **"Enable"**
4. Go back to the Library
5. Search for **"Google Drive API"**
6. Click on it and click **"Enable"**

#### Step 3: Create a Service Account
1. In the left sidebar, go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in:
   - **Service account name**: `spotify-logger`
   - **Service account ID**: (auto-generated)
4. Click **"Create and Continue"**
5. Skip the optional steps - click **"Continue"** → **"Done"**

#### Step 4: Create JSON Key
1. On the Credentials page, find your service account in the list
2. Click on the service account email
3. Go to the **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Choose **"JSON"** format
6. Click **"Create"**
7. A JSON file will download automatically
8. Rename it to `logger.json` and move it to your project folder (same folder as `logger.py`)

#### Step 5: Get Service Account Email
1. Open the `logger.json` file you just downloaded
2. Find the line with `"client_email"` - it looks like:
   ```json
   "client_email": "spotify-logger@your-project.iam.gserviceaccount.com"
   ```
3. Copy this email address (you'll need it in the next step)

### 4. Create and Share Google Sheet

#### Step 1: Create the Sheet
1. Go to [Google Sheets](https://sheets.google.com)
2. Click the **"+"** button or **"Blank"** to create a new spreadsheet
3. Click on "Untitled spreadsheet" at the top
4. Rename it to: **`Spotify Listening History`** (exact name is important!)

#### Step 2: Share with Service Account
1. Click the **"Share"** button (top right corner)
2. In the "Add people and groups" field, paste your service account email from Step 5 above
3. Make sure the role is set to **"Editor"**
4. **Uncheck** "Notify people" (service accounts can't read emails)
5. Click **"Share"** or **"Send"**

## Usage

### Run the Logger

Simply run the script whenever you want to log today's listening history:

```bash
python logger.py
```

The script will:
1. Connect to your Spotify account (first time will open a browser for authorization)
2. Fetch all tracks you've played today
3. Log them to your Google Sheet
4. Show you what was logged

### When to Run

You can run this script:
- Once at the end of each day
- Multiple times throughout the day (it won't create duplicates)
- Whenever you want to update your listening history

### First Time Setup

The first time you run the script, it will:
1. Open your browser asking you to authorize the Spotify app
2. After authorizing, it will redirect to a localhost URL
3. Copy the **entire URL** from your browser and paste it back in the terminal
4. The script will save the authorization for future runs

## Output Example

```
============================================================
SPOTIFY DAILY LOGGER
============================================================
Date: 2025-12-05 14:30:00
============================================================
Connected to spreadsheet: 'Spotify Listening History'

Fetching your listening history for today...
   Current time (UTC): 2024-12-05 14:30:00
   Start of day (UTC): 2024-12-05 00:00:00

   Fetching from Spotify API...
   Batch 1: Got 50 tracks

   Total tracks from API: 50
   Tracks from today: 50
   Time range: 08:15 - 14:25

   Already logged: 30 entries in sheet

Logging 20 new tracks...
Successfully logged 20 tracks

Recent tracks logged:
   14:20 - Song Name by Artist Name
   14:15 - Another Song by Another Artist
   ...

============================================================
Done! Run this script anytime to update today's tracks.
============================================================
```

## Google Sheet Structure

The script creates the following columns:

| Played At | Track Name | Artist(s) | Album | Duration (ms) | Track ID | Genres |
|-----------|-----------|----------|-------|---------------|----------|---------|
| 2024-12-05T14:20:30.000Z | Song Name | Artist Name | Album Name | 210000 | track_id_123 | pop, rock |

## Troubleshooting

### "Spreadsheet not found"
- Make sure the sheet is named exactly: `Spotify Listening History`
- Verify you shared it with the service account email

### "Drive storage quota exceeded"
- This means the service account can't create files
- Create the sheet manually and share it with the service account

### "No tracks found for today"
- Make sure you've listened to music for at least 30 seconds per track
- Spotify only logs tracks that were played for 30+ seconds
- Wait 2-3 minutes after listening for Spotify to update

### Authentication issues
- Delete the `.cache` file in your project folder and run again
- Make sure your redirect URI in Spotify Dashboard is: `http://127.0.0.1:8888/callback`

## Security Notes

- Never share your `logger.json` file (it contains sensitive credentials)
- Never commit `logger.json` to version control
- Add `logger.json` and `.cache` to your `.gitignore` file

## File Structure

```
your-project-folder/
├── logger.py           # Main script
├── logger.json         # Google credentials (don't commit!)
├── .cache             # Spotify auth cache (auto-generated, don't commit!)
└── README.md          # This file
```

## License

This project is for personal use. Spotify and Google APIs are subject to their respective terms of service.