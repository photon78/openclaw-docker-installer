"""
WizardState — carries all user input through the wizard steps.
Everything user-specific lives here as variables, never hardcoded.
"""
import getpass
from dataclasses import dataclass, field
from pathlib import Path


def _default_username() -> str:
    """Return the current OS username (cross-platform)."""
    try:
        return getpass.getuser()
    except Exception:
        return Path.home().name


@dataclass
class WizardState:
    # System
    home_dir: Path = field(default_factory=Path.home)
    username: str = field(default_factory=_default_username)
    openclaw_dir: Path = field(init=False)

    # API Keys
    anthropic_api_key: str = ""
    mistral_api_key: str = ""       # optional, but recommended for skills
    aki_api_key: str = ""           # optional, for aki/kimi-k2.7-code-1100b
    brave_web_search_api_key: str = ""  # optional, Brave web-search plugin
    openclaw_gateway_auth_token: str = ""  # auto-generated if empty
    primary_provider_id: str = ""   # e.g. "openai", "google", "xai"
    primary_api_key: str = ""       # key for non-anthropic/non-mistral providers
    kimi_api_key: str = ""          # Moonshot Kimi K2.6
    openai_api_key: str = ""        # OpenAI GPT-5.5 Codex
    ollama_host: str = ""           # Ollama host URL (e.g. http://172.16.50.19:11434)
    telegram_bot_token: str = ""    # set when channel == telegram (legacy name)
    telegram_bot_token_default: str = ""   # TELEGRAM_BOT_TOKEN_DEFAULT in .env
    discord_bot_token: str = ""     # set when channel == discord
    signal_number: str = ""          # set when channel == signal

    # Channel
    channel: str = ""              # "telegram" | "discord" | "signal"
    channel_allow_from: list[str] = field(default_factory=list)

    # Agent
    agent_name: str = "main"
    agent_emoji: str = "🤖"

    # User profile
    user_display_name: str = ""        # how the agent addresses the user
    user_timezone: str = "UTC"         # IANA timezone
    user_tech_level: str = ""          # free text from wizard

    # Persona
    persona_style: str = "direct"   # "direct" | "formal" | "friendly" | "skip"

    # Security
    security_profile: str = "strict"   # "strict" | "standard" | "custom"
    auto_allow_skills: bool = False    # autoAllowSkills in exec-approvals.json (default: off for security)

    # Backup
    backup_enabled: bool = True
    backup_mount_path: str = ""        # e.g. "/mnt/backup"

    # Script Registry
    script_registry_enabled: bool = True
    script_sync_enabled: bool = True
    allowlist_sync_enabled: bool = True
    allowlist_auto_apply: bool = True
    safe_exec_check_enabled: bool = True

    # Dry-run mode — write to tempdir, skip Docker and systemd
    dry_run: bool = False

    # LLM tiers
    llm_budget: str = "mistral/mistral-large-latest"
    llm_standard: str = "anthropic/claude-sonnet-4-6"
    llm_power: str = "anthropic/claude-opus-4-6"
    llm_media: str = "mistral/mistral-large-latest"
    llm_kimi: str = "moonshot/kimi-k2.6"
    llm_gemma4: str = "ollama/gemma4_26_Q5KS"
    llm_qwen3: str = "ollama/qwen3.6_27b"
    llm_codex: str = "openai/gpt-5.5"

    # Gateway auth (generated during install, written to .env)
    gateway_token: str = ""

    # Container-side paths (Docker maps host openclaw_dir → /home/node/.openclaw)
    # Scripts and agent templates that run INSIDE the container must use these.
    CONTAINER_OPENCLAW_DIR: Path = Path("/home/node/.openclaw")

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

    @property
    def gateway_auth_token(self) -> str:
        """Return the gateway auth token, generating one if necessary."""
        if not self.openclaw_gateway_auth_token:
            import secrets as _secrets
            self.openclaw_gateway_auth_token = _secrets.token_hex(32)
        return self.openclaw_gateway_auth_token

    @property
    def container_workspace_dir(self) -> Path:
        """Path to workspace as seen from INSIDE the Docker container."""
        return self.CONTAINER_OPENCLAW_DIR / "workspace"

    @property
    def container_scripts_dir(self) -> Path:
        """Path to agent scripts inside the container (workspace/scripts/).

        NOTE: /home/node/.openclaw/scripts/ is the SYSTEM scripts dir (read-only mount).
        Agent scripts (check_tasks.py, health_check.py, add_agent.py) live in
        workspace/scripts/ which is read-write.
        """
        return self.CONTAINER_OPENCLAW_DIR / "workspace" / "scripts"
