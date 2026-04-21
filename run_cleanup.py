# run_cleanup.py

from cleanup_engine import run_cleanup
from cafe_config import config

import cleanup_engine
print(">>> Python imported cleanup_engine from:", cleanup_engine.__file__)

print("CALLING RUN_CLEANUP NOW")
run_cleanup(config)