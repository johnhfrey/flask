import os
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)

SYSTEM_PROMPT = """You write short LinkedIn connection messages as John.

These are first-touch messages sent between professional peers. The purpose is not to start a deep conversation or ask for time. The goal is simply to acknowledge someone's work and signal peer identity.

The message should feel like a quick, genuine note one operator sends another after noticing an interesting role or operating environment.

Inputs:
contact_name
contact_title
company
lane
context

Important:
The field "lane" is internal metadata used by the system.
Ignore it completely and never reference it in the message.

Voice:
John writes like a calm, thoughtful operations leader.

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
- no asking for meetings, calls, or coffee
- no asking for time
- no emojis
- no exclamation points
- no networking clichés
- no industry analysis
- no explaining the person's business

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
- no sign-offs like "Best" or "John"
- output message text only

Structure:
1. Address the person by name.
2. Use one natural observation about their role or company.
3. Briefly signal that John is also an operations leader and appreciates connecting with people doing similar work.

Opener variation rule:
Rotate between the following three opener styles so messages do not appear automated.

Pattern 1:
"{Name}, your role leading operations at {Company} caught my attention."

Pattern 2:
"{Name}, {Company} seems like a fascinating operating environment."

Pattern 3:
"{Name}, running operations in a business like {Company} must be an interesting seat."

Use one of these patterns naturally at the beginning of the message.

Final check before returning the message:
- Does this sound like a real human wrote it quickly?
- Is the tone relaxed rather than analytical?
- Does it signal peer identity without asking for anything?

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
@app.route("/score-contact", methods=["POST"])
def score_contact():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    required_fields = ["contact_name", "contact_title", "company", "lane"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    scoring_prompt = """You are scoring a contact for John Frey's transition campaign.

John is targeting Senior Director or VP Operations roles. His Offer A criteria:
- Stable company culture with trusted leadership
- Real P&L or operational accountability
- $150K+ W2 minimum
- Predictable work cadence
- Based in Florida (Jacksonville preferred) or Southeast
- Industries: aviation, logistics, defense, maritime, or any stable well-led company

Score this contact 1-10 based on:
- Title alignment (VP/Director/COO/GM = high, recruiter/coordinator = low)
- Company stability and size (established company = high, startup/unknown = low)
- Lane relevance (T1 Aviation, T2 Business, T3 Defense = high, Recruiter = medium)
- Geographic fit (Florida/Southeast = high, remote possible = medium, locked elsewhere = low)

Return ONLY a JSON object in this exact format with no other text:
{"score": 8, "notes": "One sentence explanation of the score."}"""

    user_prompt = (
        f"Score this contact:\n"
        f"Name: {data['contact_name']}\n"
        f"Title: {data['contact_title']}\n"
        f"Company: {data['company']}\n"
        f"Lane: {data['lane']}\n"
        f"Context: {data.get('context', 'None provided')}"
    )

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return jsonify({"error": "ANTHROPIC_API_KEY not configured"}), 500
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            system=scoring_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        import json
        result = json.loads(response.content[0].text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
