from django.db import migrations

HOOK_FRAMEWORK_PROMPT = """As a beginner with no reviews, I need an attention-grabbing opening for my proposal that will stand out in a sea of generic applications. The client will see the first 1-2 sentences in their application list before deciding whether to open my full proposal.

Please write 10 different powerful opening hooks (2-3 sentences each) that:

1. Immediately grab attention with pattern interruption
2. Speak to the client's DEEPER desires (the REAL desires hiding beneath the task)
3. Address potential concerns/resistance they might have
4. Include one colorful emoji near the beginning (for visual pattern interruption)
5. Are personalized to this specific job
6. Avoid generic greetings like "Hello" or "Thanks for posting"
7. Use various hook techniques (curiosity, stats, questions, bold claims, etc.)
8. Make the client want to click "read more"
9. Make every word count – no wasted space or fluff

Each opening should be unique and compelling, focusing on different aspects of what the client REALLY wants from this project. Base this on the job screenshot(s) provided above, plus the title and snippet given below."""

PROPOSAL_TEMPLATE_TEXT = """You are helping a new freelancer craft an engaging, effective proposal for simple one-off jobs like surveys, feedback, testing, and other flat-fee tasks. These proposals need to be short, friendly, and designed to help beginners land their first clients and earn those crucial 5-star reviews.

Start with the chosen opening hook provided below (do not write a new one — expand on it). Use simple everyday language, be punchy and attention-grabbing.

Then write: "I can deliver exactly what you need because:" Follow with three concise bullet points:
👉 A Reliability Statement
👉 A Speed/Efficiency Statement
👉 A Quality/Attention Statement

Include this verbatim: "While I'm new to Upwork, I bring my full commitment to delivering excellent work. I understand that your 5-star review will help launch my freelance career, so I'll go above and beyond to ensure you're completely satisfied."

Add a simple offer: "I can start immediately and deliver within [realistic timeframe]. If you're not 100% satisfied with my work, I'll revise until you are."

End with a friendly closing that invites a response.

Include a P.S. mentioning your specific availability (same-day, weekends, etc.) to create urgency.

Here's an example of what this looks like for an unrelated niche/freelancer/listing:

Ready to get that spreadsheet populated without the headache? ✅ I'll handle your data entry task with speed, accuracy, and zero drama.

I can deliver exactly what you need because:
👉 I'll enter your data with 100% accuracy - no errors or inconsistencies
👉 I'll complete the entire project within the timeframe you specified - guaranteed
👉 I'll organize and format everything for maximum readability - not just raw data

While I'm new to Upwork, I bring my full commitment to delivering excellent work. I understand that your 5-star review will help launch my freelance career, so I'll go above and beyond to ensure you're completely satisfied.

I can begin working on your project immediately and will deliver within your specified deadline. If you notice any errors or issues with my work, I'll correct them right away at no additional cost.

Ready to check this task off your list?

Michael

P.S. I have availability today and can prioritize your project if you need it completed ASAP."""


def seed_templates(apps, schema_editor):
    HookFramework = apps.get_model("proposals", "HookFramework")
    ProposalTemplate = apps.get_model("proposals", "ProposalTemplate")

    HookFramework.objects.get_or_create(
        name="Default: 10-hook attention grabber",
        defaults={
            "description": "Generates 10 distinct opening hooks per job, aimed at a beginner freelancer with no reviews.",
            "prompt_template": HOOK_FRAMEWORK_PROMPT,
            "is_active": True,
        },
    )

    ProposalTemplate.objects.get_or_create(
        name="Default: Beginner-friendly one-off job proposal",
        defaults={
            "category": "General / one-off tasks",
            "template_text": PROPOSAL_TEMPLATE_TEXT,
            "is_active": True,
        },
    )


def unseed_templates(apps, schema_editor):
    HookFramework = apps.get_model("proposals", "HookFramework")
    ProposalTemplate = apps.get_model("proposals", "ProposalTemplate")
    HookFramework.objects.filter(name="Default: 10-hook attention grabber").delete()
    ProposalTemplate.objects.filter(name="Default: Beginner-friendly one-off job proposal").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("proposals", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]
