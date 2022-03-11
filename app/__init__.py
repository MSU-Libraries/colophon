"""
Main application lookup
"""
import logging
from app.logbuffer import LogBuffer
import app.report
from .manifest import Manifest
from .directory import Directory
from .suite import Suite
from .exception import (
    ColophonException, EndStagesProcessing,
    StageProcessingFailure, TemplateRenderFailure
)
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
