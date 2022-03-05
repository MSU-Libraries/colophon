"""
Colophon Exception and Error Handling
"""

class ColophonException(Exception):
    """Generic Colophon Exception"""
    pass

class StopProcessing(Exception):
    """Exception to jump out of code blocks"""
    pass
