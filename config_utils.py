import os
import yaml
from pydantic import BaseModel, ValidationError
from pathlib import Path


class GlobalConfig(BaseModel):
    llm: dict
    langfuse: dict
    diagnosis: dict

def load_config(config_path: str = "config.yaml") -> GlobalConfig:

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found, please check the path: {config_file.absolute()}")
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise Exception(f"Configuration file YAML format error:{e}")
    

    try:
        return GlobalConfig(** config_dict)
    except ValidationError as e:
        raise Exception(f"Configuration file structure error (missing key/wrong type):{e}")

def init_langfuse_env(config: GlobalConfig):
    os.environ["LANGFUSE_PUBLIC_KEY"] = config.langfuse["public_key"]
    os.environ["LANGFUSE_SECRET_KEY"] = config.langfuse["secret_key"]
    os.environ["LANGFUSE_BASE_URL"] = config.langfuse["base_url"]
    print("✅ Langfuse environment variable initialization completed")