"""Reproduce original fixtures and measured decisions without external services."""
import argparse
import hashlib
import json
from pathlib import Path
import core

ROOT = Path(__file__).resolve().parent

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode())

def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    data = core.generate()
    metrics, raw, model, report = core.experiment(data)
    dump(output / "input.json", data)
    dump(output / "metrics.json", metrics)
    dump(output / "decisions.json", raw)
    if model is not None:
        dump(output / "model.json", model)
    (output / "report.md").write_bytes(report.encode())
    artifacts = ["input.json", "metrics.json", "decisions.json", "report.md"]
    if model is not None:
        artifacts.append("model.json")
    manifest = {
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                          for p in ["core.py", "run.py", "data/dataset.json"]},
        "artifact_sha256": {p: hashlib.sha256((output / p).read_bytes()).hexdigest() for p in artifacts}}
    dump(output / "manifest.json", manifest)
    print(json.dumps(metrics, indent=2))
    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    run(parser.parse_args().output)
