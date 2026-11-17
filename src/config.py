"""
Settings for the whole project, kept in one place.

If you want to change which models are tested, or how many times each
question is asked, change it here, not inside the other scripts.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Models to test: one flagship and one small model from each lab.
#
# Model names change often. Before the real run, check them with:
#     python src/run_models.py --list-models
# and fix any name below that the provider doesn't recognise.
#
# "reasoning" is the setting we ask for so that built-in thinking is OFF
# (or as low as the model allows). We want the prompt to be the only
# difference between the "direct" and "step_by_step" modes. If a model
# rejects the setting, the runner falls back to the model's default and
# records that in the log.
# ---------------------------------------------------------------------------
MODELS = [
    {"name": "claude-opus-5-5",       "provider": "anthropic", "size": "flagship", "reasoning": "disabled"},
    {"name": "claude-haiku-5-5",      "provider": "anthropic", "size": "small",    "reasoning": "disabled"},
    {"name": "gpt-6-astra",           "provider": "openai",    "size": "flagship", "reasoning": "none"},
    {"name": "gpt-6-luna",            "provider": "openai",    "size": "small",    "reasoning": "none"},
    {"name": "gemini-4-argon",        "provider": "google",    "size": "flagship", "reasoning": "low"},
    {"name": "gemini-3.5-flash-lite", "provider": "google",    "size": "small",    "reasoning": "minimal"},
]

# Two fake models for testing the pipeline without spending money.
# Used only with the --mock flag.
MOCK_MODELS = [
    {"name": "mock-biased",   "provider": "mock", "size": "flagship", "reasoning": "none"},
    {"name": "mock-unbiased", "provider": "mock", "size": "small",    "reasoning": "none"},
]

FRAMES = ["gain", "loss"]
MODES = ["direct", "step_by_step"]
N_RUNS = 30            # runs per model x scenario x frame x mode
MAX_OUTPUT_TOKENS = 2000

# Students: the first 15 valid responses per form (by time submitted).
N_STUDENTS_PER_FRAME = 15

# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
STUDENT_DIR = ROOT / "data" / "students"


def model_dirs(mock=False):
    """Where model data and results go. Mock runs are kept separate."""
    if mock:
        data = ROOT / "data" / "mock"
        results = ROOT / "results" / "mock"
    else:
        data = ROOT / "data" / "models"
        results = ROOT / "results"
    return {
        "raw": data / "raw",
        "responses": data / "responses.csv",
        "tables": results / "tables",
        "figures": results / "figures",
    }
