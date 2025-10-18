# src/tools/composio_tools.py
import os
from composio import Composio
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, create_model
from typing import Type, Any

# This is a consistent, hardcoded ID for your application's "user".
MY_APP_USER_ID = "build-with-me-buddy-developer-001"

# 1. Instantiate the main Composio class. This will be our "Doer".
composio_instance = Composio()

# 2. Define the tool(s) that the THINKER agents will have access to.
#    We are only giving them the search tool.
agent_tool_names = ["COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH"]

# 3. Get the raw descriptions for ONLY the agent-facing tools.
raw_tool_descriptions = composio_instance.tools.get(
    user_id=MY_APP_USER_ID,
    tools=agent_tool_names
)


# 4. The Custom Tool Bridge (for the search tool only)
class ComposioCustomTool(BaseTool):
    name: str
    description: str
    slug: str
    args_schema: Type[BaseModel]

    def _run(self, **kwargs: Any) -> Any:
        return composio_instance.tools.execute(
            user_id=MY_APP_USER_ID,
            slug=self.slug,
            arguments=kwargs
        )


# 5. The Factory to build ONLY the search tool object.
tools_for_agents = []
for tool_dict in raw_tool_descriptions:
    tool_name = tool_dict['function']['name']
    tool_description = tool_dict['function']['description']

    args_fields = {}
    if 'parameters' in tool_dict['function'] and 'properties' in tool_dict['function']['parameters']:
        for prop, details in tool_dict['function']['parameters']['properties'].items():
            args_fields[prop] = (str, Field(..., description=details.get('description')))

    ArgsSchema = create_model(f"{tool_name.replace('.', '_')}Schema", **args_fields)

    new_tool = ComposioCustomTool(
        name=tool_name,
        description=tool_description,
        slug=tool_name,
        args_schema=ArgsSchema
    )
    tools_for_agents.append(new_tool)

print("✅ Successfully built agent-facing tools from Composio data.")