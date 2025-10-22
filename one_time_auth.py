# one_time_auth.py

# Standard library imports
import os # Provides functions for interacting with the operating system, like accessing environment variables.
import json # For working with JSON data (though not directly used in the provided snippet, often used with API responses).

# Third-party library imports
from dotenv import load_dotenv # Used to load environment variables from a .env file.
from composio import Composio # Imports the Composio client for interacting with external tools and services.

# --- Script Initialization ---

print("--- Reusable Authentication Setup for Notion ---")

# Load environment variables from the .env file.
load_dotenv()
# Retrieve the Notion authentication configuration ID from environment variables.
NOTION_AUTH_CONFIG_ID = os.getenv("NOTION_AUTH_CONFIG_ID")

# Define a unique user ID for the application to interact with Composio.
MY_APP_USER_ID = "build-with-me-buddy-developer-001"

# Check if essential environment variables are set.
if not os.getenv("COMPOSIO_API_KEY") or not NOTION_AUTH_CONFIG_ID:
    print("\n[ERROR] Make sure COMPOSIO_API_KEY and NOTION_AUTH_CONFIG_ID are in your .env file.")
    exit() # Exit the script if required environment variables are missing.

# --- Composio Authentication Flow ---

try:
    # Initialize the Composio client.
    composio_instance = Composio()
    print(f"\nChecking for existing Notion connection for user: {MY_APP_USER_ID}...")

    try:
        # Attempt to retrieve an existing Notion connection for the specified user and config.
        composio_instance.connected_accounts.get_by_user_id(
            user_id=MY_APP_USER_ID,
            auth_config_id=NOTION_AUTH_CONFIG_ID
        )
        print("✅ Existing connection found! You are all set.")
    except Exception:
        # If no existing connection is found, initiate a new one-time authentication.
        print("No existing connection found. Initiating one-time authentication...")
        connection_request = composio_instance.connected_accounts.initiate(
            user_id=MY_APP_USER_ID,
            auth_config_id=NOTION_AUTH_CONFIG_ID,
        )
        # Provide instructions to the user for manual authentication.
        print("\n" + "=" * 60)
        print("   >>> ONE-TIME ACTION REQUIRED <<<")
        print("Click the link below to authorize Notion. After you approve, the script will continue.")
        print(f"Visit this URL to authenticate: {connection_request.redirect_url}")
        print("=" * 60)
        # Wait for the user to complete the authentication process (with a timeout).
        connection_request.wait_for_connection(timeout=120)
        print("\n✅ Authentication successful! Your connection is now stored for this user.")

except Exception as e:
    # Handle any exceptions that occur during the authentication process.
    print(f"\n--- ❌ FAILED ---")
    print(f"An error occurred: {e}")
