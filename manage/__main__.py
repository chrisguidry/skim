import os
import sys


command = sys.argv[1]

if command == 'update_requirements':
    os.system(
        'pip-compile --upgrade requirements.in --output-file requirements.txt'
    )
