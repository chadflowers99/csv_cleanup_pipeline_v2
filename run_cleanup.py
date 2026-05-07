# run_cleanup.py
# To switch datasets, change the import below to the config you want:
#   from cafe_config import config  # (if you create one)
#   from electronics_config import config

from electronics_config import config #from cafe_config import config  # <-- swap this line to change dataset

from cleanup_engine import run_cleanup

import cleanup_engine
print(">>> Python imported cleanup_engine from:", cleanup_engine.__file__)

print("CALLING RUN_CLEANUP NOW")
run_cleanup(config)