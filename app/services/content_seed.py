from app import db
from app.models import Page, PageSection, SiteSetting


CURATED_PAGES = {
    "home": {
        "title": "Bring a Smile to Someone's Life",
        "meta_title": "NayePankh Foundation | UP Govt. 80G & 12A Registered NGO",
        "meta_description": (
            "NayePankh Foundation is a student-led, UP Government, 80G and 12A "
            "registered NGO working to uplift underprivileged communities."
        ),
        "content": """
<p>NayePankh Foundation is a UP Government, 80G and 12A registered NGO working with students and volunteers to support underprivileged communities.</p>
<p>We believe meaningful change can begin with simple acts: a meal, a book, a sanitary pad, a warm piece of clothing, a mentor, or a few hours of service.</p>
<p>Your money, skills, time and voice can help us reach more families with dignity and care.</p>
""".strip(),
        "sections": [
            (
                "What We Do",
                "impact",
                """
<p>Our work focuses on practical support for people who need it most. NayePankh volunteers contribute through food distribution, education support, hygiene awareness, clothes donation drives and community outreach.</p>
<p>Each campaign is built around a direct need on the ground, so support reaches people in a useful and respectful way.</p>
""".strip(),
                1,
            ),
            (
                "Join Our Team",
                "volunteer",
                """
<p>NayePankh is powered by students, volunteers and supporters who want to create positive change. Whether you care about education, health, fundraising, outreach or field work, there is a role for you.</p>
<p>If we all do something, together there is no problem we cannot solve.</p>
""".strip(),
                2,
            ),
        ],
    },
    "about-us": {
        "title": "About NayePankh Foundation",
        "meta_title": "About NayePankh Foundation",
        "meta_description": "Learn about NayePankh Foundation, a student-led NGO working for underprivileged communities.",
        "content": """
<p>NayePankh Foundation is a non-governmental organisation with a strong desire to make society more compassionate, equal and hopeful.</p>
<p>The organisation began with a simple belief: service to mankind is service to God. That belief continues to guide every drive, campaign and volunteer effort.</p>
""".strip(),
        "sections": [
            (
                "How It Started",
                "story",
                """
<p>During the difficult years around the COVID-19 pandemic, many families struggled for food, education, healthcare and basic necessities. NayePankh began by doing whatever was possible with the resources available.</p>
<p>That spirit grew into a student-led movement working across Kanpur, Ghaziabad and other cities.</p>
""".strip(),
                1,
            ),
            (
                "Our Approach",
                "mission",
                """
<p>We think global and act local. Every campaign is designed around real community needs and delivered through volunteers who understand the value of direct, humane action.</p>
<p>Our aim is not only to provide support, but also to build confidence, dignity and opportunity.</p>
""".strip(),
                2,
            ),
        ],
    },
    "contact-us": {
        "title": "Contact Us",
        "meta_title": "Contact NayePankh Foundation",
        "meta_description": "Contact NayePankh Foundation by email, phone, or at the Kanpur office.",
        "content": """
<p>We appreciate your interest in NayePankh Foundation. Reach out for donations, volunteering, collaborations, media enquiries or general questions.</p>
<p><strong>Email:</strong> contact@nayepankh.com<br><strong>Phone:</strong> +91-8318500748<br><strong>Address:</strong> 104A/279, P Road, Kanpur</p>
""".strip(),
        "sections": [
            (
                "Get In Touch",
                "contact",
                """
<p>For the fastest response, email us directly or call the team. You can also connect with us on Instagram, Facebook, LinkedIn and YouTube through the footer links.</p>
""".strip(),
                1,
            ),
        ],
    },
    "donate": {
        "title": "Donate to NayePankh Foundation",
        "meta_title": "Donate | NayePankh Foundation",
        "meta_description": "Support NayePankh Foundation's work for underprivileged communities.",
        "content": """
<p>Together, let's make a difference. Your contribution helps NayePankh Foundation support children, families and communities with education, food, hygiene and essential care.</p>
<p>Donations are eligible for tax exemption under 80G of the Indian Income Tax Act.</p>
""".strip(),
        "sections": [
            (
                "How Your Support Helps",
                "donation",
                """
<p>Every contribution strengthens field campaigns, community drives, education support, hygiene initiatives and emergency assistance. You can support with money, supplies, skills, professional services or volunteer time.</p>
""".strip(),
                1,
            ),
        ],
    },
    "certificates": {
        "title": "Our Certificates",
        "meta_title": "Certificates | NayePankh Foundation",
        "meta_description": "View NayePankh Foundation registration and compliance certificates.",
        "content": "<p>View our registration and compliance documents. These records are managed through the CMS and can be updated from the admin panel.</p>",
        "sections": [],
    },
    "media-recognition": {
        "title": "Media Recognition",
        "meta_title": "Media Recognition | NayePankh Foundation",
        "meta_description": "News and media recognition for NayePankh Foundation.",
        "content": "<p>Coverage and recognition from newspapers and media outlets are collected here and managed through the admin panel.</p>",
        "sections": [],
    },
}


CURATED_SETTINGS = {
    "footer_content": "All our efforts are made possible because of your support.",
    "office_address": "104A/279, P Road, Kanpur",
    "homepage_support_line": "Money, skill or time: every contribution can become someone's reason to smile.",
}


def upsert_curated_content():
    for key, value in CURATED_SETTINGS.items():
        setting = SiteSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            db.session.add(SiteSetting(key=key, value=value))

    for slug, data in CURATED_PAGES.items():
        page = Page.query.filter_by(slug=slug).first()
        if not page:
            page = Page(slug=slug)
            db.session.add(page)
        page.title = data["title"]
        page.content = data["content"]
        page.meta_title = data["meta_title"]
        page.meta_description = data["meta_description"]
        page.status = "published"

        PageSection.query.filter_by(page=page).delete()
        db.session.flush()
        for name, section_type, content, sort_order in data["sections"]:
            db.session.add(
                PageSection(
                    page=page,
                    name=name,
                    section_type=section_type,
                    content=content,
                    sort_order=sort_order,
                    is_active=True,
                )
            )

    db.session.commit()
