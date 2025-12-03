import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()


import openai
from agent_wrapper.recorder import record_capsule

client = openai.OpenAI()  # Uses OPENAI_API_KEY from env

# NOTE: To use this, set OPENAI_API_KEY in your environment or configure openai.api_key


def ask_gpt(
    prompt,
    capsule_type="Introspective",
    model="gpt-4",
    metadata=None,
    parent_capsule_id=None,
):
    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    output = response.choices[0].message.content
    # For MVP, reasoning_trace is just the prompt and output; can be expanded
    reasoning_trace = [f"Prompt: {prompt}", f"Output: {output}"]
    confidence = 0.9  # Default confidence value for introspective capsules
    capsule_id = record_capsule(
        capsule_type=capsule_type,
        confidence=confidence,
        reasoning_trace=reasoning_trace,
        metadata=metadata or {},
        previous_capsule_id=parent_capsule_id,
    )
    return output, capsule_id


if __name__ == "__main__":
    load_dotenv()
    print("UATP Capsule Engine GPT Wrapper (type 'exit' to quit)")
    parent_capsule_id = None
    while True:
        try:
            prompt = input("Enter your prompt: ")
            if prompt.strip().lower() == "exit":
                print("Exiting.")
                break
            response, capsule_id = ask_gpt(prompt, parent_capsule_id=parent_capsule_id)
            print(f"GPT: {response}\nCapsule ID: {capsule_id}\n")
            parent_capsule_id = capsule_id
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"Error: {e}\n")
