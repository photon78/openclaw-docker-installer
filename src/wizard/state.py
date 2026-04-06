"""
WizardState — carries all user input through the wizard steps.
Everything user-specific lives here as variables, never hardcoded.
"""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WizardState:
    # System
    home_dir: Path = field(default_factory=Path.home)
    username: str = field(default_factory=lambda: Path.home().name)
    openclaw_dir: Path = field(init=False)

    # API Keys
    anthropic_api_key: str = ""
    mistral_api_key: str = ""       # optional, but recommended for skills
    primary_provider_id: str = ""   # e.g. "openai", "google", "xai"
    primary_api_key: str = ""       # key for non-anthropic/non-mistral providers
    telegram_bot_token: str = ""    # optional, set per channel

    # Channel
    channel: str = ""              # "telegram" | "discord" | "signal"
    channel_allow_from: list[str] = field(default_factory=list)

    # Agent
    agent_name: str = "main"
    agent_emoji: str = "🤖"

    # Security
    security_profile: str = "strict"   # "strict" | "standard" | "custom"

    # Backup
    backup_enabled: bool = True
    backup_mount_path: str = ""        # e.g. "/mnt/backup"

    # LLM tiers
    llm_budget: str = "mistral/mistral-large-latest"
    llm_standard: str = "anthropic/claude-sonnet-4-6"
    llm_power: str = "anthropic/claude-opus-4-6"
    llm_media: str = "mistral/mistral-large-latest"

    def __post_init__(self) -> None:
        self.openclaw_dir = self.home_dir / ".openclaw"

    @property
    def workspace_dir(self) -> Path:
        return self.openclaw_dir / "workspace"

    @property
    def scripts_dir(self) -> Path:
        return self.openclaw_dir / "scripts"

    @property
    def env_file(self) -> Path:
        return self.openclaw_dir / ".env"
