# config.py
import toml
import os


class Config:
    CONFIG_FILE = os.getenv("CONFIG_FILE", "./config.toml")
    configurations = toml.load(CONFIG_FILE)
    MONITORING_INTERVAL = configurations['monitoring']['interval']
    PROCESSING_INTERVAL = configurations['processing']['interval']

    DATABASE_URL = os.getenv("DATABASE_URL", configurations['database']['url'])
    EBPF_SCRIPT = os.getenv("EBPF_SCRIPT", "./signal_collection/monitor_lifecyle_events.sh")
    PS_SCRIPT_PATH = os.getenv("PS_SCRIPT_PATH", "./signal_collection/metrics_collection.sh")
