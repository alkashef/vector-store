
"""
Minimal settings.py: Only loads .env variables.
"""

from pathlib import Path
from dotenv import load_dotenv

def load_envs():
    cfg_dir = Path(__file__).resolve().parent
    env_path = cfg_dir / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    repo_env = cfg_dir.parent / ".env"
    if repo_env.exists():
        load_dotenv(dotenv_path=repo_env)

load_envs()


