"""Environment variable bootstrap logic.

Responsible for safely injecting correct .env runtime values BEFORE
Pydantic config initialization begins.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("env_loader")


def load_environment() -> None:
    """Load the correct .env file based on APP_RUNTIME."""
    if os.getenv("ENV_LOADED"):
        return

    # Find the root directory containing .env.local
    current_dir = Path(__file__).resolve()
    search_dir = current_dir
    while search_dir != search_dir.parent:
        if (search_dir / ".env.local").exists():
            break
        search_dir = search_dir.parent
    else:
        logger.warning("Could not locate project root containing .env.local")
        return

    # If already loaded by docker-compose, APP_RUNTIME will be 'docker'
    runtime = os.getenv("APP_RUNTIME", "local")

    if runtime == "docker":
        env_file = search_dir / ".env.docker"
    else:
        env_file = search_dir / ".env.local"

    if env_file.exists():
        # Load the base .env first for shared secrets (never override runtime env)
        base_env = search_dir / ".env"
        if base_env.exists():
            load_dotenv(base_env, override=False)

        # Load runtime-specific file as defaults (never override runtime env)
        load_dotenv(env_file, override=False)
        print(f"Loaded environment defaults from {env_file.name}")
        os.environ["ENV_LOADED"] = "1"
    else:
        print(f"Warning: Environment file {env_file} not found.")
