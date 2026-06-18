from datetime import datetime

from app import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Page(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False, default="")
    meta_title = db.Column(db.String(255), nullable=False, default="")
    meta_description = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(30), nullable=False, default="published")

    sections = db.relationship(
        "PageSection",
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="PageSection.sort_order",
    )


class PageSection(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("page.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    section_type = db.Column(db.String(80), nullable=False, default="content")
    content = db.Column(db.Text, nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    page = db.relationship("Page", back_populates="sections")


class SiteSetting(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False, default="")


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False, default="admin")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    volunteer_profile = db.relationship("VolunteerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class VolunteerProfile(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False, default="")
    city = db.Column(db.String(100), nullable=False, default="")
    date_of_birth = db.Column(db.Date, nullable=True)
    interests = db.Column(db.Text, nullable=False, default="")
    skills = db.Column(db.Text, nullable=False, default="")
    availability = db.Column(db.String(120), nullable=False, default="")
    motivation = db.Column(db.Text, nullable=False, default="")
    emergency_contact = db.Column(db.String(160), nullable=False, default="")
    status = db.Column(db.String(30), nullable=False, default="pending")
    hours_contributed = db.Column(db.Float, nullable=False, default=0)
    admin_notes = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="volunteer_profile")


class MediaAsset(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(80), nullable=False)
    alt_text = db.Column(db.String(255), nullable=False, default="")
    uploaded_by = db.Column(db.String(120), nullable=False, default="system-import")


class Certificate(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    issue_date = db.Column(db.Date, nullable=True)
    certificate_type = db.Column(db.String(120), nullable=False, default="registration")


class MediaRecognition(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    publication_name = db.Column(db.String(255), nullable=False, default="")
    publication_date = db.Column(db.Date, nullable=True)
    article_link = db.Column(db.String(500), nullable=False, default="")
    category = db.Column(db.String(120), nullable=False, default="newspaper")
