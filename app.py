# app.py
from dotenv import load_dotenv
import os

# --- THIS IS THE DEFINITIVE FIX ---
# This block MUST run before any other application imports (like src.crew).
# It ensures the environment is configured before any part of your app needs it.
project_root = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    print(f"✅ Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("⚠️ .env file not found. Please ensure it exists in the project root.")
# ------------------------------------

# Now that the environment is loaded, we can safely import the rest of the application.
from flask import Flask, render_template, request, jsonify, session
import time
import json 
from src.crew import ProjectPartnerCrew
from src.tools.composio_tools import composio_instance, MY_APP_USER_ID

# Define the checkpoint file path
CHECKPOINT_FILE = "task_progress.json"


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/kickoff_crew', methods=['POST'])
def kickoff_crew_endpoint():
    """Stage 1: AI generates the initial plan and clears old checkpoints."""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    data = request.get_json()
    project_details = data.get('project_details')
    if not project_details: return jsonify({"error": "Project details are required."}), 400

    print(f"🚀 Stage 1: Planning for -> {project_details}")
    try:
        crew_manager = ProjectPartnerCrew()
        result = crew_manager.planning_crew().kickoff(inputs={'project_details': project_details})
        
        session['project_plan'] = result.raw
        session['project_details'] = project_details

        print(f"✅ Stage 1 Finished.")
        return jsonify({
            "result": result.raw,
            "prompt": "Enter 'Proceed' to generate the Bill of Materials."
        })
    except Exception as e:
        return jsonify({"error": "Error in Stage 1", "details": str(e)}), 500

    
@app.route('/generate_bom', methods=['POST'])
def generate_bom_endpoint():
    """Stage 2: AI thinks (in pieces), Python does (publishes)."""
    project_plan = session.get('project_plan')
    project_details = session.get('project_details')
    if not project_plan or not project_details: return jsonify({"error": "Session data missing."}), 400

    print(f"🚀 Stage 2: Generating BOM content for -> {project_details}")
    try:
        crew_manager = ProjectPartnerCrew()

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
        
        # --- THIS IS THE DEFINITIVE FIX ---
        # The key in the dictionary MUST match the placeholder in tasks.yaml.
        # The placeholder is {final_bom}, so the key must be 'final_bom'.
        sourcing_inputs = {'final_bom': session['conceptual_bom_table']}
        sourcing_result = crew_manager.sourcing_crew().kickoff(inputs=sourcing_inputs)
        
        if "RATE_LIMIT_HIT" in sourcing_result.raw:
            print("🚨 Rate limit hit. Process paused. Progress has been saved by the agent.")
            return jsonify({
                "result": "I'm working on your component list, but I've hit a temporary API limit. Your progress is saved!",
                "prompt": "Please wait 60 seconds and then enter 'Proceed' again to continue from where I left off."
            })

        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)

        full_bom_output = sourcing_result.raw
        
        if '---DATA_SEPARATOR---' not in full_bom_output:
            raise Exception(f"Sourcing crew failed to generate the correct output format. It returned: '{full_bom_output}'")
        
        user_summary, final_bom_table = full_bom_output.split('---DATA_SEPARATOR---')

        print("🤖 Python is now creating and populating the Notion pages...")
        project_name = session['project_name']
        
        project_page_result = composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE", arguments={"parent_id": os.getenv("NOTION_PARENT_PAGE_ID"), "title": project_name})
        if not project_page_result.get("successful"): raise Exception(f"Failed to create main project page: {project_page_result.get('error')}")
        
        project_page_id = project_page_result['data']['id']
        project_page_url = project_page_result['data']['url']
        session['project_page_id'] = project_page_id
        session['project_page_url'] = project_page_url

        conceptual_page_result = composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE", arguments={"parent_id": project_page_id, "title": "Conceptual BOM"})
        if not conceptual_page_result.get("successful"): raise Exception(f"Failed to create Conceptual BOM page: {conceptual_page_result.get('error')}")
        composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_ADD_MULTIPLE_PAGE_CONTENT", arguments={"parent_block_id": conceptual_page_result['data']['id'], "content_blocks": [{"content_block": {"content": session['conceptual_bom_table']}}]})
        
        final_bom_page_result = composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE", arguments={"parent_id": project_page_id, "title": "Final Bill of Materials (BOM)"})
        if not final_bom_page_result.get("successful"): raise Exception(f"Failed to create Final BOM page: {final_bom_page_result.get('error')}")
        composio_instance.tools.execute(user_id=MY_APP_USER_ID, slug="NOTION_ADD_MULTIPLE_PAGE_CONTENT", arguments={"parent_block_id": final_bom_page_result['data']['id'], "content_blocks": [{"content_block": {"content": final_bom_table}}]})
        
        print("✅ Notion pages created and populated successfully.")
        
        session['final_bom_data'] = final_bom_table.strip()
        final_output_for_user = user_summary.strip() + f"\n\n[View your full project folder on Notion]({project_page_url})"
        return jsonify({"result": final_output_for_user, "prompt": "Enter 'Proceed' to generate the final assets (code and diagram)."})

    except Exception as e:
        print(f"❌ Error during Stage 2: {e}")
        return jsonify({"error": "Error in Stage 2", "details": str(e)}), 500

  

@app.route('/generate_final_assets', methods=['POST'])
def generate_final_assets_endpoint():
    """Stage 3: AI generates assets, Python publishes them."""
    final_bom_data = session.get('final_bom_data')
    project_page_id = session.get('project_page_id')
    if not final_bom_data or not project_page_id: return jsonify({"error": "Session data missing."}), 400

    print(f"🚀 Stage 3: Generating final assets...")
    try:
        crew_manager = ProjectPartnerCrew()
        inputs = {'final_bom': final_bom_data}
        ai_result = crew_manager.final_assets_crew().kickoff(inputs=inputs)

        circuit_diagram = ai_result.tasks_outputs[0].raw_output
        code_sketch = ai_result.tasks_outputs[1].raw_output
        
        print("🤖 Python is now appending assets to the Notion page...")
        
        final_content = f"## Circuit Diagram\n\n```mermaid\n{circuit_diagram}\n```\n\n## Arduino Code\n\n```cpp\n{code_sketch}\n```"
        
        append_result = composio_instance.tools.execute(
            user_id=MY_APP_USER_ID,
            slug="NOTION_ADD_MULTIPLE_PAGE_CONTENT",
            arguments={"parent_block_id": project_page_id, "content_blocks": [{"content": final_content}]}
        )
        if not append_result.get("successful"): raise Exception(f"Failed to append assets: {append_result.get('error')}")

        print("✅ Final assets appended successfully.")
        
        project_page_url = session.get('project_page_url', '#')
        session.clear()
        
        return jsonify({"result": f"[View your complete project guide on Notion!]({project_page_url})"})
    except Exception as e:
        print(f"❌ Error during Stage 3: {e}")
        return jsonify({"error": "Error in Stage 3", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)