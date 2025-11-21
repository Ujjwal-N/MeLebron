import asyncio
import os

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import AssistantMessage, TextBlock

SYSTEM_PROMPT = "You are a helpful, thoughtful assistant."


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model="sonnet",  # or "claude-3-7-sonnet-latest", etc.
        system_prompt=SYSTEM_PROMPT,
        # Name can be anything; it becomes part of the tool prefix `mcp__redis-memory-server__...`
        mcp_servers={
            "redis-memory-server": {
                "type": "stdio",
                "command": "uv",
                "args": [
                    "--directory",
                    "/ABSOLUTE/PATH/TO/agent-memory-server",  # <- change this
                    "run",
                    "agent-memory",
                    "mcp",
                ],
                "env": {
                    "REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379"),
                    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
                },
            }
        },
        # Allow the specific Redis memory tools
        allowed_tools=[
            "mcp__redis-memory-server__set_working_memory",
            "mcp__redis-memory-server__create_long_term_memories",
            "mcp__redis-memory-server__search_long_term_memory",
            "mcp__redis-memory-server__edit_long_term_memory",
            "mcp__redis-memory-server__delete_long_term_memories",
            "mcp__redis-memory-server__get_long_term_memory",
            "mcp__redis-memory-server__memory_prompt",
        ],
        # So it doesn’t pause every time to ask you for tool permission
        permission_mode="acceptEdits",
    )


async def run_repl():
    options = build_options()
    async with ClaudeSDKClient(options=options) as client:
        print("Claude + Redis-memory REPL")
        print("Commands: 'exit' to quit\n")

        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            # Send the user query to the agent
            await client.query(user_input)

            print("Claude: ", end="", flush=True)

            # Stream back responses
            async for msg in client.receive_response():
                # Filter for assistant text chunks
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="", flush=True)

            print()  # newline after response


if __name__ == "__main__":
    asyncio.run(run_repl())
