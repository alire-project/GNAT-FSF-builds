"""
Test that always fails to check if we can detect failures
"""
import os

os.sys_exit(1)  # FAIL

print("SUCCESS")
