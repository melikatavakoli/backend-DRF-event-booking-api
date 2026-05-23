import os
from pathlib import Path
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent.parent

env = {
    **dotenv_values(BASE_DIR / ".env"),
    **dotenv_values(BASE_DIR / ".env.local"),
}
for key, value in env.items():
    if value is not None:
        os.environ[key] = value
