import os
import sys
import inspect
import re

from flask import Flask, render_template, url_for, request, abort
from flask_sqlalchemy_lite import SQLAlchemy

from sqlalchemy import select, URL

from markupsafe import Markup, escape

import mistune

db = SQLAlchemy()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, template_folder='../templates')
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    app.config |= {
        "SQLALCHEMY_ENGINES": {
            "default": {
                'url': URL.create(
                    drivername= 'mysql+mysqlconnector',
                    host= 'db',
                    database= os.environ['MYSQL_DATABASE'],
                    username= os.environ['MYSQL_USER'],
                    password= os.environ['MYSQL_PASSWORD'],
                ),
                'echo': True
            }
        },
        "TEMPLATES_AUTO_RELOAD": True,
    }

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.config.from_prefixed_env()

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from .templates import loader
    app.jinja_loader = loader
    loader.init_db(db)

    @app.errorhandler(404)
    def page_not_found(e):
        # TODO figure out how to pass exception in useful way
        return render_template('error.html', exception= None), 404

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='top')

    @app.route('/photo')
    def photos():
        return "Not yet"

    from .models import Page
    @app.route('/<path:path>')
    def page(path):
        # load page
        page = db.session.scalar((select(Page).where(Page.slug == path)))
        if page is None:
            abort(404)
        return render_template('page.html', page=page)

    @app.template_filter('get_debug_type')
    def get_debug_type():
        return ""

    @app.template_filter('expand_psuedo_urls')
    def expand_psuedo_urls(s):
        # Replace ISBN references with Bookshop.org URLs
        s = re.sub(r'isbn:([0-9x]+)', r'https://bookshop.org/a/94608/\1', s)
        # Replace ASIN references with Amazon URLs
        s = re.sub(r'asin:(\w+)', r'http://www.amazon.com/exec/obidos/ASIN/\1/trainedmonkey', s)
        return s

    @app.template_filter('markdown_to_html')
    def markdown(s):
        return mistune.html(s)

    @app.template_filter('date')
    def date(dt, fmt):
        return dt

    # Just an alias for what Twig calls it
    @app.template_filter('raw')
    def raw(s):
        return Markup(s)

    # Jinja does much more limited escaping than Twig, but this handles the
    # strategy argument values we need for our templates that use the `e` filter.
    @app.template_filter('e')
    def e(s, strategy= None):
        if strategy not in (None, "html", "html_attr"):
            raise ValueError(f'Unhandled strategy "{strategy}" for escaping')
        return escape(s)

    @app.context_processor
    def inject_twig_compat():
        # Unlike Flask's default url_for() we accept a second parameter that
        # looks like a dict of keywords to make it compatible with Twig's
        # url_for() which looks like url_for('route', { 'var': value })
        def url_for(endpoint_name, *args, **kwargs):
            d = {}
            if (args): # TODO should validate this more, we just assume it's a dict
                d = args[0]
            return app.url_for(endpoint_name, **d, **kwargs)

        def full_url_for(endpoint_name, *args, **kwargs):
            view_func = app.view_functions.get(endpoint_name)
            if view_func:
                # Get argument names from the view function definition (reflection)
                argspec = inspect.getfullargspec(view_func)
                arg_names = argspec.args[1:]  # Skip 'self'
                # Convert args to kwargs if the number of arguments match
                if len(args) == len(arg_names):
                    kwargs.update(dict(zip(arg_names, args)))

            return url_for(endpoint_name, _external=True, **kwargs)  # _external for full URL

        def current_url():
            # if there's no endpoint, we're probably in an error handler
            if request.endpoint:
                return url_for(request.endpoint, _external=False, **request.view_args)
            else:
                return "/error"

        def block(block_name, **kwargs):
            return "no"

        def current_release(**kwargs):
            return ""

        def date(str, **kwargs):
            return ""

        return {
            'url_for' : url_for,
            'full_url_for' : full_url_for,
            'current_url' : current_url,
            'block' : block,
            'current_release' : current_release,
            'date' : date,
        }

    db.init_app(app)

    return app
