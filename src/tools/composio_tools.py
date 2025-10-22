# src/tools/composio_tools.py

# Standard library imports
import os # Provides functions for interacting with the operating system.
from typing import Type, Any # Used for type hinting, specifically for generic types.

# Third-party library imports
from composio import Composio # Imports the Composio client for interacting with external tools.
from crewai.tools import BaseTool # Base class for creating custom tools in CrewAI.
from pydantic import BaseModel, Field, create_model # Used for data validation and settings management, and dynamic model creation.

# --- Configuration and Initialization ---

# Define a unique user ID for the application to interact with Composio.
MY_APP_USER_ID = "build-with-me-buddy-developer-001"

# Initialize the Composio client.
composio_instance = Composio()

# List of tool names (slugs) that this agent will use from Composio.
# Currently configured to use DuckDuckGo search.
agent_tool_names = ["COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH"]

# Fetch raw tool descriptions from Composio based on the specified tool names.
raw_tool_descriptions = composio_instance.tools.get(
    user_id=MY_APP_USER_ID,
    tools=agent_tool_names
)

# --- Custom Composio Tool Class ---

class ComposioCustomTool(BaseTool):
    """
    A custom CrewAI tool wrapper for Composio tools.
    This class dynamically creates CrewAI-compatible tools from Composio tool descriptions.
    """
    name: str = Field(..., description="The name of the tool.")
    description: str = Field(..., description="A description of what the tool does.")
    slug: str = Field(..., description="The unique slug identifier for the Composio tool.")
    args_schema: Type[BaseModel] = Field(..., description="Pydantic model defining the tool's input arguments.")

    def _run(self, **kwargs: Any) -> Any:
        """
        Executes the Composio tool with the provided arguments.
        This method is called when the CrewAI agent uses the tool.
        """
        return composio_instance.tools.execute(
            user_id=MY_APP_USER_ID,
            slug=self.slug,
            arguments=kwargs
        )

# --- Dynamic Tool Creation ---

# List to store the dynamically created CrewAI tools.
tools_for_agents = []
for tool_dict in raw_tool_descriptions:
    # Extract tool name and description from the Composio tool dictionary.
    tool_name = tool_dict['function']['name']
    tool_description = tool_dict['function']['description']

    # Dynamically build the arguments schema for the tool using Pydantic.
    args_fields = {}
    if 'parameters' in tool_dict['function'] and 'properties' in tool_dict['function']['parameters']:
        for prop, details in tool_dict['function']['parameters']['properties'].items():
            # Each property becomes a field in the Pydantic model.
            args_fields[prop] = (str, Field(..., description=details.get('description')))

    # Create a Pydantic model for the tool's arguments.
    ArgsSchema = create_model(f"{tool_name.replace('.', '_')}Schema", **args_fields)

    # Instantiate the custom Composio tool and add it to the list.
    new_tool = ComposioCustomTool(
        name=tool_name,
        description=tool_description,
        slug=tool_name,
        args_schema=ArgsSchema
    )
    tools_for_agents.append(new_tool)

# Confirmation message that tools have been successfully built.
print("✅ Successfully built agent-facing tools from Composio data.")
