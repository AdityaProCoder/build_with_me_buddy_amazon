# app.py
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os

# Import your CrewAI class
from src.crew import ProjectPartnerCrew

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# A secret key is required for Flask session management
app.config['SECRET_KEY'] = os.urandom(24)


@app.route('/')
def index():
    """Renders the main landing page."""
    return render_template('index.html')


# This is the UPDATED, correct code for app.py

# In app.py, replace the whole kickoff_crew_endpoint function

@app.route('/kickoff_crew', methods=['POST'])
def kickoff_crew_endpoint():
    """API endpoint for the FIRST stage: Project Planning."""
    data = request.get_json()
    project_details = data.get('project_details')

    if not project_details:
        return jsonify({"error": "Project details are required."}), 400

    print(f"🚀 Kicking off planning phase for: {project_details}")

    try:
        project_crew_manager = ProjectPartnerCrew()
        inputs = {'project_details': project_details}

        planning_result_object = project_crew_manager.planning_crew().kickoff(inputs=inputs)
        plan_string = planning_result_object.raw

        # Save the plan to the session
        session['project_plan'] = plan_string

        # --- THIS IS THE FIX ---
        # We must also save the original project details for the next step.
        session['project_details'] = project_details
        # --- END OF FIX ---

        print(f"✅ Planning phase finished.")

        return jsonify({
            "result": plan_string,
            "prompt": "Enter Proceed to continue to add Parts to Cart 🛒"
        })

    except Exception as e:
        print(f"❌ Error during Planning Crew execution: {e}")
        return jsonify({"error": "An error occurred during the planning phase.", "details": str(e)}), 500

@app.route('/continue_crew', methods=['POST'])
def continue_crew_endpoint():
    """API endpoint for the SECOND stage: Building the project guide."""
    # Retrieve the stored plan from the session
    project_plan = session.get('project_plan')
    project_details = session.get('project_details')

    if not project_plan or not project_details:
        return jsonify({"error": "No project plan found in session. Please start over."}), 400

    print("🚀 Continuing to build phase...")

    try:
        project_crew_manager = ProjectPartnerCrew()
        # The 'project_plan' from the first crew is now an input for the second crew
        inputs = {
            'project_details': project_details,
            'project_plan': project_plan
        }

        # Run the build crew
        build_result = project_crew_manager.build_crew().kickoff(inputs=inputs)

        print(f"✅ Build phase finished.")

        # Clear the session after completion
        session.pop('project_plan', None)
        session.pop('project_details', None)

        return jsonify({"result": build_result})

    except Exception as e:
        print(f"❌ Error during Build Crew execution: {e}")
        return jsonify({"error": "An error occurred during the build phase.", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)