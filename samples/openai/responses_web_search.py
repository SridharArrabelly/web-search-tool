import os
from openai import OpenAI

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

response = client.responses.create(
    model="gpt-5.5",
    tools=[
        {
            "type": "web_search",
            "filters": {
                "allowed_domains": ["www.sars.gov.za"],
            },
        }
    ],
    # tool_choice={"type": "web_search"},
    include=["web_search_call.action.sources"],
    input="Tell me PAYE tax brackets for the year 2026?",
)

print("=== Output ===")
print(response.output_text)

print("\n=== Sources ===")
for item in response.output:
    if getattr(item, "type", None) == "web_search_call":
        action = getattr(item, "action", None)
        sources = getattr(action, "sources", None) if action else None
        if sources:
            for s in sources:
                print("-", getattr(s, "url", s))

print("\n=== Token usage ===")
usage = response.usage
if usage is None:
    print("No usage data returned.")
else:
    try:
        usage_dict = usage.model_dump()
    except AttributeError:
        usage_dict = dict(usage)

    print(f"Input tokens : {usage_dict.get('input_tokens')}")
    print(f"Output tokens: {usage_dict.get('output_tokens')}")
    print(f"Total tokens : {usage_dict.get('total_tokens')}")

    details = usage_dict.get("input_tokens_details") or {}
    if details:
        print(f"  input details : {details}")
    out_details = usage_dict.get("output_tokens_details") or {}
    if out_details:
        print(f"  output details: {out_details}")

    print("\nFull usage object:")
    print(usage_dict)
