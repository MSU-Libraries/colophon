"""
This file is executed before pytest runs
"""
import os
import sys
cur_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cur_path)
