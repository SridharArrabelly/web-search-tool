import asyncio
import json
import logging
import os
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from agent_framework.foundry import FoundryChatClient
from agent_framework import Agent
from rich.console import Console
from rich.logging import RichHandler


console = Console()
logger = logging.getLogger(__name__)
load_dotenv(override=True)

async def main():
    async with DefaultAzureCredential() as cred:
        
        AgentName = "WebSearchToolAgent"
        AgentInstructions = (
            "You are a research assistant for a South African audience. "
            "You MUST answer using ONLY information returned by the web_search tool. "
            "If the search tool returns no relevant results, reply: "
            "'I could not find this in the configured sources.' "
            "Every factual claim must be followed by a numbered citation [n] and a Sources list "
            "containing only URLs returned by the tool."
        )
        logger.info(f"Creating agent: {AgentName}")
        
        client = FoundryChatClient(
            project_endpoint=os.getenv("PROJECT_ENDPOINT"),
            credential=cred,
            model=os.getenv("MODEL", "gpt-5.1"),
        )

        logger.info("Creating web search tool...")
        # Create web search tool
        web_search_tool = client.get_web_search_tool(
            user_location= {
                "country": "ZA",
            },
            allowed_domains=["www.sars.gov.za"],
            search_context_size="medium",
        )

        logger.info("Creating agent with web search tool...")
        agent = Agent(
            client=client,
            name=AgentName,
            instructions=AgentInstructions,
            tools=[web_search_tool],
            description="Agent for SARS-grounded web search.",
        )

        query = "What are the current individual income tax brackets?"
        console.print(f"User: {query}")
        
        
        result = await agent.run(query)
        console.print(f"Agent: {result.text}")


if __name__ == "__main__":
    logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(console=console)]
)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)
    logging.getLogger("azure.core").setLevel(logging.WARNING)
    asyncio.run(main())
