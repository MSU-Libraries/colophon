from app import helpers

def test_value_match():
    # Greater than / less than
    value = "{{ file.size }}"
    ctx = {
        "file": { "size": "500" },
    }
    conditions = { "greaterthan": "256", "lessthan": "512" }
    assert helpers.value_match(value, conditions, ctx) == True
    conditions = { "greaterthan": "500", "lessthan": "512" }
    assert helpers.value_match(value, conditions, ctx) == False
    conditions = { "greaterthan": "256", "lessthan": "384" }
    assert helpers.value_match(value, conditions, ctx) == False
