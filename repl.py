import json
import time
from pathlib import Path

import anthropic
from anthropic import APIConnectionError, APIError, APIStatusError


class ClaudeREPL:
    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        history_file: str = "chat_history.json",
        system_prompt: str = None,
    ):
        self.client = anthropic.Anthropic()
        self.model = model
        self.history_file = Path(history_file)
        self.system_prompt = system_prompt
        self.conversation = self.load_history()

    def load_history(self) -> list:
        """Load conversation history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_history(self):
        """Persist conversation to disk"""
        with open(self.history_file, "w") as f:
            json.dump(self.conversation, f, indent=2)

    def chat_streaming(self, user_input: str, max_retries: int = 3) -> str:
        """Send message with streaming and update history"""
        self.conversation.append({"role": "user", "content": user_input})

        for attempt in range(max_retries):
            try:
                full_response = ""

                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=2048,
                    system=self.system_prompt,
                    messages=self.conversation,
                ) as stream:
                    for text in stream.text_stream:
                        print(text, end="", flush=True)
                        full_response += text

                print()

                self.conversation.append(
                    {"role": "assistant", "content": full_response}
                )
                self.save_history()
                return full_response

            except APIConnectionError as e:
                if attempt < max_retries - 1:
                    print(
                        f"\nConnection error, retrying... ({attempt + 1}/{max_retries})"
                    )
                    continue
                self.conversation.pop()
                raise
            except APIStatusError as e:
                if e.status_code == 429:
                    print("\nRate limited, waiting before retry...")
                    time.sleep(2**attempt)
                    continue
                elif e.status_code >= 500 and attempt < max_retries - 1:
                    continue
                print(f"\nAPI Error: {e.status_code} - {e.message}")
                self.conversation.pop()
                raise
            except APIError as e:
                print(f"\nAPI Error: {str(e)}")
                self.conversation.pop()
                raise

    def clear_history(self):
        """Clear conversation and file"""
        self.conversation = []
        self.history_file.unlink(missing_ok=True)
        print("History cleared")

    def show_history(self):
        """Display conversation history"""
        if not self.conversation:
            print("No conversation history")
            return

        print("\n--- Conversation History ---")
        for i, msg in enumerate(self.conversation, 1):
            role = msg["role"].capitalize()
            content = (
                msg["content"][:100] + "..."
                if len(msg["content"]) > 100
                else msg["content"]
            )
            print(f"{i}. {role}: {content}")
        print("--- End History ---\n")

    def run(self):
        """Run interactive REPL"""
        print("Claude REPL")
        print(
            "Commands: 'exit' to quit, 'clear' to reset history, 'history' to view history"
        )
        print()

        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() == "exit":
                    print("Goodbye!")
                    break
                elif user_input.lower() == "clear":
                    self.clear_history()
                    continue
                elif user_input.lower() == "history":
                    self.show_history()
                    continue
                elif not user_input:
                    continue

                print("Claude: ", end="", flush=True)
                self.chat_streaming(user_input)
                print()

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except APIError as e:
                print(f"Failed to get response: {e}\n")
            except Exception as e:
                print(f"Unexpected error: {e}\n")


if __name__ == "__main__":
    repl = ClaudeREPL(system_prompt="You are a helpful, thoughtful assistant.")
    repl.run()
