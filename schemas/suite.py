"""
The schema for suite files
"""
from copy import deepcopy
_label_match = {
    'label': {
        'required': True,
        'type': 'string'
    },
    'equals': { 'type': 'string' },
    'startswith': { 'type': 'string' },
    'endswith': { 'type': 'string' },
    'regex': { 'type': 'string' },
    'ignorecase': { 'type': 'boolean' }
}
_file_match = deepcopy(_label_match)
_file_match.update(
    {
        'multiple': { 'type': 'boolean' },
        'optional': { 'type': 'boolean' }
    }
)

suite = {
    'manifest': {
        'required': True,
        'type': 'dict',
        'schema': {
            'filter': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'minlength': 2,
                    'schema': _label_match
                }
            },
            'files': {
                'empty': False,
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': _file_match
                }
            }
        }
    },
    'stages': {
        'required': True,
        'type': 'dict',
        'allow_unknown': True,
        'minlength': 1,
        'schema': {
            'schema': {
                'script': {
                    'required': True,
                    'type': 'string'
                }
            }
        }
    }
}
