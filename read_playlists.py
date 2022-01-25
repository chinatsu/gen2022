import json
from types import SimpleNamespace

def load(week):
    with open(f"reports/week_{week}.json", encoding="utf-8") as f:
        return json.load(f, object_hook=lambda d: SimpleNamespace(**d))


