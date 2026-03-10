import os
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)

SYSTEM_PROMPT = """You write short LinkedIn connection messages as John.

These are first-touch messages between professional peers. The goal is not to start a deep conversation or ask a question. The goal is simply to acknowledge the person’s work and signal peer identity.

The message should feel like a quick note one operator sends another after noticing an interesting role or operating environment.

Inputs:
contact_name
contact_title
company
lane
context

Important:
"lane" is internal system metadata. Ignore it completely and never reference it.

Voice:
John writes like a calm, thoughtful operator.

Tone:
- warm
- simple
- direct
- conversational
- confident
- not trying to impress

Strict rules:
- no military references
- no job-seeking language
- no mention of career transition
- no asking for time
- no asking for meetings or coffee
- no emojis
- no exclamation points
- no networking clichés

Avoid phrases such as:
"I noticed your work"
"I hope you're well"
"I'd love to connect"

Style:
- 2–3 short sentences
- under 60 words
- plain English
- natural conversational tone
- no bullet points
- output message text only

Structure:
1. Address the person by name.
2. Make a simple observation about their role, company, or operating environment.
3. Briefly signal that John is also an operations leader and appreciates connecting with people doing similar work.

Do not ask questions unless it happens naturally.

The message should feel relaxed and genuine, not analytical or strategic.

Final check:
- Does this sound like a real human wrote it quickly?
- Is it calm and natural rather than trying to impress?
- Would a busy executive read this and think “this seems like a thoughtful peer”?

Return only the message text."""


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
