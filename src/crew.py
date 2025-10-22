# src/crew.py
import os
import yaml
from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM
# This now correctly imports only the tools the agents need (the search tool)
from src.tools.composio_tools import tools_for_agents

# Load configs and LLMs at the module level
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("FATAL ERROR: GOOGLE_API_KEY or GEMINI_API_KEY not found in .env file.")

manager_llm = LLM(model="gemini/gemini-2.5-pro", api_key=api_key)
worker_llm = LLM(model="gemini/gemini-2.5-flash", api_key=api_key)

with open('src/config/agents.yaml', 'r') as f:
    AGENTS_CONFIG = yaml.safe_load(f)
with open('src/config/tasks.yaml', 'r') as f:
    TASKS_CONFIG = yaml.safe_load(f)


class ProjectPartnerCrew:
    def __init__(self):
        # Create all agent instances. The parts_sourcer now only has the search tool.
        self.agents = {
            'project_architect': Agent(config=AGENTS_CONFIG['agents']['project_architect'], llm=worker_llm, memory=True, verbose=True),
            'project_namer': Agent(config=AGENTS_CONFIG['agents']['project_namer'], llm=worker_llm, memory=True, verbose=True),
            'system_designer': Agent(config=AGENTS_CONFIG['agents']['system_designer'], llm=worker_llm, memory=True, verbose=True),
            'parts_sourcer': Agent(config=AGENTS_CONFIG['agents']['parts_sourcer'], 
                        tools=tools_for_agents, 
                       llm=worker_llm, memory=True, verbose=True, max_iter=25, max_rpm=4),            
            'diagram_specialist': Agent(config=AGENTS_CONFIG['agents']['diagram_specialist'], llm=worker_llm, memory=True, verbose=True, max_rpm=4),
            'code_wizard': Agent(config=AGENTS_CONFIG['agents']['code_wizard'], llm=worker_llm, memory=True, verbose=True)
        }

    def planning_crew(self):
        """Generates the initial project plan."""
        task = Task(**TASKS_CONFIG['tasks']['project_planning_task'], agent=self.agents['project_architect'])
        return Crew(agents=[self.agents['project_architect']], tasks=[task], process=Process.sequential, verbose=True)

    def naming_crew(self):
        """Generates just the project name."""
        task = Task(**TASKS_CONFIG['tasks']['project_naming_task'], agent=self.agents['project_namer'])
        return Crew(agents=[self.agents['project_namer']], tasks=[task], process=Process.sequential, verbose=True)

    def design_crew(self):
        """Generates just the conceptual BOM markdown table."""
        task = Task(**TASKS_CONFIG['tasks']['component_reasoning_task'], agent=self.agents['system_designer'])
        return Crew(agents=[self.agents['system_designer']], tasks=[task], process=Process.sequential, verbose=True)

    def sourcing_crew(self):
        """Takes a conceptual BOM and generates the final summary and table."""
        task = Task(**TASKS_CONFIG['tasks']['component_sourcing_task'], agent=self.agents['parts_sourcer'])
        return Crew(agents=[self.agents['parts_sourcer']], tasks=[task], process=Process.sequential, verbose=True)

    def diagram_generation_crew(self):
        """Generates all the Mermaid diagrams in a single JSON object."""
        task = Task(**TASKS_CONFIG['tasks']['diagram_generation_task'], agent=self.agents['diagram_specialist'])
        return Crew(agents=[self.agents['diagram_specialist']], tasks=[task], process=Process.sequential, verbose=True)

    def code_generation_crew(self):
        """Generates the final Arduino code."""
        task = Task(**TASKS_CONFIG['tasks']['code_generation_task'], agent=self.agents['code_wizard'])
        return Crew(agents=[self.agents['code_wizard']], tasks=[task], process=Process.sequential, verbose=True)