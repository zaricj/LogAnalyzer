import os
from src.commands import commands
from src.config import config

APP_NAME = "name_me"

if os.name == "posix":
    DATA_PATH = os.path.join(
        os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), APP_NAME
    )
    CONFIG_PATH = os.path.join(
        os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), APP_NAME
    )
else:
    raise Exception("Not supported OS, only POSIX currently")


class Controller:
    def __init__(self):
        self.config_default = self.load_config()
        self.init_directories()

    def init_directories(self):
        if not os.path.exists(DATA_PATH):
            os.mkdir(DATA_PATH)
        if not os.path.exists(CONFIG_PATH):
            os.mkdir(CONFIG_PATH)

    def read_arguments(self):
        args = commands(self)
        args.func(args)

    def load_config(self):
        return config()

    def command_version(self):
        print("Version: Under developement")
