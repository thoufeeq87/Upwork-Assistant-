"""
Sole integration point with the Anthropic API. Every Claude call in this
project goes through the two functions below.
"""

import base64
import json

import anthropic
from django.conf import settings

HOOKS_SCHEMA = {
    "type": "object",
    "properties": {
        "hooks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["hooks"],
    "additionalProperties": False,
}


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _image_blocks(screenshots) -> list[dict]:
    blocks = []
    for shot in screenshots:
        shot.image.open("rb")
        try:
            data = base64.standard_b64encode(shot.image.read()).decode("utf-8")
        finally:
            shot.image.close()
        media_type = "image/png" if shot.image.name.lower().endswith("png") else "image/jpeg"
        blocks.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": data},
            }
        )
    return blocks


def generate_hooks(job, framework, screenshots, count: int = 10) -> tuple[list[str], dict]:
    """Ask Claude for `count` opening-hook options from the job screenshots.

    `screenshots` must already be ordered (JobScreenshot.order). Returns
    (hook_texts, raw_response_dict).
    """
    content = _image_blocks(screenshots)
    content.append(
        {
            "type": "text",
            "text": (
                f"{framework.prompt_template}\n\n"
                f"Job title: {job.title}\n"
                f"Job snippet: {job.snippet_text}\n\n"
                f"Generate {count} distinct hook (opening line) options for an Upwork "
                f"proposal, based on the job description visible in the screenshot(s) above."
            ),
        }
    )

    response = _client().messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": HOOKS_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    hooks = json.loads(text)["hooks"]
    return hooks, response.to_dict()


def generate_proposal(job, hook_text: str, template) -> tuple[str, dict]:
    """Expand a chosen hook into a full proposal using the user's template. Text-only."""
    prompt = (
        f"{template.template_text}\n\n"
        f"Job title: {job.title}\n"
        f"Job snippet: {job.snippet_text}\n"
        f"Chosen hook (opening line): {hook_text}\n\n"
        f"Write the full Upwork proposal, starting with the hook above."
    )

    response = _client().messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(b.text for b in response.content if b.type == "text")
    return text, response.to_dict()
