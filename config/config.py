import json

class Config:
    _config = None

    @classmethod
    def load_config(cls):
        if cls._config is None:
            with open('config/config.json', 'r') as config_file:
                cls._config = json.load(config_file)
        return cls._config
    

config = Config.load_config()
# Usage
# config = Config.load_config()
