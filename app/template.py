"""
Template functionality
"""
import os
import jinja2
from jinja2.lexer import Token
from jinja2.ext import Extension
import app

COMPILED_TEMPLATES = {}

def escape_shell_arg(arg: str):
    """
    Escape a string to pass as a shell argument
    """
    return "'" + arg.replace("'", "'\\''") + "'"

class ShellEscapeInjector(Extension):
    """Inject shell escape calls after template variables"""
    def parse(self, parser):
        pass

    def filter_stream(self, stream):
        """Find variables, add shell escape"""
        for token in stream:
            # Inject our escape into the stream after each variable
            if token.type == 'variable_end':
                yield Token(token.lineno, 'pipe', '|')
                yield Token(token.lineno, 'name', 'esh')
            yield token

def render_template_string(string: str, context: dict, shell=False) -> str:
    """
    Render the template string using the provided context.
    All variables will be escaped as shell arguments using single quotes.
    args:
        string: The string to be rendered
        context: The context to make available to the template
        shell: If true, will escape all variables for use as shell arguments
    returns:
        The rendered string
    """
    templ_key = (string, shell)
    try:
        if templ_key not in COMPILED_TEMPLATES:
            env = jinja2.Environment(
                autoescape=False,
                extensions=([ShellEscapeInjector] if shell else [])
            )
            env.filters['esh'] = escape_shell_arg
            env.filters['basename'] = os.path.basename
            COMPILED_TEMPLATES[templ_key] = env.from_string(string)
        return COMPILED_TEMPLATES[templ_key].render(context)
    except jinja2.exceptions.TemplateSyntaxError as exc:
        fmsg = f"Jinja syntax had {exc} in `{string}`"
        raise app.TemplateRenderFailure(fmsg) from None
    except jinja2.exceptions.UndefinedError as exc:
        fmsg = f"Jinja value {exc} inside `{string}`"
        raise app.TemplateRenderFailure(fmsg) from None
