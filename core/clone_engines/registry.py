from core.clone_engines.sopro_engine import SoproEngine
from core.clone_engines.xtts_engine import XTTSEngine


class CloneRegistry:

    def __init__(self, prosody_engine):
        self.engines = {
            "sopro": SoproEngine(prosody_engine),
            "xtts": XTTSEngine(prosody_engine),
        }

    def get(self, name):
        return self.engines.get(name)