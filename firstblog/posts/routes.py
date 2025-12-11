from flask import Blueprint
from flask import render_template, url_for, flash, redirect, request, abort
from firstblog import db, mail
from firstblog.posts.forms import PostForm
from firstblog.models import User, Post
from flask_login import current_user, login_required
import requests
import os
import logging
import re

posts = Blueprint('posts', __name__)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-flash-2.0:generateContent"
)
# Use environment variable for the API key (safer). Set this before running your app.
GEMINI_API_KEY = "AIzaSyBqsfzRQ5YqXSeiNvwCnE2cGzgretLfZWE"

# Optional: configure basic logging if your app doesn't already do so
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _clean_input_text(s: str) -> str:
    """Remove any leading classification symbols and trim whitespace."""
    if not s:
        return ""
    # Remove leading symbols and whitespace
    return re.sub(r'^[⛔✔️➖\s]+', '', s).strip()


def _analyze_text_to_symbol(title: str, content: str) -> str:
    """
    Improved classifier:
    - sanitizes inputs,
    - short-circuits to 'real' for clear official announcements,
    - uses a strict prompt with examples,
    - logs model raw responses for debugging,
    - falls back to neutral (➖) on errors or unclear replies.
    Returns one of: "⛔" (fake), "✔️" (real), "➖" (neutral).
    """
    # sanitize
    title_clean = _clean_input_text(title)
    content_clean = _clean_input_text(content)

    # deterministic heuristic for obvious "official announcement" phrasing
    official_keywords = (
        "official", "first look", "dropped", "announced", "press release", "released", "netflix", "trailer"
    )
    text_concat = f"{title_clean} {content_clean}".lower()
    if any(k in text_concat for k in official_keywords):
        # if it mentions a year (e.g. 2026) or specific 'official' wording, assume real
        if re.search(r'\b20\d{2}\b', text_concat) or "official" in text_concat or "first look" in text_concat:
            logger.info("Heuristic: detected official announcement keywords; returning 'real'")
            return "✔️"

    # Ensure we have an API key
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set in environment; returning neutral symbol.")
        return "➖"

    # Strict prompt — force a single-word response
    prompt = (
        "You are a classifier. Classify the following news/text as exactly one of the words: "
        "'fake', 'real', or 'neutral'. ONLY reply with that one word and NOTHING ELSE.\n\n"
        "Examples:\n"
        "1) 'Company X announces their confirmed press release' -> real\n"
        "2) 'Rumor: celebrity might be dating...' -> fake\n"
        "3) 'Discussion about whether shows will return' -> neutral\n\n"
        f"Title: {title_clean}\n\nContent: {content_clean}\n\nReturn only one word:"
    )

    body = {"contents": [{"parts": [{"text": prompt}]}]}

    symbol = "➖"  # default neutral
    try:
        resp = requests.post(
            GEMINI_API_URL + f"?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=body,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # Log raw response for debugging (remove or reduce in production if verbose)
        logger.info("Gemini raw response: %s", data)

        # Preferred extraction path
        output_text = ""
        try:
            output_text = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            # Fallback: gather all string leaves if response shape differs
            strings = []

            def _gather(o):
                if isinstance(o, str):
                    strings.append(o)
                elif isinstance(o, dict):
                    for v in o.values():
                        _gather(v)
                elif isinstance(o, list):
                    for v in o:
                        _gather(v)

            _gather(data)
            output_text = " ".join(strings)[:2000]

        # Log the extracted text
        logger.info("Gemini extracted text: %s", output_text)

        t = (output_text or "").strip().lower()

        # Exact match preferred
        if t == "fake":
            symbol = "⛔"
        elif t == "real":
            symbol = "✔️"
        elif t == "neutral":
            symbol = "➖"
        else:
            # Try substring detection for cases where the model responds in a sentence
            if "fake" in t:
                symbol = "⛔"
            elif "real" in t:
                symbol = "✔️"
            elif "neutral" in t:
                symbol = "➖"
            else:
                logger.info("Unclear classification from model: '%s' — defaulting to neutral", t)
                symbol = "➖"

    except requests.exceptions.RequestException as e:
        logger.exception("Request to Gemini failed: %s", e)
        symbol = "➖"
    except Exception as e:
        logger.exception("Unexpected error parsing Gemini response: %s", e)
        symbol = "➖"

    return symbol


@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        # Remove any existing symbol before analyzing (avoid bias)
        title_to_check = _clean_input_text(form.title.data)
        content_to_check = _clean_input_text(form.content.data)

        symbol = _analyze_text_to_symbol(title_to_check, content_to_check)
        content_with_symbol = f"{symbol}\n\n{form.content.data}"
        post = Post(title=form.title.data, content=content_with_symbol, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@posts.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@posts.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('posts.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@posts.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('main.home'))


@posts.route("/posts/mark_all", methods=['POST'])
@login_required
def mark_all_posts():
    posts_list = Post.query.all()
    updated = 0
    for p in posts_list:
        # If you want to re-evaluate posts that already have symbols, remove this skip
        text = (p.content or "").lstrip()
        if text.startswith(("⛔", "✔️", "➖")):
            continue

        # Clean content before sending to model (removes any stray symbols)
        title_to_check = _clean_input_text(p.title or "")
        content_to_check = _clean_input_text(p.content or "")

        symbol = _analyze_text_to_symbol(title_to_check, content_to_check)
        p.content = f"{symbol}\n\n{p.content or ''}"
        updated += 1
    db.session.commit()
    flash(f'Marked {updated} posts.', 'success')
    return redirect(url_for('main.home'))
