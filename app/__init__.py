from .manifest import Manifest
from .directory import Directory
from .suite import Suite
from .exception import ColophonException
from .process import exec_command, write_output

manifest = None
suite = None
sourcedir = None
workdir = None
prefix = ''
logger = None
globalctx = {}
