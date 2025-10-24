# app.py

# Standard library imports
from dotenv import load_dotenv # Used to load environment variables from a .env file.
import os # Provides functions for interacting with the operating system.
import re # Regular expression operations, used for parsing text.

# Determine the project root directory and the path to the .env file.
project_root = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(project_root, '.env')

# Load environment variables from the .env file if it exists.
if os.path.exists(dotenv_path):
    print(f"✅ Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("⚠️ .env file not found. Please ensure it exists in the project root.")

# Third-party library imports
from flask import Flask, render_template, request, jsonify, session # Flask framework components for web application.
import time # Provides time-related functions (though not directly used in the provided snippets).
import json # For working with JSON data.

# Local application imports
from src.crew import ProjectPartnerCrew # Imports the main crew management class.
from src.tools.composio_tools import composio_instance, MY_APP_USER_ID # Imports Composio tools for external integrations (e.g., Notion).

# Define a constant for the checkpoint file, used to save/resume task progress.
CHECKPOINT_FILE = "task_progress.json"

# --- Flask Application Setup ---

# Initialize the Flask application.
app = Flask(__name__)
# Configure a secret key for session management, essential for security.
app.config['SECRET_KEY'] = os.urandom(24)

# --- Routes ---

@app.route('/')
def index():
    """
    Renders the main index page of the application.
    This is typically the entry point for the user interface.
    """
    return render_template('index.html')

@app.route('/kickoff_crew', methods=['POST'])
def kickoff_crew_endpoint():
    """
    API endpoint to initiate the project planning stage.
    It receives project details from the frontend, kicks off the planning crew,
    and stores the plan in the session.
    """
    # Remove any existing checkpoint file to start a fresh process.
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    # Get project details from the incoming JSON request.
    data = request.get_json()
    project_details = data.get('project_details')
    # Validate if project details are provided.
    if not project_details: return jsonify({"error": "Project details are required."}), 400

    print(f"🚀 Stage 1: Planning for -> {project_details}")
    try:
        # Initialize the crew manager and run the planning crew.
        crew_manager = ProjectPartnerCrew()
        result = crew_manager.planning_crew().kickoff(inputs={'project_details': project_details})

        # Store the project plan and details in the Flask session.
        session['project_plan'] = result.raw
        session['project_details'] = project_details

        print(f"✅ Stage 1 Finished.")
        # Return the planning result and a prompt for the next stage.
        return jsonify({
            "result": result.raw,
            "prompt": "Enter 'Proceed' to generate the Bill of Materials."
        })
    except Exception as e:
        # Handle any errors during Stage 1.
        return jsonify({"error": "Error in Stage 1", "details": str(e)}), 500

@app.route('/generate_bom', methods=['POST'])
def generate_bom_endpoint():
    """
    API endpoint to generate the Bill of Materials (BOM).
    This stage involves naming the project, designing a conceptual BOM,
    and sourcing final parts, potentially interacting with external tools like Notion.
    """
    # Retrieve necessary data from the session.
    project_plan = session.get('project_plan')
    project_details = session.get('project_details')
    # Validate if session data is present.
    if not project_plan or not project_details: return jsonify({"error": "Session data missing."}), 400

    print(f"🚀 Stage 2: Generating BOM content for -> {project_details}")
    try:
        crew_manager = ProjectPartnerCrew()

        # Check for a checkpoint file to resume progress if available.
        # This condition checks if the checkpoint file does NOT exist, indicating a fresh start or a point before a checkpoint was saved.
        if not os.path.exists(CHECKPOINT_FILE):
            print("🧠 Generating project name...")
            name_result = crew_manager.naming_crew().kickoff(inputs={'project_details': project_details})
            session['project_name'] = name_result.raw

            print("🧠 Designing conceptual BOM...")
            design_result = crew_manager.design_crew().kickoff(inputs={'project_plan': project_plan})
            session['conceptual_bom_table'] = design_result.raw
        else:
            print("Resuming from a saved checkpoint...")

        print("🧠 Sourcing final parts...")

        # Kick off the sourcing crew with the conceptual BOM.
        sourcing_inputs = {'final_bom': session['conceptual_bom_table']}
        sourcing_result = crew_manager.sourcing_crew().kickoff(inputs=sourcing_inputs)

        # Handle rate limit hits from external APIs.
        if "RATE_LIMIT_HIT" in sourcing_result.raw:
            print("🚨 Rate limit hit. Process paused. Progress has been saved by the agent.")
            return jsonify({
                "result": "I'm working on your component list, but I've hit a temporary API limit. Your progress is saved!",
                "prompt": "Please wait 60 seconds and then enter 'Proceed' again to continue from where I left off."
            })

        # Remove checkpoint file after successful sourcing.
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)

        full_bom_output = sourcing_result.raw

        # Ensure the output from the sourcing crew is in the expected format.
        if '---DATA_SEPARATOR---' not in full_bom_output:
            raise Exception(f"Sourcing crew failed to generate the correct output format. It returned: '{full_bom_output}'")

        # Split the output into user summary and final BOM table.
        user_summary, final_bom_table = full_bom_output.split('---DATA_SEPARATOR---')

        print("🤖 Python is now creating and populating the Notion pages...")
        project_name = session['project_name']

        # Create a main project page in Notion.
        project_page_result = composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE", arguments={"parent_id": os.getenv("NOTION_PARENT_PAGE_ID"), "title": project_name})
        if not project_page_result.get("successful"): raise Exception(f"Failed to create main project page: {project_page_result.get('error')}")

        # Store Notion page details in the session.
        project_page_id = project_page_result['data']['id']
        project_page_url = project_page_result['data']['url']
        session['project_page_id'] = project_page_id
        session['project_page_url'] = project_page_url

        # Create a "Conceptual BOM" page under the main project page and populate it.
        conceptual_page_result = composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE", arguments={"parent_id": project_page_id, "title": "Conceptual BOM"})
        if not conceptual_page_result.get("successful"): raise Exception(f"Failed to create Conceptual BOM page: {conceptual_page_result.get('error')}")
        composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_ADD_MULTIPLE_PAGE_CONTENT", arguments={"parent_block_id": conceptual_page_result['data']['id'], "content_blocks": [{"content_block": {"content": session['conceptual_bom_table']}}]})

        # Create a "Final Bill of Materials (BOM)" page and populate it.
        final_bom_page_result = composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE", arguments={"parent_id": project_page_id, "title": "Final Bill of Materials (BOM)"})
        if not final_bom_page_result.get("successful"): raise Exception(f"Failed to create Final BOM page: {final_bom_page_result.get('error')}")
        composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_ADD_MULTIPLE_PAGE_CONTENT", arguments={"parent_block_id": final_bom_page_result['data']['id'], "content_blocks": [{"content_block": {"content": final_bom_table}}]})

        print("✅ Notion pages created and populated successfully.")

        # Store final BOM data and prepare the output for the user.
        session['final_bom_data'] = final_bom_table.strip()
        final_output_for_user = user_summary.strip() + f"\n\n[View your full project folder on Notion]({project_page_url})"
        return jsonify({"result": final_output_for_user, "prompt": "Enter 'Proceed' to generate the final assets (code and diagram)."})

    except Exception as e:
        print(f"❌ Error during Stage 2: {e}")
        return jsonify({"error": "Error in Stage 2", "details": str(e)}), 500

@app.route('/generate_final_assets', methods=['POST'])
def generate_final_assets_endpoint():
    """
    API endpoint to generate final project assets, including diagrams and code.
    These assets are then uploaded to Notion.
    """
    # Retrieve necessary data from the session.
    final_bom_data = session.get('final_bom_data')
    project_page_id = session.get('project_page_id') # This is the ID of the main project FOLDER in Notion.
    project_plan = session.get('project_plan')
    # Validate if session data is present.
    if not all([final_bom_data, project_page_id, project_plan]):
        return jsonify({"error": "Session data missing."}), 400

    print(f"🚀 Stage 3: Generating final assets...")
    try:
        crew_manager = ProjectPartnerCrew()

        print("🧠 Generating all diagrams...")
        # Kick off the diagram generation crew.
        diagram_inputs = {'final_bom': final_bom_data, 'project_plan': project_plan}
        diagram_result = crew_manager.diagram_generation_crew().kickoff(inputs=diagram_inputs)
        diagram_json_output = diagram_result.raw

        print("🧠 Generating Arduino code...")
        # Kick off the code generation crew.
        code_inputs = {'final_bom': final_bom_data}
        code_result = crew_manager.code_generation_crew().kickoff(inputs=code_inputs)
        code_sketch = code_result.raw

        print("🤖 Python is now parsing and creating the final guide page...")

        def extract_json_block(text: str) -> dict:
            """
            Helper function to extract a JSON block from a given text.
            It looks for content enclosed in ```json ... ```.
            """
            match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
            if not match:
                try: return json.loads(text) # Try to load as JSON directly if no code block found.
                except json.JSONDecodeError: raise ValueError("Could not find a valid JSON block in diagram output.")
            return json.loads(match.group(1))

        def clean_code_block(text: str, language: str) -> str:
            """
            Helper function to extract and clean a code block from a given text.
            It looks for content enclosed in ```<language> ... ```.
            """
            match = re.search(rf"```{language}\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
            return match.group(1).strip() if match else text.strip()

        # Extract diagram data from the crew's output.
        diagram_data = extract_json_block(diagram_json_output)
        workflow_mermaid = diagram_data.get("workflow_mermaid", "Error: Workflow diagram not found.")
        architecture_mermaid = diagram_data.get("architecture_mermaid", "Error: Architecture diagram not found.")

        # Create a "Full Project Guide" page in Notion.
        guide_page_result = composio_instance.tools.execute(
            user_id=MY_APP_USER_ID,
            slug="NOTION_CREATE_NOTION_PAGE",
            arguments={"parent_id": project_page_id, "title": "Full Project Guide"}
        )
        if not guide_page_result.get("successful"):
            raise Exception(f"Failed to create the final guide page: {guide_page_result.get('error')}")

        guide_page_id = guide_page_result['data']['id']

        # Prepare content blocks for the Notion page, including diagrams and code.
        final_content_blocks = [
            {"content_block": {"content": "## Workflow Diagram"}},
            # Wrap the mermaid diagram source in a Markdown code block
            {"content_block": {"content": f"```mermaid\n{workflow_mermaid}\n```"}},
            
            {"content_block": {"content": "## Architecture Diagram"}},
            # Wrap the architecture diagram source in a Markdown code block
            {"content_block": {"content": f"```mermaid\n{architecture_mermaid}\n```"}},

            {"content_block": {"content": "## Arduino Code"}},
            # Wrap the Arduino code in a Markdown code block, specifying the language
            {"content_block": {"content": f"```cpp\n{clean_code_block(code_sketch, 'cpp')}\n```"}}
        ]

        # Append the generated content to the Notion guide page.
        append_result = composio_instance.tools.execute(
            user_id=MY_APP_USER_ID,
            slug="NOTION_ADD_MULTIPLE_PAGE_CONTENT",
            arguments={"parent_block_id": guide_page_id, "content_blocks": final_content_blocks}
        )
        if not append_result.get("successful"):
            raise Exception(f"Failed to append final assets to the guide page: {append_result.get('error')}")

        print("✅ Final guide page created and populated successfully.")

        # Clear session data and provide the final Notion project URL.
        project_page_url = session.get('project_page_url', '#')
        session.clear()

        return jsonify({"result": f"[View your complete project folder on Notion!]({project_page_url})"})
    except Exception as e:
        print(f"❌ Error during Stage 3: {e}")
        return jsonify({"error": "Error in Stage 3", "details": str(e)}), 500

# --- Application Entry Point ---

if __name__ == '__main__':
    # Run the Flask application in debug mode.
    # use_reloader=False prevents the app from restarting twice.
    app.run(debug=True, use_reloader=False, port=5000)
