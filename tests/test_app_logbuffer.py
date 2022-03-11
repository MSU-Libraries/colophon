import logging
import pytest
import tempfile
from app import LogBuffer

def line_count(text):
    return len(text.splitlines())

def test_app_logbuffer(caplog):
    caplog.set_level(logging.DEBUG)
    logger = logging.getLogger()

    logger.debug("001")
    assert line_count(caplog.text) == 1

    LogBuffer.start_buffer()
    logger.debug("002")
    logger.debug("003")
    assert line_count(caplog.text) == 1

    LogBuffer.end_buffer()
    assert line_count(caplog.text) == 3

    logger.debug("004")
    assert line_count(caplog.text) == 4

    LogBuffer.start_buffer()
    logger.debug("005")
    logger.debug("006")
    assert line_count(caplog.text) == 4

    LogBuffer.end_buffer(discard=True)
    assert line_count(caplog.text) == 4

    logger.debug("007")
    assert line_count(caplog.text) == 5
