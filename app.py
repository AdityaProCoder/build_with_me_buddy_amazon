# app.py (The Definitive, Corrected Version)
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
import time
from src.crew import ProjectPartnerCrew
from src.tools.composio_tools import composio_instance, MY_APP_USER_ID
from litellm import RateLimitError

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


# Helper function to execute crews with retries
def execute_crew_with_retries(crew_function, inputs, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            result = crew_function().kickoff(inputs=inputs)
            if result is None: raise Exception("Crew kickoff returned no result.")
            return result
        except RateLimitError as e:
            retries += 1
            print(f"🚨 Rate limit error. Attempt {retries}/{max_retries}. Retrying in 60s...")
            time.sleep(60)
            if retries == max_retries: raise e


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/kickoff_crew', methods=['POST'])
def kickoff_crew_endpoint():
    """Stage 1: AI generates the initial plan."""
    data = request.get_json()
    project_details = data.get('project_details')
    if not project_details: return jsonify({"error": "Project details are required."}), 400

    print(f"🚀 Stage 1: Planning for -> {project_details}")
    try:
        crew_manager = ProjectPartnerCrew()
        inputs = {'project_details': project_details}
        result = execute_crew_with_retries(crew_manager.planning_crew, inputs)

        session['project_plan'] = result.raw
        session['project_details'] = project_details

        print(f"✅ Stage 1 Finished.")
        return jsonify({
            "result": result.raw,
            "prompt": "Enter 'Proceed' to generate the Bill of Materials."
        })
    except Exception as e:
        print(f"❌ Error during Stage 1: {e}")
        return jsonify({"error": "Error in Stage 1", "details": str(e)}), 500


@app.route('/generate_bom', methods=['POST'])
def generate_bom_endpoint():
    """Stage 2: AI thinks, Python does."""
    project_plan = session.get('project_plan')
    project_details = session.get('project_details')
    if not project_plan or not project_details: return jsonify({"error": "Session data missing."}), 400

    print(f"🚀 Stage 2: Generating BOM content for -> {project_details}")
    try:
        # === PART 1: The "Thinker" (AI Crews running in sequence) ===
        crew_manager = ProjectPartnerCrew()

        print("🧠 Generating project name...")
        name_result = execute_crew_with_retries(crew_manager.naming_crew, {'project_details': project_details})
        project_name = name_result.raw

        print("🧠 Designing conceptual BOM...")
        design_result = execute_crew_with_retries(crew_manager.design_crew, {'project_plan': project_plan})
        conceptual_bom_table = design_result.raw

        print("🧠 Sourcing final parts...")
        sourcing_result = execute_crew_with_retries(crew_manager.sourcing_crew, {'final_bom': conceptual_bom_table})
        full_bom_output = sourcing_result.raw

        # --- THIS IS THE ROBUSTNESS FIX ---
        # Check if the AI succeeded before trying to split the string.
        if '---DATA_SEPARATOR---' not in full_bom_output:
            raise Exception(
                f"Sourcing crew failed to generate the correct output format. It returned: '{full_bom_output}'")

        user_summary, final_bom_table = full_bom_output.split('---DATA_SEPARATOR---')

        # === PART 2: The "Doer" (Python Code) ===
        print("🤖 Python is now creating the Notion pages...")
        # ... (The rest of the Notion tool calls are correct and remain the same) ...
        project_page_result = composio_instance.tools.execute(
            user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE",
            arguments={"parent_id": os.getenv("NOTION_PARENT_PAGE_ID"), "title": project_name}
        )
        if not project_page_result.get("successful"): raise Exception(
            f"Failed to create main project page: {project_page_result.get('error')}")

        project_page_id = project_page_result['data']['id']
        project_page_url = project_page_result['data']['url']
        session['project_page_id'] = project_page_id
        session['project_page_url'] = project_page_url

        conceptual_page_result = composio_instance.tools.execute(
            user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE",
            arguments={"parent_id": project_page_id, "title": "Conceptual BOM"}
        )
        if not conceptual_page_result.get("successful"): raise Exception(
            f"Failed to create Conceptual BOM page: {conceptual_page_result.get('error')}")
        conceptual_page_id = conceptual_page_result['data']['id']
        composio_instance.tools.execute(
            user_id=MY_APP_USER_ID, slug="NOTION_APPEND_BLOCK_CHILDREN",
            arguments={"block_id": conceptual_page_id, "content": conceptual_bom_table}
        )

        final_bom_page_result = composio_instance.tools.execute(
            user_id=MY_APP_USER_ID, slug="NOTION_CREATE_NOTION_PAGE",
            arguments={"parent_id": project_page_id, "title": "Final Bill of Materials (BOM)"}
        )
        if not final_bom_page_result.get("successful"): raise Exception(
            f"Failed to create Final BOM page: {final_bom_page_result.get('error')}")
        final_bom_page_id = final_bom_page_result['data']['id']
        composio_instance.tools.execute(
            user_id=MY_APP_USER_ID, slug="NOTION_APPEND_BLOCK_CHILDREN",
            arguments={"block_id": final_bom_page_id, "content": final_bom_table}
        )
        print("✅ Notion pages created and populated successfully.")

        session['final_bom_data'] = final_bom_table.strip()

        final_output_for_user = user_summary.strip() + f"\n\n[View your full project folder on Notion]({project_page_url})"
        return jsonify({"result": final_output_for_user,
                        "prompt": "Enter 'Proceed' to generate the final assets (code and diagram)."})

    except Exception as e:
        print(f"❌ Error during Stage 2: {e}")
        return jsonify({"error": "Error in Stage 2", "details": str(e)}), 500


@app.route('/generate_final_assets', methods=['POST'])
def generate_final_assets_endpoint():
    """Stage 3: AI generates assets, Python publishes them."""
    # ... (This function is correct and needs no changes) ...
    final_bom_data = session.get('final_bom_data')
    project_page_id = session.get('project_page_id')
    if not final_bom_data or not project_page_id: return jsonify({"error": "Session data missing."}), 400

    print(f"🚀 Stage 3: Generating final assets...")
    try:
        crew_manager = ProjectPartnerCrew()
        inputs = {'final_bom': final_bom_data}
        ai_result = execute_crew_with_retries(crew_manager.final_assets_crew, inputs)

        # We must access the individual task outputs to separate them.
        circuit_diagram = ai_result.tasks_outputs[0].raw_output
        code_sketch = ai_result.tasks_outputs[1].raw_output

        print("🤖 Python is now appending assets to the Notion page...")

        final_content = f"## Circuit Diagram\n\n```mermaid\n{circuit_diagram}\n```\n\n## Arduino Code\n\n```cpp\n{code_sketch}\n```"

        append_result = composio_instance.tools.execute(
            user_id=MY_APP_USER_ID,
            slug="NOTION_APPEND_BLOCK_CHILDREN",
            arguments={"block_id": project_page_id, "content": final_content}
        )
        if not append_result.get("successful"): raise Exception(
            f"Failed to append assets: {append_result.get('error')}")

        print("✅ Final assets appended successfully.")

        project_page_url = session.get('project_page_url', '#')
        session.clear()

        return jsonify({"result": f"[View your complete project guide on Notion!]({project_page_url})"})
    except Exception as e:
        print(f"❌ Error during Stage 3: {e}")
        return jsonify({"error": "Error in Stage 3", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)