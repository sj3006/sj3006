import json
import os
import sys
import types

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gpu"))
import run_gpu  # noqa: E402

T4 = dict(name="Tesla T4", mem=15.6, cc=[7, 5])
A100 = dict(name="A100", mem=85.1, cc=[8, 0])
L4 = dict(name="L4", mem=24.0, cc=[8, 9])


def _run(**kw):
    a = dict(dtype=None, device=None, batch=None, score_batch=None)
    a.update(kw)
    return types.SimpleNamespace(args=types.SimpleNamespace(**a))


def test_kaggle_two_t4s_split_a_7b_model_in_float16():
    p = run_gpu.plan(_run(), dict(gpus=[T4, T4]), 7.25e9, {})
    assert p["dtype"] == "float16" and p["device"] == "auto" and p["score_batch"] == 16


def test_a100_keeps_a_7b_model_on_one_card_in_bfloat16():
    p = run_gpu.plan(_run(), dict(gpus=[A100]), 7.6e9, {})
    assert p["dtype"] == "bfloat16" and p["device"] == "cuda" and p["batch"] == 160


def test_l4_fits_a_7b_model_and_one_t4_does_not():
    assert run_gpu.plan(_run(), dict(gpus=[L4]), 7.25e9, {})["device"] == "cuda"
    with pytest.raises(RuntimeError):
        run_gpu.plan(_run(), dict(gpus=[T4]), 7.25e9, {})


def test_a_model_started_in_bfloat16_is_not_resumed_on_a_t4():
    with pytest.raises(RuntimeError):
        run_gpu.plan(_run(), dict(gpus=[T4, T4]), 7.25e9, {"dtype": "bfloat16"})
    assert run_gpu.plan(_run(), dict(gpus=[T4, T4]), 7.25e9, {"dtype": "float16"})["dtype"] == "float16"


def test_param_count_reads_safetensors_headers(tmp_path):
    header = {"a": {"dtype": "F16", "shape": [3, 4], "data_offsets": [0, 24]},
              "b": {"dtype": "F16", "shape": [5], "data_offsets": [24, 34]},
              "__metadata__": {"format": "pt"}}
    raw = json.dumps(header).encode()
    (tmp_path / "model.safetensors").write_bytes(len(raw).to_bytes(8, "little") + raw + b"\0" * 34)
    assert run_gpu.param_count(str(tmp_path)) == 17


def test_seconds_per_setting_and_settings_count(tmp_path):
    log = tmp_path / "s.log"
    log.write_text("Loading\n[1/144] T=0.2 top_p=0.5 rep4>0.2: 0.1  NLL>3.5: 0.0  (20s)\n"
                   "[2/144] T=0.2 top_p=0.545 rep4>0.2: 0.1  NLL>3.5: 0.0  (33s)\n")
    assert run_gpu.seconds_per_setting(str(log)) == 13
    np.savez(tmp_path / "s.npz", **{"0_0": np.zeros((2, 3)), "0_1": np.zeros((2, 3))},
             temps=np.zeros(12), tops=np.zeros(12))
    assert run_gpu.n_settings(str(tmp_path / "s.npz")) == 2
