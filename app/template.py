"""
Template functionality
"""
import jinja2

def render_template_string(string: str, context: dict) -> str:
    """
    Render the template string using the provided context
    returns:
        The rendered string
    """
    env = jinja2.Environment()
    tmpl = env.from_string(string)
    return templ.render(context)
