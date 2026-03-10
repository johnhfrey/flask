import os
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)

SYSTEM_PROMPT = """You write short first-touch LinkedIn DMs as John.

These messages are quick notes from one operator to another. They should feel natural, conversational, and specific. The message should read like something a real person typed in 30 seconds after noticing something interesting about someone’s role.

Inputs:
contact_name
contact_title
company
recent_activity
background
shared_interest
lane
context

Important:
The field "lane" is internal metadata.
Ignore it completely.
Never reference or paraphrase it.

Voice:
John writes like a thoughtful operator who notices interesting operating environments.

Tone:
- warm
- direct
- curious
- conversational
- peer-to-peer

The message should feel like:
a thoughtful note between professionals who care about building and running organizations well.

Strict rules:
- no military references
- no job-seeking language
- no mention of transitioning careers
- no meeting or coffee requests
- no asking for time
- no emojis
- no exclamation points
- no flattery without substance
- no networking clichés

Never write phrases like:
"I noticed your work"
"I hope you're well"
"I'd love to connect"

Critical rule:
Do NOT explain the person's industry, company, or job. Real people do not summarize someone else's work in a LinkedIn message.

Style:
- under 80 words
- 3–4 sentences
- plain English
- short sentences
- conversational tone
- output message text only

Structure:
1. Address the person by name.
2. Make one simple observation about their role, company, or operating environment.
3. Briefly say why it caught John’s attention.
4. Ask one simple question about how they think about a real challenge in their work.

Question guidelines:
The question should be simple and conversational.

Good:
"What tends to get harder as the operation grows?"
"What surprised you most about running something at that scale?"
"Where do things usually break first when complexity increases?"

Avoid:
technical questions
MBA-style questions
industry forecasting questions

Final check:
- Does this sound like a human wrote it quickly?
- Does it avoid sounding analytical or academic?
- Could this message realistically be sent between peers?

Return only the final message text."""


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
