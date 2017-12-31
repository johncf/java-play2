import os
import sys

is_frozen = getattr(sys, 'frozen', False)

if is_frozen:
    root_dir = os.path.dirname(sys.executable)
else:
    root_dir = os.path.dirname(os.path.realpath(__file__))

sessions_dir = os.path.join(root_dir, 'sessions')
static_dir = os.path.join(root_dir, 'static')

def _get_jdkpath(path_file):
    try:
        with open(path_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                if len(line) > 0:
                    if os.path.isabs(line):
                        return line
                    else:
                        return os.path.join(root_dir, line)
    except:
        pass
    return ''

jdk_path = _get_jdkpath(os.path.join(root_dir, 'jdk.path'))
