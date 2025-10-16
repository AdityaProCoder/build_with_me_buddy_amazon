# src/crew.py (Final Corrected Version)
import os
import yaml  # Import the YAML library
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.llm import LLM
from src.tools.composio_tools import parts_sourcing_tool

# --- Define the LLMs for the Crew ---
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("FATAL ERROR: GOOGLE_API_KEY or GEMINI_API_KEY not found in .env file.")

manager_llm = LLM(model="gemini/gemini-2.5-pro", api_key=api_key)
worker_llm = LLM(model="gemini/gemini-2.5-flash", api_key=api_key)


@CrewBase
class ProjectPartnerCrew():
    """A crew designed to take a project idea and build a complete guide."""

    # --- THIS IS THE FIX FOR THE WARNINGS ---
    # We manually load the YAML files so the IDE understands their structure.
    with open('src/config/agents.yaml', 'r') as f:
        AGENTS_CONFIG = yaml.safe_load(f)
    with open('src/config/tasks.yaml', 'r') as f:
        TASKS_CONFIG = yaml.safe_load(f)

    # --- Agent Definitions ---
    @agent
    def project_architect(self) -> Agent:
        return Agent(config=self.AGENTS_CONFIG['agents']['project_architect'], llm=manager_llm, memory=True,
                     verbose=True)

    @agent
    def system_designer(self) -> Agent:
        return Agent(config=self.AGENTS_CONFIG['agents']['system_designer'], llm=worker_llm, memory=True, verbose=True)

    @agent
    def parts_sourcer(self) -> Agent:
        return Agent(
            config=self.AGENTS_CONFIG['agents']['parts_sourcer'],
            tools=parts_sourcing_tool,
            llm=worker_llm,
            memory=True,
            verbose=True
        )

    @agent
    def budget_optimizer(self) -> Agent:
        return Agent(config=self.AGENTS_CONFIG['agents']['budget_optimizer'], llm=worker_llm, memory=True, verbose=True)

    @agent
    def circuit_designer(self) -> Agent:
        return Agent(config=self.AGENTS_CONFIG['agents']['circuit_designer'], llm=worker_llm, memory=True, verbose=True)

    @agent
    def code_wizard(self) -> Agent:
        return Agent(config=self.AGENTS_CONFIG['agents']['code_wizard'], llm=worker_llm, memory=True, verbose=True)

    @agent
    def storyboard_creator(self) -> Agent:
        return Agent(config=self.AGENTS_CONFIG['agents']['storyboard_creator'], llm=worker_llm, memory=True,
                     verbose=True)

    # --- Task Definitions ---
    @task
    def project_planning_task(self) -> Task:
        return Task(config=self.TASKS_CONFIG['tasks']['project_planning_task'], agent=self.project_architect())

    @task
    def component_reasoning_task(self) -> Task:
        return Task(config=self.TASKS_CONFIG['tasks']['component_reasoning_task'], agent=self.system_designer())

    @task
    def component_sourcing_task(self) -> Task:
        return Task(config=self.TASKS_CONFIG['tasks']['component_sourcing_task'], agent=self.parts_sourcer(),
                    context=[self.component_reasoning_task()])

    @task
    def budget_optimization_task(self) -> Task:
        return Task(config=self.TASKS_CONFIG['tasks']['budget_optimization_task'], agent=self.budget_optimizer(),
                    context=[self.component_sourcing_task()])

    @task
    def circuit_design_task(self) -> Task:
        return Task(config=self.TASKS_CONFIG['tasks']['circuit_design_task'], agent=self.circuit_designer(),
                    context=[self.budget_optimization_task()])

    @task
    def code_generation_task(self) -> Task:
        return Task(config=self.TASKS_CONFIG['tasks']['code_generation_task'], agent=self.code_wizard(),
                    context=[self.circuit_design_task()])

    @task
    def storyboard_creation_task(self) -> Task:
        return Task(config=self.TASKS_CONFIG['tasks']['storyboard_creation_task'], agent=self.storyboard_creator(),
                    context=[self.code_generation_task()])

    # --- Crew Definitions ---
    @crew
    def planning_crew(self) -> Crew:
        return Crew(agents=[self.project_architect()], tasks=[self.project_planning_task()], process=Process.sequential,
                    verbose=True)

    @crew
    def build_crew(self) -> Crew:
        return Crew(
            agents=[
                self.system_designer(),
                self.parts_sourcer(),
                self.budget_optimizer(),
                self.circuit_designer(),
                self.code_wizard(),
                self.storyboard_creator()
            ],
            tasks=[
                self.component_reasoning_task(),
                self.component_sourcing_task(),
                self.budget_optimization_task(),
                self.circuit_design_task(),
                self.code_generation_task(),
                self.storyboard_creation_task()
            ],
            process=Process.sequential,
            verbose=True
        )
