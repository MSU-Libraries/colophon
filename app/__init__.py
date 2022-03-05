from .manifest import Manifest
from .directory import Directory
from .suite import Suite
from .exception import ColophonException
from .process import exec_command, write_output
from .job import ColophonJob
import app.report

install_path = None
manifest = None
suite = None
sourcedir = None
workdir = None
logger = None
globalctx = {}
