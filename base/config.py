import sys
from dataclasses import dataclass, field
from distutils.util import strtobool
from inspect import Parameter, Signature, signature
from typing import Dict, Optional

import dotenv
from discord.ext.commands import Bot
from pydantic import BaseModel

EXPECTED_ENV_VALUES = set(["server", "token"])

ACCEPTED_KEYS = set(
    [
        "test_mode",
        "spam_channel",
        "bot_status_channel",
        "dev_id",
        # "test_config",
        # "config"
    ]
).union(EXPECTED_ENV_VALUES)


@dataclass
class Config:
    test_mode: True
    token: str
    server: int
    spam_channel: str
    bot_status_channel: str
    dev_id: Optional[str] = None
    command_prefix: str = "visabot"
    sync_commands_globally: bool = False


class ConfigedBot(Bot):
    def __init__(self, config: Config, command_prefix: str, **kwargs):
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
    extra_keys = found_env_keys - ACCEPTED_KEYS
    if len(extra_keys) > 0:
        print(f"Found extra keys: {extra_keys}")
        sys.exit(1)
    config_dict["test_mode"] = strtobool(config_dict.pop("test_mode", True)) == 1
    config_dict["server"] = int(config_dict.pop("server"))
    config = Config(**config_dict)
    return config


CONFIG = load_env()
