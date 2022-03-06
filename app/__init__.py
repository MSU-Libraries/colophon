"""
Main application lookup
"""
import logging
import app.report
from .manifest import Manifest
from .directory import Directory
from .suite import Suite
from .exception import ColophonException, EndStagesProcessing, StageProcessingFailure
from .process import exec_command, write_output
from .job import ColophonJob

# pylint: disable=invalid-name
install_path: str = None
manifest: Manifest = None
suite: Suite = None
sourcedir: Directory = None
workdir: str = None
logger: logging.Logger = None
globalctx: dict = {}
