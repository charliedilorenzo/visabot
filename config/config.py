import sys
from dataclasses import dataclass
from distutils.util import strtobool
from typing import Dict, Optional

import dotenv
from discord.ext.commands import Bot

EXPECTED_ENV_VALUES = set(["server", "token"])

ACCEPTED_KEYS = set(
    ["test_mode", "spam_channel", "bot_status_channel", "dev_id"]
).union(EXPECTED_ENV_VALUES)


@dataclass
class Config:
    token: str
    server: int
    spam_channel: str
    bot_status_channel: str
    dev_id: Optional[int] = None
    command_prefix: str = "visabot"
    sync_commands_globally: bool = True
    test_mode: bool = True


class ConfigedBot(Bot):
    def __init__(self, config: Config, command_prefix: str, **kwargs):
        kwargs["guilds"] = [config.server]
        super().__init__(command_prefix, **kwargs)
        self.config = config


def load_env():
    env_values: Dict[str, str] = dotenv.dotenv_values(".env")
    config_dict = {key.lower(): value for key, value in env_values.items()}
    found_env_keys = EXPECTED_ENV_VALUES.intersection(set(config_dict.keys()))
    missing_env_keys = EXPECTED_ENV_VALUES - found_env_keys
    if missing_env_keys:
        # something like - 'SERVER', 'TOKEN'
        missing_keys_string = "', '".join(missing_env_keys)
        print(f"Env requires keys: '{missing_keys_string}'")
        sys.exit(1)
    unexpected_keys = found_env_keys - ACCEPTED_KEYS
    if len(unexpected_keys) > 0:
        print(f"Found unexpected keys: {unexpected_keys}")
        sys.exit(1)
    config_dict["test_mode"] = strtobool(config_dict.pop("test_mode", True)) == 1
    config_dict["sync_commands_globally"] = (
        strtobool(config_dict.pop("sync_commands_globally", True)) == 1
    )
    config_dict["server"] = int(config_dict.pop("server"))
    if config_dict.get("dev_id"):
        config_dict["dev_id"] = int(config_dict.pop("dev_id"))
    config = Config(**config_dict)
    return config


CONFIG = load_env()
