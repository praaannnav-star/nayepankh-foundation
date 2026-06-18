import csv
import io
import mimetypes
from datetime import datetime
from pathlib import Path

from flask import Blueprint, Response, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from app import db
from app.auth import admin_required, current_user, current_volunteer, hash_password, role_required, verify_password, volunteer_required
from app.models import (
    Certificate,
    MediaAsset,
    MediaRecognition,
    Page,
    PageSection,
    SiteSetting,
    User,
    VolunteerProfile,
)


bp = Blueprint("main", __name__)


def settings_dict():
    return {item.key: item.value for item in SiteSetting.query.all()}


def save_upload(field_name, folder, title=None, alt_text=""):
    uploaded = request.files.get(field_name)
    if not uploaded or not uploaded.filename:
        return ""
    upload_dir = Path(current_app.config["UPLOAD_ROOT"], folder)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_name = secure_filename(uploaded.filename)
    target = upload_dir / file_name
    uploaded.save(target)
    public_path = f"/static/uploads/{folder}/{file_name}"
    asset = MediaAsset.query.filter_by(file_path=public_path).first()
    if not asset:
        asset = MediaAsset(
            title=title or Path(file_name).stem.replace("-", " ").replace("_", " ").title(),
            file_name=file_name,
            file_path=public_path,
            file_type=mimetypes.guess_type(file_name)[0] or "application/octet-stream",
            alt_text=alt_text,
            uploaded_by="admin",
        )
        db.session.add(asset)
    return public_path


@bp.context_processor
def inject_site_settings():
    return {"site": settings_dict(), "admin_user": current_user(), "volunteer_user": current_volunteer()}


@bp.route("/healthz")
def healthz():
    return {"status": "ok"}


@bp.route("/")
def home():
    page = Page.query.filter_by(slug="home", status="published").first()
    if not page:
        return redirect(url_for("main.admin_dashboard"))
    certificates = Certificate.query.order_by(Certificate.created_at.desc()).limit(6).all()
    recognitions = MediaRecognition.query.order_by(MediaRecognition.created_at.desc()).limit(6).all()
    gallery = MediaAsset.query.filter(MediaAsset.file_path.like("%/gallery/%")).limit(9).all()
    return render_template(
        "page.html",
        page=page,
        certificates=certificates,
        recognitions=recognitions,
        gallery=gallery,
        is_home=True,
    )


@bp.route("/certificates")
@bp.route("/our-certificates")
def certificates():
    page = Page.query.filter_by(slug="certificates", status="published").first()
    items = Certificate.query.order_by(Certificate.created_at.desc()).all()
    return render_template("certificates.html", page=page, items=items)


@bp.route("/media-recognition")
@bp.route("/newspaper-recognition")
def media_recognition():
    page = Page.query.filter_by(slug="media-recognition", status="published").first()
    items = MediaRecognition.query.order_by(MediaRecognition.created_at.desc()).all()
    return render_template("media_recognition.html", page=page, items=items)


@bp.route("/<slug>")
def cms_page(slug):
    alias_map = {
        "about-us": "about-us",
        "contact-us": "contact-us",
        "privacy-policy": "privacy-policy",
        "refund-policy": "refund-policy",
        "cancellation-and-refund": "refund-policy",
        "terms-and-conditions": "terms-and-conditions",
        "donate": "donate",
    }
    page_slug = alias_map.get(slug, slug)
    page = Page.query.filter_by(slug=page_slug, status="published").first_or_404()
    return render_template("page.html", page=page)


@bp.route("/admin")
@admin_required
def admin_dashboard():
    counts = {
        "pages": Page.query.count(),
        "media": MediaAsset.query.count(),
        "certificates": Certificate.query.count(),
        "recognitions": MediaRecognition.query.count(),
        "settings": SiteSetting.query.count(),
        "users": User.query.count(),
        "volunteers": User.query.filter_by(role="volunteer").count(),
    }
    return render_template("admin/dashboard.html", counts=counts)


@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user():
        return redirect(url_for("main.admin_dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if verify_password(user, password):
            session.clear()
            session["admin_user_id"] = user.id
            flash("Logged in.")
            return redirect(request.args.get("next") or url_for("main.admin_dashboard"))
        flash("Invalid email or password.")
    return render_template("admin/login.html")


@bp.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("main.admin_login"))


@bp.route("/volunteer/login", methods=["GET", "POST"])
def volunteer_login():
    if current_volunteer():
        return redirect(url_for("main.volunteer_dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, role="volunteer").first()
        if verify_password(user, password):
            session.clear()
            session["volunteer_user_id"] = user.id
            flash("Logged in.")
            return redirect(request.args.get("next") or url_for("main.volunteer_dashboard"))
        flash("Invalid email or password.")
    return render_template("volunteer/login.html")


@bp.route("/volunteer/signup", methods=["GET", "POST"])
def volunteer_signup():
    if current_volunteer():
        return redirect(url_for("main.volunteer_dashboard"))
    
    is_first_user = False
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not name or not email or not password:
            flash("All fields are required.")
            return render_template("volunteer/signup.html", is_first_user=is_first_user)
        
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("volunteer/signup.html", is_first_user=is_first_user)
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return render_template("volunteer/signup.html", is_first_user=is_first_user)
        
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="volunteer",
            is_active=True
        )
        db.session.add(user)
        db.session.flush()
        profile = VolunteerProfile(user=user, phone=request.form.get("phone", "").strip(), city=request.form.get("city", "").strip(), interests=request.form.get("interests", "").strip(), availability=request.form.get("availability", "").strip(), motivation=request.form.get("motivation", "").strip())
        db.session.add(profile)
        db.session.commit()
        flash("Registration received. Welcome to NayePankh!")
        session.clear()
        session["volunteer_user_id"] = user.id
        return redirect(url_for("main.volunteer_dashboard"))
    
    return render_template("volunteer/signup.html", is_first_user=is_first_user)


@bp.route("/volunteer/dashboard")
@volunteer_required
def volunteer_dashboard():
    volunteer = current_volunteer()
    return render_template("volunteer/dashboard.html", volunteer=volunteer)


@bp.route("/volunteer/profile", methods=["GET", "POST"])
@volunteer_required
def volunteer_profile():
    volunteer = current_volunteer()
    profile = volunteer.volunteer_profile or VolunteerProfile(user=volunteer)
    if request.method == "POST":
        volunteer.name = request.form.get("name", "").strip() or volunteer.name
        for field in ("phone", "city", "interests", "skills", "availability", "motivation", "emergency_contact"):
            setattr(profile, field, request.form.get(field, "").strip())
        db.session.add(profile)
        db.session.commit()
        flash("Profile updated.")
        return redirect(url_for("main.volunteer_dashboard"))
    return render_template("volunteer/profile.html", volunteer=volunteer, profile=profile)


@bp.route("/admin/volunteers")
@admin_required
def admin_volunteers():
    volunteers = User.query.filter_by(role="volunteer").order_by(User.created_at.desc()).all()
    return render_template("admin/volunteers.html", volunteers=volunteers)


@bp.post("/admin/volunteers/<int:user_id>/status")
@admin_required
def admin_volunteer_status(user_id):
    user = User.query.filter_by(id=user_id, role="volunteer").first_or_404()
    profile = user.volunteer_profile or VolunteerProfile(user=user)
    profile.status = request.form.get("status", "pending") if request.form.get("status") in {"pending", "approved", "inactive"} else "pending"
    profile.hours_contributed = max(0, float(request.form.get("hours_contributed") or 0))
    profile.admin_notes = request.form.get("admin_notes", "").strip()
    db.session.add(profile)
    db.session.commit()
    flash("Volunteer record updated.")
    return redirect(url_for("main.admin_volunteers"))


@bp.get("/admin/volunteers/report.csv")
@admin_required
def volunteer_report():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Phone", "City", "Interests", "Availability", "Status", "Hours", "Registered"])
    for user in User.query.filter_by(role="volunteer").order_by(User.created_at.desc()):
        p = user.volunteer_profile
        writer.writerow([user.name, user.email, p.phone if p else "", p.city if p else "", p.interests if p else "", p.availability if p else "", p.status if p else "pending", p.hours_contributed if p else 0, user.created_at.date().isoformat()])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=volunteers.csv"})


@bp.get("/api/volunteers/me")
@volunteer_required
def api_volunteer_me():
    user = current_volunteer()
    p = user.volunteer_profile
    return jsonify({"id": user.id, "name": user.name, "email": user.email, "status": p.status if p else "pending", "hours_contributed": p.hours_contributed if p else 0, "interests": p.interests if p else ""})


@bp.post("/volunteer/logout")
@volunteer_required
def volunteer_logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("main.volunteer_login"))


@bp.route("/admin/users")
@role_required("admin")
def admin_users():
    users = User.query.order_by(User.email).all()
    return render_template("admin/users.html", users=users)


@bp.route("/admin/users/new", methods=["GET", "POST"])
@bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def admin_user_form(user_id=None):
    user = User.query.get(user_id) if user_id else User(role="editor", is_active=True)
    if user_id and not user:
        abort(404)
    if request.method == "POST":
        password = request.form.get("password", "")
        user.name = request.form["name"]
        user.email = request.form["email"].strip().lower()
        user.role = request.form.get("role", "editor")
        user.is_active = bool(request.form.get("is_active"))
        if password:
            user.password_hash = hash_password(password)
        elif not user.password_hash:
            flash("Password is required for new users.")
            return render_template("admin/user_form.html", user=user)
        db.session.add(user)
        db.session.commit()
        flash("User saved.")
        return redirect(url_for("main.admin_users"))
    return render_template("admin/user_form.html", user=user)


@bp.post("/admin/users/<int:user_id>/delete")
@role_required("admin")
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user().id:
        flash("You cannot delete your own account.")
        return redirect(url_for("main.admin_users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.")
    return redirect(url_for("main.admin_users"))


@bp.route("/admin/pages")
@admin_required
def admin_pages():
    pages = Page.query.order_by(Page.slug).all()
    return render_template("admin/pages.html", pages=pages)


@bp.route("/admin/pages/new", methods=["GET", "POST"])
@bp.route("/admin/pages/<int:page_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_page_form(page_id=None):
    page = Page.query.get(page_id) if page_id else Page()
    if page_id and not page:
        abort(404)
    if request.method == "POST":
        page.title = request.form["title"]
        page.slug = request.form["slug"]
        page.content = request.form.get("content", "")
        page.meta_title = request.form.get("meta_title", "")
        page.meta_description = request.form.get("meta_description", "")
        page.status = request.form.get("status", "published")
        db.session.add(page)
        db.session.commit()
        flash("Page saved.")
        return redirect(url_for("main.admin_pages"))
    return render_template("admin/page_form.html", page=page)


@bp.route("/admin/pages/<int:page_id>/sections", methods=["GET", "POST"])
@admin_required
def admin_page_sections(page_id):
    page = Page.query.get_or_404(page_id)
    if request.method == "POST":
        section = PageSection(
            page=page,
            name=request.form["name"],
            section_type=request.form.get("section_type", "content"),
            content=request.form.get("content", ""),
            sort_order=int(request.form.get("sort_order") or 0),
            is_active=bool(request.form.get("is_active")),
        )
        db.session.add(section)
        db.session.commit()
        flash("Section added.")
        return redirect(url_for("main.admin_page_sections", page_id=page.id))
    return render_template("admin/sections.html", page=page)


@bp.post("/admin/sections/<int:section_id>/delete")
@admin_required
def admin_delete_section(section_id):
    section = PageSection.query.get_or_404(section_id)
    page_id = section.page_id
    db.session.delete(section)
    db.session.commit()
    flash("Section deleted.")
    return redirect(url_for("main.admin_page_sections", page_id=page_id))


@bp.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    if request.method == "POST":
        for key, value in request.form.items():
            setting = SiteSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
        db.session.commit()
        flash("Settings saved.")
        return redirect(url_for("main.admin_settings"))
    settings = SiteSetting.query.order_by(SiteSetting.key).all()
    return render_template("admin/settings.html", settings=settings)


@bp.route("/admin/media", methods=["GET", "POST"])
@admin_required
def admin_media():
    if request.method == "POST":
        folder = request.form.get("folder", "gallery")
        title = request.form.get("title", "")
        alt_text = request.form.get("alt_text", "")
        path = save_upload("file", folder, title, alt_text)
        if path:
            db.session.commit()
            flash("Media uploaded.")
        return redirect(url_for("main.admin_media"))
    assets = MediaAsset.query.order_by(MediaAsset.created_at.desc()).all()
    return render_template("admin/media.html", assets=assets)


@bp.post("/admin/media/<int:asset_id>/delete")
@admin_required
def admin_delete_media(asset_id):
    asset = MediaAsset.query.get_or_404(asset_id)
    file_path = asset.file_path
    uploaded_by = asset.uploaded_by
    db.session.delete(asset)
    db.session.commit()

    # Files uploaded through the dashboard are runtime-owned. Imported assets
    # remain in the repository, while removing their DB record hides them.
    if uploaded_by == "admin" and file_path.startswith("/static/uploads/"):
        relative_path = file_path.removeprefix("/static/uploads/")
        target = (Path(current_app.config["UPLOAD_ROOT"]) / relative_path).resolve()
        upload_root = Path(current_app.config["UPLOAD_ROOT"]).resolve()
        if upload_root in target.parents and target.is_file():
            target.unlink()

    flash("Media deleted.")
    return redirect(url_for("main.admin_media"))


@bp.route("/admin/certificates", methods=["GET", "POST"])
@admin_required
def admin_certificates():
    if request.method == "POST":
        image = save_upload("image_file", "certificates", request.form["title"], request.form.get("title", ""))
        cert = Certificate(
            title=request.form["title"],
            image=image or request.form.get("image", ""),
            certificate_type=request.form.get("certificate_type", "registration"),
        )
        db.session.add(cert)
        db.session.commit()
        flash("Certificate added.")
        return redirect(url_for("main.admin_certificates"))
    items = Certificate.query.order_by(Certificate.created_at.desc()).all()
    return render_template("admin/certificates.html", items=items)


@bp.route("/admin/certificates/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_certificate(item_id):
    item = Certificate.query.get_or_404(item_id)
    if request.method == "POST":
        image = save_upload("image_file", "certificates", request.form["title"], request.form.get("title", ""))
        item.title = request.form["title"]
        item.image = image or request.form.get("image", "")
        item.certificate_type = request.form.get("certificate_type", "registration")
        db.session.commit()
        flash("Certificate updated.")
        return redirect(url_for("main.admin_certificates"))
    return render_template("admin/certificate_form.html", item=item)


@bp.post("/admin/certificates/<int:item_id>/delete")
@admin_required
def admin_delete_certificate(item_id):
    item = Certificate.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Certificate deleted.")
    return redirect(url_for("main.admin_certificates"))


@bp.route("/admin/media-recognition", methods=["GET", "POST"])
@admin_required
def admin_media_recognition():
    if request.method == "POST":
        image = save_upload("image_file", "media-recognition", request.form["title"], request.form.get("title", ""))
        item = MediaRecognition(
            title=request.form["title"],
            image=image or request.form.get("image", ""),
            publication_name=request.form.get("publication_name", ""),
            article_link=request.form.get("article_link", ""),
            category=request.form.get("category", "newspaper"),
        )
        db.session.add(item)
        db.session.commit()
        flash("Media recognition added.")
        return redirect(url_for("main.admin_media_recognition"))
    items = MediaRecognition.query.order_by(MediaRecognition.created_at.desc()).all()
    return render_template("admin/media_recognition.html", items=items)


@bp.route("/admin/media-recognition/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_media_recognition(item_id):
    item = MediaRecognition.query.get_or_404(item_id)
    if request.method == "POST":
        image = save_upload("image_file", "media-recognition", request.form["title"], request.form.get("title", ""))
        item.title = request.form["title"]
        item.image = image or request.form.get("image", "")
        item.publication_name = request.form.get("publication_name", "")
        item.article_link = request.form.get("article_link", "")
        item.category = request.form.get("category", "newspaper")
        db.session.commit()
        flash("Media recognition updated.")
        return redirect(url_for("main.admin_media_recognition"))
    return render_template("admin/media_recognition_form.html", item=item)


@bp.post("/admin/media-recognition/<int:item_id>/delete")
@admin_required
def admin_delete_media_recognition(item_id):
    item = MediaRecognition.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Media recognition deleted.")
    return redirect(url_for("main.admin_media_recognition"))
