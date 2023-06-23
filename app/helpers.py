"""
Helper functions
"""
import re
import app
from app.template import render_template_string

CACHED_REGEX = {}

def cached_re_search(pattern: str, string: str, flags: int = 0):
    """
    Run a re.search() where it will use a cached instance of the re.compile if available.
    """
    re_key = (pattern, flags)
    ignorecase = re.IGNORECASE & flags
    if re_key not in CACHED_REGEX:
        CACHED_REGEX[re_key] = re.compile(*re_key)
    return CACHED_REGEX[re_key].search(string)

def _prerender_value(value: str, context: dict, ignorecase = False):
    """Preprocess string before comparison"""
    try:
        string = render_template_string(value, context)
    except TypeError as exc:
        fmsg = f"Could not render string \"{value}\": {exc}"
        app.logger.error(fmsg)
        raise app.TemplateRenderFailure(fmsg) from None
    return string.lower() if ignorecase else string

def value_match(value: str, conditions: dict, context: dict = None):
    """
    Check if the value meets all passed conditions
    """
    if context is None:
        context = {}
    matched = True
    ignorecase = conditions.get('ignorecase', False)
    vstr = _prerender_value(value, context, ignorecase)
    for ckey, cval in conditions.items():
        # Skip supplimental flags
        if ckey in ["ignorecase", "multiple", "optional"]:
            continue
        cstr = _prerender_value(cval, context, ignorecase)
        if ckey == 'equals':
            matched &= vstr == cstr
        elif ckey == 'startswith':
            matched &= vstr.startswith(cstr)
        elif ckey == 'endswith':
            matched &= vstr.endswith(cstr)
        elif ckey == 'regex':
            matched &= cached_re_search(
                cval,   # Intentionally not rendering Regex patterns
                vstr,
                re.IGNORECASE if ignorecase else 0
            ) is not None
        elif ckey in ('greaterthan', 'lessthan'):
            if ckey == 'lessthan':
                vstr, cstr = cstr, vstr
            matched &= vstr.isdigit() and cstr.isdigit() and int(vstr) > int(cstr)
    return matched

class ExitCode:
    """Helper class for exit codes"""
    def __init__(self, exit_code: str):
        self.exit_code = f"{exit_code}" # Ensure str

    def __repr__(self):
        return f"ExitCode(exit_code={self.exit_code}, describe={','.join(self.describe())})"

    def __str__(self):
        return f"{','.join(self.describe())}"

    def describe(self):
        """Return a list of messages describing the meaning of the exit code"""
        msgs = []
        if not self.exit_code.isdigit():
            msgs.append("invalid_or_unset")
        else:
            ec_int = int(self.exit_code)
            msgs.append("failure" if ec_int & 1 else "success")
            if ec_int & 2:
                msgs.append("inaccessible_file")
            if ec_int & 4:
                msgs.append("bad_argument")
            if ec_int & 8:
                msgs.append("warning_logged")
            if ec_int & 16:
                msgs.append("skip_manfest_row")
        return msgs
