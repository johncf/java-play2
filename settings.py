import os
import sys

is_frozen = getattr(sys, 'frozen', False)

if is_frozen:
    root_dir = os.path.dirname(sys.executable)
else:
    root_dir = os.path.dirname(os.path.realpath(__file__))

sessions_dir = os.path.join(root_dir, 'sessions')
static_dir = os.path.join(root_dir, 'static')
