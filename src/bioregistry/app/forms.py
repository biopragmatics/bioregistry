# -*- coding: utf-8 -*-

"""Forms for the web application."""

from textwrap import dedent
from typing import ClassVar, List

from flask import jsonify, render_template
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired

import bioregistry


class RenderingForm(FlaskForm):
    """A generic form that renders JSON after submitted."""

    title: ClassVar[str]
    description: ClassVar[str]

    @classmethod
    def render(cls):
        """Create the form and render it."""
        form = cls()
        if form.validate_on_submit():
            return jsonify(form.make_json())
        return render_template(
            'generic_form.html', form=form, description=cls.description, title=cls.title,
        )

    def make_json(self):
        """Generate JSON from this form."""
        raise NotImplementedError


class TextAreaForm(RenderingForm):
    """A generic form."""

    #: Text area field
    text = TextAreaField('Input', validators=[DataRequired()])
    submit = SubmitField('Submit')


class GenerateContextForm(TextAreaForm):
    """A form for generating a JSON-LD with a @context entry."""

    title = 'Generate a JSON-LD Context'
    description = dedent('''\
        Add a list of prefixes (either comma-separated or line-separated) to generate a JSON-LD
        document with a <code>@context</code> entry containing a mapping from the given prefixes
        to their respective URL expansions.
    ''')

    def get_prefixes(self) -> List[str]:
        """Get the prefixes in the form."""
        return [
            prefix.strip()
            for line in self.text.data.splitlines()
            for prefix in line.strip().split(',')
        ]

    def make_json(self):
        """Generate a JSON-LD document with context for the given prefixes."""
        return {
            '@context': {
                prefix: bioregistry.get_format_url(prefix)
                for prefix in self.get_prefixes()
                if prefix
            },
        }
