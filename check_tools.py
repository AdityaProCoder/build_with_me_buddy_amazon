# check_tools.py (The Simplest Possible Version)
import os
from dotenv import load_dotenv
from composio import Composio

print("--- Listing all available Composio Tools for your account ---")
load_dotenv()

if not os.getenv('COMPOSIO_API_KEY'):
    print("FATAL ERROR: API key not found in .env file.")
else:
    print("API key loaded. Instantiating Composio and fetching tools...")
    try:
        composio_instance = Composio()

        # --- THIS IS THE FINAL ATTEMPT ---
        # Calling the function with NO arguments, as per the last error.
        available_tools = composio_instance.tools.get_raw_composio_tools()

        print("\n" + "=" * 50)
        print("      YOUR AVAILABLE COMPOSIO TOOLS")
        print("=" * 50)

        if not available_tools:
            print("No tools found. Please check your Composio account connections.")
        else:
            print("You can use any of the following tool names in your project files:")
            for tool in available_tools:
                print(f"- {tool['slug']}")

        print("\n" + "=" * 50)

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")