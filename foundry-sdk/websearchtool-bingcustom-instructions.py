import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    WebSearchTool,
    WebSearchConfiguration,
    WebSearchApproximateLocation,
)

load_dotenv()

# Format: "https://resource_name.ai.azure.com/api/projects/project_name"
PROJECT_ENDPOINT = os.environ["PROJECT_ENDPOINT"]
BING_CUSTOM_SEARCH_CONNECTION_ID = os.environ["BING_CUSTOM_SEARCH_CONNECTION_ID"]
BING_CUSTOM_SEARCH_INSTANCE_NAME = os.environ["BING_CUSTOM_SEARCH_INSTANCE_NAME"]
MODEL = os.environ.get("MODEL", "gpt-5.1")  # Default to gpt-5.1 if MODEL is not set in .env

# Create clients to call Foundry API
project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)
openai = project.get_openai_client()

# Create an agent with the web search tool and custom search configuration
agent = project.agents.create_version(
    agent_name="WebSearchToolAgent-BingCustom-instructions",
    definition=PromptAgentDefinition(
        model=MODEL,
        # instructions="""You are an AI assistant that answers user questions using information retrieved via web Search.

        #                 STRICT SCOPING RULES:
        #                 - You MUST search and retrieve information ONLY from the domain: https://www.sars.gov.za/
        #                 - Do NOT use, cite, or rely on any other websites or external sources.
        #                 - If search results include content from outside this domain, ignore those results.

        #                 BEHAVIOR:
        #                 - Always prioritize official and authoritative information from the SARS website.
        #                 - Provide clear, accurate, and concise answers based only on the retrieved content.
        #                 - Include citations or references to the SARS website where applicable.

        #                 FAILURE HANDLING:
        #                 - If relevant information is not found on https://www.sars.gov.za/, respond with:
        #                 "I could not find this information on the official SARS website. Please check directly on https://www.sars.gov.za/ or refine your query."
        #                 - Do NOT hallucinate or infer answers outside the available content.

        #                 RESPONSE STYLE:
        #                 - Keep responses factual and professional.
        #                 - Do not include speculation or general knowledge outside the scoped domain. """,
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
        tools=[
            WebSearchTool(
                custom_search_configuration=WebSearchConfiguration(
                    project_connection_id=BING_CUSTOM_SEARCH_CONNECTION_ID,
                    instance_name=BING_CUSTOM_SEARCH_INSTANCE_NAME,
                ),
                # user_location=WebSearchApproximateLocation(
                #     country="ZA", city="Johannesburg", region="Gauteng"
                # ),
                search_context_size="low",
            )
        ],
    ),
    description="Agent for domain-restricted web search.",
)
print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")

# Send a query and stream the response
stream_response = openai.responses.create(
    stream=True,
    tool_choice="required",
    input="What are the personal tax rates for the 2025 tax year?",
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
)

print(f"apim-request-id: {stream_response.response.headers.get('apim-request-id')}")

# Process streaming events
for event in stream_response:
    if event.type == "response.created":
        print(f"Response created with ID: {event.response.id}")
    elif event.type == "response.output_text.delta":
        print(f"Delta: {event.delta}")
    elif event.type == "response.text.done":
        print(f"\nResponse done!")
    elif event.type == "response.output_item.done":
        if event.item.type == "message":
            item = event.item
            if item.content[-1].type == "output_text":
                text_content = item.content[-1]
                for annotation in text_content.annotations:
                    if annotation.type == "url_citation":
                        print(f"URL Citation: {annotation.url}")
    elif event.type == "response.completed":
        print(f"\nResponse completed!")
        print(f"Full response: {event.response.output_text}")

# project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
# print("Agent deleted")
