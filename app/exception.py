"""
Colophon Exception and Error Handling
"""

class ColophonException(Exception):
    """Generic Colophon Exception"""

class EndStagesProcessing(Exception):
    """Exception to jump out of stages for current manifest entry"""

class StageProcessingFailure(Exception):
    """Exception to jump out of stages for current manifest entry"""
