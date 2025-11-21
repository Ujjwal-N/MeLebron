"""Minimal hello world using the Claude Agents SDK."""

from __future__ import annotations

import asyncio

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, query


async def main() -> None:
    prompt = "Respond with exactly 'Hello World from the Claude Agents SDK!'"

    async for message in query(prompt=prompt):
        if isinstance(message, AssistantMessage):
            text_blocks = [block.text for block in message.content if isinstance(block, TextBlock)]
            if text_blocks:
                print("\n".join(text_blocks))
        elif isinstance(message, ResultMessage):
            total_cost = f"${message.total_cost_usd:.4f}" if message.total_cost_usd else "$0.0000"
            print(f"\nFinished session {message.session_id} in {message.duration_ms / 1000:.2f}s (cost {total_cost}).")


if __name__ == "__main__":
    asyncio.run(main())
