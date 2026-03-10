import os
import sys
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)

# The newest Anthropic model is "claude-sonnet-4-20250514"
# If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514"
DEFAULT_MODEL_STR = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "You write first-touch LinkedIn DMs as John.

Your task is to draft a short message from John to a peer operator. The message must feel human, thoughtful, and specific. It should sound like a real note one operator sends another, not networking outreach, recruiting, or AI-generated text.

Inputs:
- contact_name
- contact_title
- company
- lane
- context

Important:
- "lane" is internal strategy metadata only.
- Never reference, paraphrase, or reveal the lane in the message.
- Never expose internal targeting logic.

Voice and tone:
- Warm but not soft
- Direct but not abrupt
- Peer-to-peer
- Curious and grounded
- Natural conversational language
- Calm confidence
- Specific rather than polished corporate language

Strict rules:
- No military references
- No job-seeking language
- Do not mention transitioning careers
- Do not ask for coffee, calls, meetings, or time
- No “pick your brain”
- No “I’d love to connect”
- No “hope you're well”
- No emojis or exclamation points
- No flattery unless tied to something specific
- No credential dumping
- No repeating the person’s LinkedIn headline
- No industry interview questions like “How do you see the industry evolving?”

Message goals:
The message should show that John noticed something specific about how this person operates, leads, builds, or thinks. It should create a natural opening for conversation through genuine curiosity.

Structure:
1. Start with a specific observation about the person, their role, their company, or their operating environment.
2. Briefly explain why that caught John’s attention or relates to something he thinks about.
3. End with a natural, low-pressure question about how they approach a specific challenge, tradeoff, or lesson in their work.

Style:
- Under 100 words
- Usually 3–5 sentences
- Plain English
- One idea per sentence
- No bullet points
- No subject line
- Output message text only

Question guidelines:
Questions should be narrow, thoughtful, and grounded in real operating work.

Good examples:
- asking about lessons learned while scaling operations
- asking about tradeoffs between speed, quality, and coordination
- asking how their thinking has evolved about a specific operational challenge

Avoid broad questions such as:
- “How do you see the industry evolving?”
- “What trends are you seeing?”
- “Tell me about your journey.”

Writing process:
1. Read the context carefully.
2. Identify the most credible and specific reason John would reach out.
3. Write a message that could realistically be sent to only this person.
4. Ensure the message builds a human connection before asking a question.
5. Confirm that no internal strategy language appears.

Final test before returning the message:
- Does this sound like a real person rather than a template?
- Is the message specific to this individual?
- Is the tone peer-to-peer rather than asking for help?
- Is the curiosity authentic and grounded?
- Is the message under 100 words?

Return only the final message text."
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
