"""
Run this script locally to get your Spotify refresh token.
You only need to run this once, then add the tokens to Render environment variables.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'
SCOPE = 'user-read-recently-played'

print("=" * 60)
print("SPOTIFY TOKEN GENERATOR")
print("=" * 60)
print()
print("This will authenticate with Spotify and get your tokens.")
print("You'll need to add these tokens to your Render environment variables.")
print()

# Authenticate
sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE,
    cache_path='.cache-token-generator'
)

# Get the authorization URL
auth_url = sp_oauth.get_authorize_url()
print("1. Go to this URL in your browser:")
print(f"   {auth_url}")
print()
print("2. After authorizing, you'll be redirected to a URL like:")
print("   http://127.0.0.1:8888/callback?code=...")
print()

# Get the code from user
response_url = input("3. Paste the entire redirect URL here: ").strip()

# Extract the code and get tokens
code = sp_oauth.parse_response_code(response_url)
token_info = sp_oauth.get_access_token(code, as_dict=True)

print()
print("=" * 60)
print("SUCCESS! Here are your tokens:")
print("=" * 60)
print()
print("Add these to your Render environment variables:")
print()
print("1. SPOTIFY_REFRESH_TOKEN")
print(f"   Value: {token_info['refresh_token']}")
print()
print("2. SPOTIFY_ACCESS_TOKEN (optional, will be refreshed automatically)")
print(f"   Value: {token_info['access_token']}")
print()
print("=" * 60)
print()
print("IMPORTANT: Keep these tokens secret!")
print("Add them to Render and NEVER commit them to Git.")
print()

# Save to a file for reference (add to .gitignore!)
with open('spotify_tokens.txt', 'w') as f:
    f.write(f"SPOTIFY_REFRESH_TOKEN={token_info['refresh_token']}\n")
    f.write(f"SPOTIFY_ACCESS_TOKEN={token_info['access_token']}\n")
    f.write(f"\nExpires at: {token_info.get('expires_at', 'Unknown')}\n")

print("✓ Tokens also saved to 'spotify_tokens.txt'")
print("  (Make sure this file is in .gitignore!)")
print()

# Clean up cache
if os.path.exists('.cache-token-generator'):
    os.remove('.cache-token-generator')