"""Configuration management -- loads .env and exposes typed settings."""

from __future__ import annotations

import os
import platform
import socket
from pathlib import Path, PurePosixPath

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


def _find_repo_root() -> Path:
    """Walk up from this file to find the structured-agents repo root (contains pyproject.toml)."""
    current = Path(__file__).resolve().parent
    for ancestor in [current, *current.parents]:
        if (ancestor / "pyproject.toml").exists() and (ancestor / "agents").is_dir():
            return ancestor
    return current


class Settings(BaseSettings):
    """Typed settings populated from environment variables and .env file."""

    repo_root: Path = Field(default_factory=_find_repo_root)

    # Remote server / SSH
    # Stored as str because this is a *remote* Linux path -- converting it to
    # a local Path on Windows would mangle forward slashes into backslashes.
    sagent_workspace: str = Field(alias="SAGENT_WORKSPACE")
    sagent_ssh_host: str = Field(default="", alias="SAGENT_SSH_HOST")
    sagent_ssh_user: str = Field(default="", alias="SAGENT_SSH_USER")
    sagent_ssh_key: str = Field(default="~/.ssh/id_ed25519", alias="SAGENT_SSH_KEY")
    sagent_ssh_port: int = Field(default=22, alias="SAGENT_SSH_PORT")
    sagent_is_remote: bool = Field(default=False, alias="SAGENT_IS_REMOTE")

    # External services (presence-checked, not stored in full)
    jira_server_url: str = Field(default="", alias="JIRA_SERVER_URL")
    jira_username: str = Field(default="", alias="JIRA_USERNAME")
    jira_api_token: str = Field(default="", alias="JIRA_API_TOKEN")
    gitlab_url: str = Field(default="https://gitlab.com", alias="GITLAB_URL")
    gitlab_token: str = Field(default="", alias="GITLAB_TOKEN")
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    slack_bot_token: str = Field(default="", alias="SLACK_BOT_TOKEN")

    @model_validator(mode="after")
    def _auto_detect_remote(self) -> "Settings":
        """Auto-detect whether we are running on the remote server.

        On Windows we are never "on" a Linux remote, regardless of what the
        env var says, so we force False.  Otherwise, if SAGENT_IS_REMOTE was
        not explicitly set, we compare the local hostname to ssh_host.
        """
        if platform.system() == "Windows":
            self.sagent_is_remote = False
            return self

        explicit = os.environ.get("SAGENT_IS_REMOTE", "").lower()
        if explicit not in ("true", "1", "yes"):
            hostname = socket.gethostname()
            self.sagent_is_remote = bool(
                self.sagent_ssh_host and hostname.startswith(self.sagent_ssh_host.split(".")[0])
            )
        return self

    @property
    def sagent_workspace_posix(self) -> PurePosixPath:
        """Return the remote workspace as a PurePosixPath (safe on any OS)."""
        return PurePosixPath(self.sagent_workspace)

    @property
    def sagent_ssh_key_path(self) -> Path:
        """Return the SSH key as a local Path with ~ expanded."""
        return Path(self.sagent_ssh_key).expanduser()

    @property
    def has_jira(self) -> bool:
        return bool(self.jira_api_token and self.jira_server_url)

    @property
    def has_gitlab(self) -> bool:
        return bool(self.gitlab_token)

    @property
    def has_github(self) -> bool:
        return bool(self.github_token)

    @property
    def has_slack(self) -> bool:
        return bool(self.slack_bot_token)

    model_config = {"populate_by_name": True, "extra": "ignore"}


def load_settings(repo_root: Path | None = None, env_file: Path | None = None) -> Settings:
    """Load settings from .env file and environment variables."""
    root = repo_root or _find_repo_root()
    dotenv_path = env_file or root / ".env"

    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=False)

    return Settings(repo_root=root)
