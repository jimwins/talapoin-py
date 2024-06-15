from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from . import db
from .models import Entry

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    entries = db.session.scalars(select(Entry).where(Entry.draft == False).order_by(Entry.created_at.desc()).limit(10)).all()
    return render_template('index.html', entries=entries)

@bp.route('/index.atom')
@bp.route('/{tag}/index.atom')
def atom(tag=None):
    return "Not yet"

@bp.route('/tag/<tag>')
def tag(tag):
    return "Not yet"

@bp.route('/<int:year>/<int:month>/<int:date>/<string:slug>')
def entry(year, month, date, slug):
    if slug.isdigit():
        entry = db.session.scalar(select(Entry).where(Entry.id == slug))
    else:
        entry = db.session.scalar(select(Entry).filter(Entry.title.ilike(slug)))

    if entry is None:
        abort(404)

    # make sure we used canonical URL, or redirect
    # TODO

    # get next and previous
    # TODO
    next = False
    previous = False

    return render_template('entry.html', entry= entry, next= next, previous= previous)
