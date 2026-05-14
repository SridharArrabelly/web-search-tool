import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    BingCustomSearchPreviewTool,
    BingCustomSearchToolParameters,
    BingCustomSearchConfiguration,
)

load_dotenv()

# Format: "https://resource_name.ai.azure.com/api/projects/project_name"
PROJECT_ENDPOINT = os.environ["PROJECT_ENDPOINT"]
CUSTOM_SEARCH_CONNECTION_NAME = os.environ["CUSTOM_SEARCH_CONNECTION_NAME"]
CUSTOM_SEARCH_INSTANCE_NAME = os.environ["CUSTOM_SEARCH_INSTANCE_NAME"]
MODEL = os.environ.get("MODEL", "gpt-5.1")  # Default to gpt-5.1 if MODEL is not set in .env

# Create clients to call Foundry API
project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)
openai = project.get_openai_client()

# Get connection ID from connection name
bing_custom_connection = project.connections.get(CUSTOM_SEARCH_CONNECTION_NAME)

bing_custom_search_tool = BingCustomSearchPreviewTool(
    bing_custom_search_preview=BingCustomSearchToolParameters(
        search_configurations=[
            BingCustomSearchConfiguration(
                project_connection_id=bing_custom_connection.id,
                instance_name=CUSTOM_SEARCH_INSTANCE_NAME,
            )
        ]
    )
)
print(f"Model used: {MODEL}")

agent = project.agents.create_version(
    agent_name="BingCustomSearchToolAgent",
    definition=PromptAgentDefinition(
        model=MODEL,
        # instructions="""You are a helpful assistant that can assist users with answering their questions.""",
        instructions="""You are an AI assistant that answers questions using Bing Custom Search.

                Rules:

                Only use information from https://www.sars.gov.za/
                Ignore all other websites and sources.
                Answer only based on retrieved SARS content.
                Keep responses clear, accurate, and professional.
                Include SARS references or links when available.
                Do not guess, speculate, or use outside knowledge.

                If the information is not found on the SARS website, respond with:
                "I could not find this information on the official SARS website. Please check directly on https://www.sars.gov.za/ or refine your query.""",
        tools=[bing_custom_search_tool],
    ),
    description="Agent for domain-restricted web search using Bing Custom Search tool.",
)
print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")

# user_input = input(
#     "Enter your question for the Bing Custom Search agent " "(e.g., 'Tell me more about foundry agent service'): \n"
# )

# Send initial request that will trigger the Bing Custom Search tool
stream_response = openai.responses.create(
    stream=True,
    input="What are the PAYE tax rates for the 2026 tax year?",
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
)

print(f"apim-request-id: {stream_response.response.headers.get('apim-request-id')}")

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
                        print(
                            f"URL Citation: {annotation.url}, "
                            f"Start index: {annotation.start_index}, "
                            f"End index: {annotation.end_index}"
                        )
    elif event.type == "response.completed":
        print(f"\nFollow-up completed!")
        print(f"Full response: {event.response.output_text}")
