import os
import sys
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)

# The newest Anthropic model is "claude-sonnet-4-20250514"
# If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514"
DEFAULT_MODEL_STR = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "You are drafting LinkedIn outreach messages for John Frey, a senior enterprise "
    "operations executive. He is writing peer-to-peer, not as a job seeker. Never "
    "mention rank, military titles, transition timelines, or that he is looking for a "
    "role. No corporate filler. Short lines, one idea per line, 100-150 words max. "
    "End with a specific low-friction ask. Return only the message text."
)


def get_anthropic_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable must be set")
    return Anthropic(api_key=api_key)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/generate-outreach", methods=["POST"])
def generate_outreach():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    required_fields = [
        "contact_name",
        "contact_title",
        "company",
        "lane",
        "message_type",
        "context",
    ]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    user_prompt = (
        f"Write a {data['message_type']} LinkedIn message to {data['contact_name']}, "
        f"{data['contact_title']} at {data['company']}.\n"
        f"Lane/topic: {data['lane']}\n"
        f"Context: {data['context']}"
    )

    try:
        client = get_anthropic_client()
        response = client.messages.create(
            model=DEFAULT_MODEL_STR,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        generated_text = response.content[0].text
        return jsonify({"message": generated_text})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Anthropic API error: {str(e)}"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
