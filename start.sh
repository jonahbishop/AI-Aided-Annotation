# For development use (simple logging, etc):
python3 server.py
# python3 mmr.py
# For production use: 
# gunicorn server:app -w 1 --log-file -

# #!/bin/bash

# # Exit early on errors
# set -eu

# # Python buffers stdout. Without this, you won't see what you "print" in the Activity Logs
# export PYTHONUNBUFFERED=true

# # Install Python 3 virtual env
# VIRTUALENV=.data/venv

# if [ ! -d $VIRTUALENV ]; then
#   python3 -m venv $VIRTUALENV
# fi

# if [ ! -f $VIRTUALENV/bin/pip ]; then
#   curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | $VIRTUALENV/bin/python
# fi

# # Install the requirements
# $VIRTUALENV/bin/pip install -r requirements.txt

# # Start the MongoDB service
# sudo systemctl start mongodb

# # Run a glorious Python 3 server
# $VIRTUALENV/bin/python3 server.py