import importlib.util
import sys
import types
from pathlib import Path


def _load_module(path: str, name: str):
    torch_stub = types.SimpleNamespace(float16="float16", float32="float32", cuda=types.SimpleNamespace(is_available=lambda: False))
    transformers_stub = types.SimpleNamespace(AutoTokenizer=object, AutoModelForCausalLM=object)

    sys.modules.setdefault("torch", torch_stub)
    sys.modules.setdefault("transformers", transformers_stub)

    spec = importlib.util.spec_from_file_location(name, Path(path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_extract_pred_requires_final_token_and_reads_last_number():
    mod = _load_module("part2_generate_trajectories.py", "part2_generate_trajectories")

    assert mod.extract_pred("Reasoning... 12 <FINAL>") == "12"
    assert mod.extract_pred("Reasoning... 2 then 13 <FINAL>") == "13"
    assert mod.extract_pred("No final token so should not parse 99") is None


def test_extract_pred_supports_negative_and_decimal_values():
    mod = _load_module("part2_generate_trajectories.py", "part2_generate_trajectories")

    assert mod.extract_pred("Compute... -3.5 <FINAL>") == "-3.5"
