from app import template

def test_render_template_string():
    ctx1 = {
        "a": "alpha",
        "b": "beta"
    }
    assert template.render_template_string(
        "{{ a }} before {{ b }}",
        ctx1
    ) == "alpha before beta"
    assert template.render_template_string(
        "{{ a }} before {{ b }}",
        ctx1,
        shell=True
    ) == "'alpha' before 'beta'"

    ctx2 = {
        "a": "Special 'chars' found $ here!! <> $?.",
        "b": None
    }
    assert template.render_template_string(
        "=={{ a }}==",
        ctx2
    ) == "==Special 'chars' found $ here!! <> $?.=="
    assert template.render_template_string(
        "=={{ a }}==",
        ctx2,
        shell=True
    ) == "=='Special '\\''chars'\\'' found $ here!! <> $?.'=="
