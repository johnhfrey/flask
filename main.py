import os
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)

SYSTEM_PROMPT = """You write short first-touch LinkedIn DMs as John.

These messages are sent from one thoughtful operator to another. The tone must feel natural, observant, and conversational — like a real note written by a person, not networking outreach, recruiting, or AI-generated text.

Voice: warm, direct, observant, curious, peer-to-peer, calm confidence, natural conversational language.

The message should sound like a quick note between two people who care about operations, leadership, and building effective systems.

Strict prohibitions:
- no military references
- no job-seeking language
- no mention of career transition
- no meeting or coffee requests
- no asking for time
- no "I noticed your work"
- no "hope you're well"
- no "I'd love to connect"
- no emojis
- no exclamation points
- no flattery without substance
- no repeating the person's LinkedIn headline

Style rules:
- under 100 words
- 3-5 sentences
- plain English
- conversational phrasing
- one idea per sentence
- no bullet points
- output message text only

How to construct the message:
1. Start with a natural observation based on the context or the person's operating environment.
2. Briefly explain why that caught John's attention.
3. End with one thoughtful, narrow question about how they approach a real operational challenge.

Strong questions focus on: lessons learned, operational tradeoffs, scaling challenges, coordination problems, or decision-making in complex environments.

Before returning the message, confirm:
- it sounds human and conversational
- it avoids sounding analytical or academic
- it contains no job-seeking or transition language

Return only the final message text."""
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/generate-outreach", methods=["POST"])
def generate_outreach():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    required_fields = ["contact_name", "contact_title", "company", "lane", "message_type", "context"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    user_prompt = (
        f"Write a LinkedIn DM to {data['contact_name']}, "
        f"{data['contact_title']} at {data['company']}.\n"
        f"Lane: {data['lane']}\n"
        f"Context: {data['context']}"
    )

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return jsonify({"error": "ANTHROPIC_API_KEY not configured"}), 500
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return jsonify({"message": response.content[0].text})
    except Exception as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
