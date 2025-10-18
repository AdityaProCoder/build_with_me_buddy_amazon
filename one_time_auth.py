# one_time_auth.py - Run this script ONCE to authorize Notion for your developer user.
import os
from dotenv import load_dotenv
from composio import Composio
import json

print("--- Reusable Authentication Setup for Notion ---")

# --- Configuration ---
# These are now read from your .env file
load_dotenv()
NOTION_AUTH_CONFIG_ID = os.getenv("NOTION_AUTH_CONFIG_ID")

# This is a consistent, hardcoded ID for your developer identity.
MY_APP_USER_ID = "build-with-me-buddy-developer-001"

# ---------------------

if not os.getenv("COMPOSIO_API_KEY") or not NOTION_AUTH_CONFIG_ID:
    print("\n[ERROR] Make sure COMPOSIO_API_KEY and NOTION_AUTH_CONFIG_ID are in your .env file.")
    exit()

try:
    composio_instance = Composio()
    print(f"\nChecking for existing Notion connection for user: {MY_APP_USER_ID}...")

    try:
        # Try to find an existing connection
        composio_instance.connected_accounts.get_by_user_id(
            user_id=MY_APP_USER_ID,
            auth_config_id=NOTION_AUTH_CONFIG_ID
        )
        print("✅ Existing connection found! You are all set.")
    except Exception:
        # If no connection is found, start the one-time interactive flow
        print("No existing connection found. Initiating one-time authentication...")
        connection_request = composio_instance.connected_accounts.initiate(
            user_id=MY_APP_USER_ID,
            auth_config_id=NOTION_AUTH_CONFIG_ID,
        )
        print("\n" + "=" * 60)
        print("   >>> ONE-TIME ACTION REQUIRED <<<")
        print("Click the link below to authorize Notion. After you approve, the script will continue.")
        print(f"Visit this URL to authenticate: {connection_request.redirect_url}")
        print("=" * 60)
        connection_request.wait_for_connection(timeout=120)
        print("\n✅ Authentication successful! Your connection is now stored for this user.")

except Exception as e:
    print(f"\n--- ❌ FAILED ---")
    print(f"An error occurred: {e}")