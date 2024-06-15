import os
import sys
import inspect

from flask import Flask, render_template, url_for, request, abort
from flask_sqlalchemy_lite import SQLAlchemy

from sqlalchemy import select, URL

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

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html'), 404

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    from .models import Page
    @app.route('/<path:path>')
    def page(path):
        # load page
        page = db.session.scalar((select(Page).where(Page.slug == path)))
        if page is None:
            abort(404)
        return render_template('page.html', page=page)

    @app.template_filter('markdown_to_html')
    def markdown(s):
        return mistune.html(s)

    @app.template_filter('date')
    def date(dt, fmt):
        return dt

    @app.context_processor
    def inject_twig_compat():
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

        def include(str, **kwargs):
            return ""

        def template_from_string(str, **kwargs):
            return ""

        def include_fragment(fragment_name, **kwargs):
            return ""

        def date(str, **kwargs):
            return ""

        return {
            'full_url_for' : full_url_for,
            'current_url' : current_url,
            'block' : block,
            'current_release' : current_release,
            'include' : include,
            'template_from_string' : template_from_string,
            'includeFragment' : include_fragment,
            'date' : date,
        }

    db.init_app(app)

    return app
