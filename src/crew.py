# src/crew.py

# Standard library imports
import os # Provides functions for interacting with the operating system, like accessing environment variables.
import yaml # Library for parsing YAML files, used here for configuration.

# Third-party library imports
from crewai import Agent, Crew, Process, Task # Core components from the CrewAI framework for defining agents, crews, processes, and tasks.
from crewai.llm import LLM # Used to define and configure Large Language Models for agents.

# Local application imports
from src.tools.composio_tools import tools_for_agents # Imports custom tools for agents from the composio_tools module.

# --- Configuration and Initialization ---

# Retrieve API key for Google Gemini models from environment variables.
# It checks for both GOOGLE_API_KEY and GEMINI_API_KEY for flexibility.
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    # Raise an error if no API key is found, as it's essential for LLM operation.
    raise ValueError("FATAL ERROR: GOOGLE_API_KEY or GEMINI_API_KEY not found in .env file.")

# Initialize different LLM instances for manager and worker agents.
# manager_llm uses a more powerful model (gemini-2.5-pro) for complex orchestration.
manager_llm = LLM(model="gemini/gemini-2.5-pro", api_key=api_key)
# worker_llm uses a faster, lighter model (gemini-2.5-flash) for individual tasks.
worker_llm = LLM(model="gemini/gemini-2.5-flash", api_key=api_key)

# Load agent configurations from a YAML file.
# This externalizes agent definitions, making them easier to manage and update.
with open('src/config/agents.yaml', 'r') as f:
    AGENTS_CONFIG = yaml.safe_load(f)
# Load task configurations from a YAML file.
# This externalizes task definitions, allowing for flexible task management.
with open('src/config/tasks.yaml', 'r') as f:
    TASKS_CONFIG = yaml.safe_load(f)

# --- ProjectPartnerCrew Class Definition ---

class ProjectPartnerCrew:
    """
    Manages the creation and orchestration of various AI agents and their respective crews
    for different stages of a project development lifecycle.
    """
    def __init__(self):
        """
        Initializes the ProjectPartnerCrew by defining and configuring individual agents.
        Each agent is assigned a specific role and an LLM.
        """
        self.agents = {
            # Project Architect: Responsible for initial project planning.
            'project_architect': Agent(config=AGENTS_CONFIG['agents']['project_architect'], llm=worker_llm, memory=True, verbose=True),
            # Project Namer: Responsible for generating project names.
            'project_namer': Agent(config=AGENTS_CONFIG['agents']['project_namer'], llm=worker_llm, memory=True, verbose=True),
            # System Designer: Responsible for designing conceptual Bill of Materials (BOM).
            'system_designer': Agent(config=AGENTS_CONFIG['agents']['system_designer'], llm=worker_llm, memory=True, verbose=True),
            # Parts Sourcer: Utilizes external tools to source final parts for the BOM.
            'parts_sourcer': Agent(config=AGENTS_CONFIG['agents']['parts_sourcer'],
                        tools=tools_for_agents, # Integrates external tools for sourcing.
                       llm=worker_llm, memory=True, verbose=True, max_iter=25, max_rpm=4),
            # Diagram Specialist: Generates various project diagrams (e.g., workflow, architecture).
            'diagram_specialist': Agent(config=AGENTS_CONFIG['agents']['diagram_specialist'], llm=worker_llm, memory=True, verbose=True, max_rpm=4),
            # Code Wizard: Generates code snippets, typically for microcontrollers like Arduino.
            'code_wizard': Agent(config=AGENTS_CONFIG['agents']['code_wizard'], llm=worker_llm, memory=True, verbose=True)
        }

    def planning_crew(self):
        """
        Creates a crew for initial project planning.
        The project_architect agent handles the 'project_planning_task'.
        """
        task = Task(**TASKS_CONFIG['tasks']['project_planning_task'], agent=self.agents['project_architect'])
        return Crew(agents=[self.agents['project_architect']], tasks=[task], process=Process.sequential, verbose=True)

    def naming_crew(self):
        """
        Creates a crew for generating project names.
        The project_namer agent handles the 'project_naming_task'.
        """
        task = Task(**TASKS_CONFIG['tasks']['project_naming_task'], agent=self.agents['project_namer'])
        return Crew(agents=[self.agents['project_namer']], tasks=[task], process=Process.sequential, verbose=True)

    def design_crew(self):
        """
        Creates a crew for designing the conceptual Bill of Materials (BOM).
        The system_designer agent handles the 'component_reasoning_task'.
        """
        task = Task(**TASKS_CONFIG['tasks']['component_reasoning_task'], agent=self.agents['system_designer'])
        return Crew(agents=[self.agents['system_designer']], tasks=[task], process=Process.sequential, verbose=True)

    def sourcing_crew(self):
        """
        Creates a crew for sourcing final parts based on the conceptual BOM.
        The parts_sourcer agent handles the 'component_sourcing_task'.
        """
        task = Task(**TASKS_CONFIG['tasks']['component_sourcing_task'], agent=self.agents['parts_sourcer'])
        return Crew(agents=[self.agents['parts_sourcer']], tasks=[task], process=Process.sequential, verbose=True)

    def diagram_generation_crew(self):
        """
        Creates a crew for generating project diagrams.
        The diagram_specialist agent handles the 'diagram_generation_task'.
        """
        task = Task(**TASKS_CONFIG['tasks']['diagram_generation_task'], agent=self.agents['diagram_specialist'])
        return Crew(agents=[self.agents['diagram_specialist']], tasks=[task], process=Process.sequential, verbose=True)

    def code_generation_crew(self):
        """
        Creates a crew for generating code (e.g., Arduino sketches).
        The code_wizard agent handles the 'code_generation_task'.
        """
        task = Task(**TASKS_CONFIG['tasks']['code_generation_task'], agent=self.agents['code_wizard'])
        return Crew(agents=[self.agents['code_wizard']], tasks=[task], process=Process.sequential, verbose=True)
