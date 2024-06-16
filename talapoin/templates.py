from jinja2 import BaseLoader, FileSystemLoader, TemplateNotFound
from sqlalchemy import select

from .models import Page

class TalapoinLoader(BaseLoader):
    def __init__(self, load_func, filesystem_loader):
        self.load_func = load_func
        self.filesystem_loader = filesystem_loader

    def get_source(self, environment, template):
        # First we try load_func, then fall back to FileSystemLoader if
        # load_func signals it couldn't handle it
        try:
            source, filename, uptodate = self.load_func(self.db, template)
            return source, filename, uptodate
        except (ValueError):
            # If we get a ValueError, load_func didn't understand template
            # so we just pass it on the the FileSystemLoader
            return self.filesystem_loader.get_source(environment, template)

    def init_db(self, db):
        self.db = db

def db_template(db, template_name):
    if template_name.startswith('@'):
        template = db.session.scalar((select(Page).where(Page.slug == template_name)))
        if template is None:
            raise TemplateNotFound(f"Unable to find template '{template_name}'")
        return template.content, None, None
    else:
        raise ValueError(f"Don't know how to handle template named '{template_name}'")

# Create the filesystem loader
filesystem_loader = FileSystemLoader("templates")

# Combine the loaders
loader = TalapoinLoader(db_template, filesystem_loader)
