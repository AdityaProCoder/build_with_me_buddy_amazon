# check_tools.py (Final Working Version)
import os
from dotenv import load_dotenv
from composio import Composio

print("--- Listing all available Composio Tools ---")
load_dotenv()

if not os.getenv('COMPOSIO_API_KEY'):
    print("FATAL ERROR: API key not found in .env file.")
else:
    print("API key loaded. Instantiating Composio and fetching tools...")
    try:
        composio_instance = Composio()

        # --- THIS IS THE CORRECT METHOD ---
        # Calling .tools.get() with no arguments lists all available tools.
        available_tools = composio_instance.tools.get()

        print("\n" + "=" * 50)
        print("      AVAILABLE COMPOSIO TOOLS")
        print("=" * 50)

        if not available_tools:
            print("No tools found. Please check your authentication.")
        else:
            print("You can use any of the following tool names in your agents.yaml file:")
            # The tool name is stored in the .slug attribute of each tool object
            for tool in available_tools:
                print(f"- {tool.slug}")

        print("\n" + "=" * 50)
        print("Example: 'google-search.search_the_web'")
        print("=" * 50)

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")