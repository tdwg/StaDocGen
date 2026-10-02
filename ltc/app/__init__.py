import os
from pathlib import Path

# freeze.py reads meta.yml, md/ and data/ relative to the app directory,
# but `flask run` is invoked from the instance root
os.chdir(Path(__file__).resolve().parent)

from app.freeze import app
