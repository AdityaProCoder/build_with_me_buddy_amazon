# test_full_notion_flow.py
import os
from dotenv import load_dotenv
from composio import Composio
import json
import uuid

print("--- Full End-to-End Test for Notion: Authenticate, Create, and Populate ---")

# --- Configuration ---
# Your .env file must contain COMPOSIO_API_KEY, NOTION_PARENT_PAGE_ID, and NOTION_AUTH_CONFIG_ID
# ---------------------

MY_APP_USER_ID = "build-with-me-buddy-developer-002"

# 1. Load Environment Variables
print("Loading environment variables...")
load_dotenv()
if not all(os.getenv(key) for key in ["COMPOSIO_API_KEY", "NOTION_PARENT_PAGE_ID", "NOTION_AUTH_CONFIG_ID"]):
    print("\n[ERROR] Make sure COMPOSIO_API_KEY, NOTION_PARENT_PAGE_ID, and NOTION_AUTH_CONFIG_ID are all set in your .env file.")
    exit()

NOTION_AUTH_CONFIG_ID = os.getenv("NOTION_AUTH_CONFIG_ID")
print("API Key and All Notion IDs loaded successfully.")

try:
    # 2. Instantiate Composio
    print("\nInstantiating Composio client...")
    composio_instance = Composio()
    print("Composio client created.")

    # 3. --- Reusable Authentication Flow ---
    print(f"\nStep A: Checking for existing Notion connection for user: {MY_APP_USER_ID}...")
    try:
        composio_instance.connected_accounts.get_by_user_id(user_id=MY_APP_USER_ID, auth_config_id=NOTION_AUTH_CONFIG_ID)
        print("✅ Existing connection found! No need to re-authenticate.")
    except Exception:
        print("No existing connection found. Initiating one-time authentication...")
        connection_request = composio_instance.connected_accounts.initiate(user_id=MY_APP_USER_ID, auth_config_id=NOTION_AUTH_CONFIG_ID)
        print("\n" + "="*60)
        print("   >>> ONE-TIME ACTION REQUIRED <<<")
        print("1. Click the link below to authorize Notion in your browser.")
        print("2. After you approve, the script will automatically continue.")
        print(f"Visit this URL to authenticate: {connection_request.redirect_url}")
        print("="*60)
        connection_request.wait_for_connection(timeout=120)
        print("\n✅ Authentication successful! Connection is now stored for this user.")

    # 4. --- Step B: Create a New, Blank Page ---
    tool_slug_create = "NOTION_CREATE_NOTION_PAGE"
    new_page_title = "Full Flow Test - FINAL SUCCESS"
    
    print(f"\nStep B: Preparing to execute tool: '{tool_slug_create}' to create a blank page...")
    
    create_result = composio_instance.tools.execute(
        user_id=MY_APP_USER_ID,
        slug=tool_slug_create,
        arguments={"parent_id": os.getenv("NOTION_PARENT_PAGE_ID"), "title": new_page_title}
    )
    if not create_result.get("successful"): raise Exception(f"Failed to create the page: {create_result.get('error')}")

    new_page_id = create_result['data']['id']
    new_page_url = create_result['data']['url']
    print(f"✅ Blank page created successfully with ID: {new_page_id}")

    # 5. --- Step C: Add Content to the New Page ---
    tool_slug_add = "NOTION_ADD_MULTIPLE_PAGE_CONTENT"
    test_content = "## Test Complete!\n\nThis content was successfully added. The full workflow is working."
    
    # --- THIS IS THE DEFINITIVE FIX ---
    # The content dictionary MUST be wrapped in a 'content_block' key, as the error message stated.
    content_arguments = {
        "parent_block_id": new_page_id,
        "content_blocks": [
            {
                "content_block": {
                    "content": test_content
                }
            }
        ]
    }
    
    print(f"\nStep C: Preparing to execute tool: '{tool_slug_add}' to add content...")

    add_content_result = composio_instance.tools.execute(
        user_id=MY_APP_USER_ID,
        slug=tool_slug_add,
        arguments=content_arguments
    )
    if not add_content_result.get("successful"):
        raise Exception(f"Failed to add content to the new page: {add_content_result.get('error')}")
    
    # 6. Final Success
    print("\n--- ✅ FULL TEST SUCCEEDED! ---")
    print("Successfully authenticated, created a page, and ADDED CONTENT to it.")
    print(f"\nView your new, populated page here: {new_page_url}")

except Exception as e:
    print("\n--- ❌ TEST FAILED ---")
    print(f"An error occurred: {e}")