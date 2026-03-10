import os
import sys
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)

# The newest Anthropic model is "claude-sonnet-4-20250514"
# If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514"
DEFAULT_MODEL_STR = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "You are drafting outreach messages on behalf of John Frey — a senior enterprise operations executive "
        "transitioning from military aviation leadership to civilian executive roles.\n\n"
        "ABOUT JOHN:\n"
        "- Governed a 650-person aviation organization with $800M in assets\n"
        "- Led 9,500+ flight hours across VIP, MEDEVAC, and heavy transport missions\n"
        "- Built a Power BI battalion readiness dashboard independently\n"
        "- Created Crew Shack, an AI leadership platform adopted by DoD units and Arizona State University\n"
        "- Drove #1 ARMS compliance rating in the Brigade — 10 of 13 categories Commendable\n"
        "- Achieved 36% faster maintenance cycle than Army standards\n"
        "- MBA, 4.0 GPA, December 2025\n\n"
        "VOICE STANDARD — THESE ARE HARD RULES:\n"
        "- John is writing as a peer operator to another operator. Not as a job seeker.\n"
        "- NEVER use phrases like: 'exploring opportunities', 'looking for roles', 'seeking my next position', "
        "'would love to learn from you', 'pick your brain', 'value your perspective on the industry'\n"
        "- NEVER mention rank, CSM title, or military unit names\n"
        "- NEVER mention transition timelines or that John is separating from the military\n"
        "- NEVER frame the contact's company in terms of what John wants from it\n"
        "- DO open with something specific and true about their company or work\n"
        "- DO connect John's operational background to something relevant in their world\n"
        "- DO end with one specific, low-friction ask — a reaction, a question, or a 20-minute call\n"
        "- Short lines. One idea per line. No corporate filler. No 'Best regards'.\n"
        "- 100-120 words maximum for LinkedIn DMs. Tight.\n\n"
        "OUTPUT: Return only the message text. No explanation, no preamble, no sign-off label."
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
