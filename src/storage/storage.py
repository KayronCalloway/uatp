import json
import os

from src.capsule_schema import Capsule

CAPSULES_DIR = os.path.join(os.path.dirname(__file__), "..", "capsules")


class CapsuleStorage:
    @staticmethod
    def save_capsule(capsule):
        capsule_dict = capsule.to_dict()
        filename = os.path.join(CAPSULES_DIR, f"{capsule.capsule_id}.json")
        with open(filename, "w") as f:
            json.dump(capsule_dict, f, indent=2)
        return filename

    @staticmethod
    def load_capsule(capsule_id):
        filename = os.path.join(CAPSULES_DIR, f"{capsule_id}.json")
        with open(filename) as f:
            data = json.load(f)
        return Capsule.from_dict(data)

    @staticmethod
    def list_capsules():
        files = [
            f
            for f in os.listdir(CAPSULES_DIR)
            if f.endswith(".json") and f != "schema.json"
        ]
        capsules = []
        for fname in files:
            with open(os.path.join(CAPSULES_DIR, fname)) as f:
                data = json.load(f)
                capsules.append(Capsule.from_dict(data))
        return capsules
