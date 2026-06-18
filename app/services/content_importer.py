import mimetypes
import os
import re
from html import escape
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from slugify import slugify

from app import db
from app.models import Certificate, MediaAsset, MediaRecognition, Page, PageSection, SiteSetting
from config import Config


SOURCE_BASE = Config.SOURCE_SITE_URL.rstrip("/")

PAGE_SOURCES = {
    "home": "/",
    "about-us": "/about-us",
    "contact-us": "/contact-us",
    "donate": "/donate",
    "certificates": "/our-certificates",
    "media-recognition": "/newspaper-recognition",
    "privacy-policy": "/privacy-policy",
    "refund-policy": "/cancellation-and-refund",
    "terms-and-conditions": "/terms-and-conditions",
}

UPLOAD_FOLDERS = [
    "logos",
    "certificates",
    "media-recognition",
    "gallery",
    "fundraisers",
    "volunteers",
    "reports",
]


def fetch_soup(path):
    url = urljoin(SOURCE_BASE + "/", path.lstrip("/"))
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser"), url


def fetch_first(paths):
    last_error = None
    for path in paths:
        try:
            return fetch_soup(path)
        except requests.RequestException as exc:
            last_error = exc
    raise last_error


def ensure_upload_folders():
    for folder in UPLOAD_FOLDERS:
        Path(Config.UPLOAD_ROOT, folder).mkdir(parents=True, exist_ok=True)


def upsert_setting(key, value):
    setting = SiteSetting.query.filter_by(key=key).first()
    if not setting:
        setting = SiteSetting(key=key, value=value or "")
        db.session.add(setting)
    elif value:
        setting.value = value
    return setting


def get_meta(soup, name):
    node = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
    return node.get("content", "").strip() if node else ""


def clean_text_items(soup):
    ignored = {
        "home",
        "about us",
        "our certificates",
        "newspaper-recognition",
        "donate",
        "terms and conditions",
        "privacy policy",
        "cancellation and refund",
        "shipping and exchange",
        "contact us",
        "follow us",
    }
    items = []
    for text in soup.stripped_strings:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized or normalized.lower() in ignored:
            continue
        if normalized not in items:
            items.append(normalized)
    return items


def page_content_from_soup(soup):
    paragraphs = clean_text_items(soup)
    return "\n".join(f"<p>{escape(item)}</p>" for item in paragraphs)


def upsert_page(slug, title, soup):
    page = Page.query.filter_by(slug=slug).first()
    meta_title = soup.title.string.strip() if soup.title and soup.title.string else title
    meta_description = get_meta(soup, "description")
    if not page:
        page = Page(slug=slug)
        db.session.add(page)
    page.title = title
    page.content = page_content_from_soup(soup)
    page.meta_title = meta_title
    page.meta_description = meta_description
    page.status = "published"
    return page


def title_from_slug(slug):
    titles = {
        "home": "It's that easy to bring a Smile on Their Faces",
        "about-us": "About Us",
        "contact-us": "Contact Us",
        "donate": "Donate",
        "certificates": "Our Certificates",
        "media-recognition": "Media Recognition",
        "privacy-policy": "Privacy Policy",
        "refund-policy": "Refund Policy",
        "terms-and-conditions": "Terms and Conditions",
    }
    return titles.get(slug, slug.replace("-", " ").title())


def extract_image_urls(soup):
    urls = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            urls.append((urljoin(SOURCE_BASE + "/", src), img.get("alt") or ""))
    return urls


def source_filename(url):
    parsed = urlparse(url)
    name = os.path.basename(parsed.path)
    if not name or "." not in name:
        name = f"asset-{abs(hash(url))}.jpg"
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    return name.lower()


def public_upload_path(folder, file_name):
    return f"/static/uploads/{folder}/{file_name}"


def download_asset(url, folder, title=None, alt_text="", uploaded_by="system-import"):
    ensure_upload_folders()
    file_name = source_filename(url)
    target = Path(Config.UPLOAD_ROOT, folder, file_name)
    public_path = public_upload_path(folder, file_name)

    if not target.exists():
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        target.write_bytes(response.content)

    file_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    asset = MediaAsset.query.filter_by(file_path=public_path).first()
    if not asset:
        asset = MediaAsset(
            title=title or Path(file_name).stem.replace("-", " ").title(),
            file_name=file_name,
            file_path=public_path,
            file_type=file_type,
            alt_text=alt_text or "",
            uploaded_by=uploaded_by,
        )
        db.session.add(asset)
    return asset


def import_branding():
    soup, _ = fetch_soup("/")
    logo_img = soup.find("img", alt=re.compile("logo", re.I)) or soup.find("img")
    if logo_img and logo_img.get("src"):
        logo = download_asset(urljoin(SOURCE_BASE + "/", logo_img["src"]), "logos", "NayePankh Foundation Logo", logo_img.get("alt", ""))
        upsert_setting("logo", logo.file_path)
        upsert_setting("favicon", logo.file_path)

    upsert_setting("site_name", get_meta(soup, "og:site_name") or "NayePankh Foundation")
    upsert_setting("registration_badge", "UP GOVERNMENT, 80G & 12A Registered NGO")
    upsert_setting("brand_primary_color", "#16813b")
    upsert_setting("brand_accent_color", "#f5b400")
    upsert_setting("typography_heading", "Poppins")
    upsert_setting("typography_body", "DM Sans")
    upsert_setting("footer_content", "All our efforts are made possible only because of your support")
    upsert_setting("contact_email", "contact@nayepankh.com")
    upsert_setting("contact_phone", "+91-8318500748")
    upsert_setting("office_address", "P Road, Kanpur- 208012")

    social_links = {
        "instagram_url": "instagram.com",
        "facebook_url": "facebook.com",
        "youtube_url": "youtube.com",
        "linkedin_url": "linkedin.com",
        "twitter_url": "twitter.com",
    }
    for setting_key, domain in social_links.items():
        link = soup.find("a", href=re.compile(domain, re.I))
        if link and link.get("href"):
            upsert_setting(setting_key, link["href"])


def import_pages():
    for slug, path in PAGE_SOURCES.items():
        soup, _ = fetch_soup(path)
        page = upsert_page(slug, title_from_slug(slug), soup)
        if not page.sections:
            intro = PageSection(
                page=page,
                name="Migrated Content",
                section_type="source-page",
                content=page.content,
                sort_order=1,
            )
            db.session.add(intro)
    db.session.commit()


def import_homepage():
    import_branding()
    soup, _ = fetch_soup("/")
    page = upsert_page("home", title_from_slug("home"), soup)
    first_non_logo = next(
        ((url, alt) for url, alt in extract_image_urls(soup) if "logo" not in alt.lower()),
        None,
    )
    if first_non_logo:
        hero = download_asset(first_non_logo[0], "gallery", "Homepage hero image", first_non_logo[1])
        upsert_setting("hero_image", hero.file_path)
    db.session.commit()
    return page


def import_about_page():
    soup, _ = fetch_soup("/about-us")
    page = upsert_page("about-us", "About Us", soup)
    db.session.commit()
    return page


def import_contact_page():
    soup, _ = fetch_first(["/contact-us", "/contact"])
    page = upsert_page("contact-us", "Contact Us", soup)
    upsert_setting("contact_email", "contact@nayepankh.com")
    upsert_setting("contact_phone", "+91-8318500748")
    upsert_setting("office_address", "P Road, Kanpur- 208012")
    db.session.commit()
    return page


def import_certificates():
    soup, _ = fetch_soup("/our-certificates")
    count = 0
    for index, (url, alt) in enumerate(extract_image_urls(soup), start=1):
        if "logo" in alt.lower():
            continue
        asset = download_asset(url, "certificates", f"Certificate {index}", alt)
        cert = Certificate.query.filter_by(image=asset.file_path).first()
        if not cert:
            cert = Certificate(
                title=asset.alt_text or asset.title,
                image=asset.file_path,
                certificate_type="registration",
            )
            db.session.add(cert)
            count += 1
    db.session.commit()
    return count


def import_media_recognition():
    soup, _ = fetch_soup("/newspaper-recognition")
    count = 0
    for index, (url, alt) in enumerate(extract_image_urls(soup), start=1):
        if "logo" in alt.lower():
            continue
        asset = download_asset(url, "media-recognition", f"Media Recognition {index}", alt)
        record = MediaRecognition.query.filter_by(image=asset.file_path).first()
        if not record:
            record = MediaRecognition(
                title=asset.alt_text or asset.title,
                image=asset.file_path,
                publication_name="Newspaper Recognition",
                category="newspaper",
            )
            db.session.add(record)
            count += 1
    db.session.commit()
    return count


def import_gallery_assets():
    count = 0
    for path in ["/", "/about-us", "/contact-us", "/donate"]:
        soup, _ = fetch_soup(path)
        for url, alt in extract_image_urls(soup):
            if "logo" in alt.lower():
                continue
            download_asset(url, "gallery", alt or Path(source_filename(url)).stem.replace("-", " ").title(), alt)
            count += 1
    db.session.commit()
    return count


def import_all():
    ensure_upload_folders()
    import_homepage()
    import_about_page()
    import_contact_page()
    import_pages()
    certificates = import_certificates()
    recognitions = import_media_recognition()
    gallery = import_gallery_assets()
    return {
        "pages": Page.query.count(),
        "settings": SiteSetting.query.count(),
        "certificates_imported": certificates,
        "media_recognition_imported": recognitions,
        "gallery_seen": gallery,
    }
