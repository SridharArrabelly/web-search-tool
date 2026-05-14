import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    WebSearchTool,
    WebSearchApproximateLocation,
)

load_dotenv()

# Format: "https://resource_name.ai.azure.com/api/projects/project_name"
PROJECT_ENDPOINT = os.environ["PROJECT_ENDPOINT"]
MODEL = os.environ.get("MODEL", "gpt-5.1")  # Default to gpt-5.1 if MODEL is not set in .env

# Create clients to call Foundry API
project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)
openai = project.get_openai_client()

# Create an agent with the web search tool
agent = project.agents.create_version(
    agent_name="WebSearchToolAgent-Bing",
    definition=PromptAgentDefinition(
        model=MODEL,
        instructions="""  You are a helpful assistant that can search the web.""",
        tools=[
            WebSearchTool(
                user_location=WebSearchApproximateLocation(
                    country="ZA", city="Johannesburg", region="Gauteng"
                )
            )
        ],
    ),
    description="Agent for web search.",
)

print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")

# Send a query and stream the response
stream_response = openai.responses.create(
    stream=True,
    tool_choice="required",
    input="What are the personal tax rates for the 2026 tax year in South Africa?",
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
)

# Process streaming events
for event in stream_response:
    if event.type == "response.created":
        print(f"Follow-up response created with ID: {event.response.id}")
    elif event.type == "response.output_text.delta":
        print(f"Delta: {event.delta}")
    elif event.type == "response.text.done":
        print(f"\nFollow-up response done!")
    elif event.type == "response.output_item.done":
        if event.item.type == "message":
            item = event.item
            if item.content[-1].type == "output_text":
                text_content = item.content[-1]
                for annotation in text_content.annotations:
                    if annotation.type == "url_citation":
                        print(f"URL Citation: {annotation.url}")
    elif event.type == "response.completed":
        print(f"\nFollow-up completed!")
        print(f"Full response: {event.response.output_text}")

# project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
# print("Agent deleted")
