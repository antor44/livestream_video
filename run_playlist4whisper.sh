#!/bin/bash

# ==============================================================================
# Script to run playlist4whisper.py
# ------------------------------------------------------------------------------
# This script performs two main actions:
# 1. Activates a standard Python virtual environment named 'whisper'.
# 2. Runs the 'playlist4whisper.py' script.
#
# It assumes that the 'whisper.cpp' directory is located in your
# home folder (~/whisper.cpp).
# ==============================================================================

echo "Navigating to the whisper.cpp directory..."
# Change to the working directory. The script will exit if this directory doesn't exist.
# Using '~' makes this path absolute from your home directory, so it works from anywhere.
cd ~/whisper.cpp || exit 1

# --- Standard Virtual Environment (venv) ---
# This activates a virtual environment named 'whisper' created with venv or virtualenv.
# Adjust the path if your 'python-environments' folder is located elsewhere.
#
echo "Activating Python virtual environment..."
source ~/python-environments/whisper/bin/activate


echo "Launching the Python script: playlist4whisper.py..."
# Runs the script. Using 'python3' ensures better compatibility.
python3 playlist4whisper.py


echo "Process finished."


# --- Alternative for Anaconda / Miniconda ---
# If you use an Anaconda environment, you should COMMENT OUT the 'source' command
# above and instead run the script from your terminal using one of the following
# commands. It handles activating the environment and running the script in one step.
#
# Replace 'your_env_name' with the actual name of your Conda environment.
#
# Command:
# conda run -n your_env_name python ~/whisper.cpp/playlist4whisper.py
#
# Or, if you need the full path to conda:
# ~/anaconda3/bin/conda run -n your_env_name python ~/whisper.cpp/playlist4whisper.py
