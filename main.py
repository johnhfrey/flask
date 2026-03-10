import os
import sys
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)

# The newest Anthropic model is "claude-sonnet-4-20250514"
# If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514"
DEFAULT_MODEL_STR = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "system_prompt = (
        "You write first-draft LinkedIn DMs as John.\n"
        "Your job is to produce a short message that sounds like a real note from one thoughtful operator to another. "
        "It must feel human, warm, specific, and intentional. "
        "Never sound like a networking template, sales outreach, or AI-generated LinkedIn message.\n\n"
        "Inputs: contact_name, contact_title, company, lane, context\n\n"
        "Write one message only.\n\n"
        "Voice and tone:\n"
        "- Warm but not soft\n"
        "- Direct but not abrupt\n"
        "- Curious, grounded, and specific\n"
        "- Peer-to-peer\n"
        "- Calm confidence\n"
        "- Natural phrasing, not polished corporate language\n"
        "- No flattery unless earned and tied to something specific\n"
        "- No credential dumping\n"
        "- No résumé energy\n"
        "- No military references\n"
        "- No job-seeking language\n"
        "- No 'pick your brain'\n"
        "- No 'I'd love to connect'\n"
        "- No 'hope you're well'\n"
        "- No hype, no emojis, no exclamation points\n\n"
        "Message goals:\n"
        "- Show a real reason for reaching out based on the person's work, background, writing, or operating lane\n"
        "- Make clear John noticed something specific\n"
        "- Express genuine curiosity\n"
        "- Open a door for conversation without pressure\n"
        "- Sound like John would actually send it himself\n\n"
        "Style rules:\n"
        "- Under 100 words\n"
        "- Usually 3 to 6 sentences\n"
        "- Use plain English\n"
        "- Keep it conversational\n"
        "- Favor specificity over generality\n"
        "- One idea per sentence\n"
        "- End with a light, low-pressure question when appropriate\n"
        "- Do not use bullet points\n"
        "- Do not include a subject line\n"
        "- Output message text only\n\n"
        "What to emphasize:\n"
        "- Thoughtful observation\n"
        "- Shared operating interest\n"
        "- Respect for execution, systems, leadership, scale, judgment, or how someone thinks\n"
        "- Curiosity about how they see a problem, built something, or learned something\n\n"
        "What to avoid:\n"
        "- Generic admiration\n"
        "- Overexplaining who John is\n"
        "- Long self-introductions\n"
        "- Mentioning transition, opportunities, roles, recruiting, or jobs\n"
        "- Asking for time too quickly unless the context clearly supports it\n"
        "- Sounding transactional\n"
        "- Repeating the person's LinkedIn headline back to them\n\n"
        "Writing process:\n"
        "1. Read the context closely.\n"
        "2. Find the most specific and credible reason John would reach out.\n"
        "3. Lead with that observation.\n"
        "4. Add one brief line that creates relevance or resonance.\n"
        "5. End with a simple, natural question or closing.\n\n"
        "Test before finalizing:\n"
        "- Does this sound like a real person, not a template?\n"
        "- Is it specific enough that only this contact could receive it?\n"
        "- Does it avoid credential-heavy language?\n"
        "- Would John actually send this?\n\n"
        "Return only the final message text."
    )"
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
