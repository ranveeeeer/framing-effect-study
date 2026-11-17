"""
Ask every model every question, many times, and log every reply.

Usage (from the project folder):
    python src/run_models.py --list-models          # check model names
    python src/run_models.py --dry-run              # show prompts and counts, no calls
    python src/run_models.py --pilot claude-haiku-5-5   # 1 call per condition, one model
    python src/run_models.py                        # the full run
    python src/run_models.py --models gpt-6-luna    # only some models
    python src/run_models.py --mock                 # fake models, free, for testing

The run is resumable: every finished call is saved straight away, and
calls already in the log are skipped. If it crashes or you stop it with
Ctrl+C, just run the same command again.
"""

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from config import FRAMES, MAX_OUTPUT_TOKENS, MOCK_MODELS, MODELS, MODES, N_RUNS, model_dirs
from items import SCENARIOS, build_prompt
from providers import ask, list_models, parse_answer

write_lock = threading.Lock()


def plan_calls(n_runs):
    """
    Every condition we need, for one model.
    Within each set of runs, the option order alternates:
    even runs show the sure option first, odd runs the risky one first.
    """
    calls = []
    for scenario in SCENARIOS:
        for frame in FRAMES:
            for mode in MODES:
                for run in range(n_runs):
                    order = "sure_first" if run % 2 == 0 else "risky_first"
                    calls.append({"scenario": scenario, "frame": frame,
                                  "mode": mode, "run": run, "order": order})
    return calls


def call_key(c):
    return (c["scenario"], c["frame"], c["mode"], c["run"])


def already_done(log_path):
    """Read the log and return the set of calls that are finished."""
    done = set()
    if log_path.exists():
        with open(log_path) as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("final"):
                    done.add(call_key(rec))
    return done


def ask_with_retry(model_cfg, prompt, tries=6):
    """Call the model; on rate limits or network errors wait and try again."""
    wait = 5
    for attempt in range(tries):
        try:
            return ask(model_cfg, prompt, MAX_OUTPUT_TOKENS)
        except Exception as e:
            # A wrong model name, a bad key or a bad request won't fix itself.
            status = getattr(e, "status_code", None) or getattr(e, "code", None)
            if status in (400, 401, 403, 404) or attempt == tries - 1:
                raise
            print(f"  ! {model_cfg['name']}: {type(e).__name__}: {str(e)[:120]} - retrying in {wait}s")
            time.sleep(wait)
            wait = min(wait * 2, 120)


def run_one(model_cfg, c, log_path):
    """
    One condition: send the prompt, check the answer can be read.
    If it can't, ask once more. Both attempts are logged; the last one is
    marked "final".
    """
    prompt, letter_meaning = build_prompt(c["scenario"], c["frame"], c["mode"], c["order"])
    tokens = 0
    for attempt in (1, 2):
        result = ask_with_retry(model_cfg, prompt)
        letter = parse_answer(result["reply"])
        final = letter is not None or attempt == 2
        record = {
            "model": model_cfg["name"],
            "provider": model_cfg["provider"],
            "size": model_cfg["size"],
            **c,
            "attempt": attempt,
            "final": final,
            "prompt": prompt,
            "reply": result["reply"],
            "letter": letter,
            "choice": letter_meaning.get(letter) if letter else None,
            "reasoning_setting": result["reasoning_setting"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with write_lock:
            with open(log_path, "a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        tokens += result["input_tokens"] + result["output_tokens"]
        if final:
            return tokens


def run_model(model_cfg, calls, raw_dir, workers):
    log_path = raw_dir / f"{model_cfg['name']}.jsonl"
    done = already_done(log_path)
    todo = [c for c in calls if call_key(c) not in done]
    print(f"\n{model_cfg['name']}: {len(done)} done, {len(todo)} to go")
    if not todo:
        return

    total_tokens = 0
    finished = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_one, model_cfg, c, log_path) for c in todo]
        for fut in as_completed(futures):
            total_tokens += fut.result()
            finished += 1
            if finished % 25 == 0 or finished == len(todo):
                print(f"  {finished}/{len(todo)} calls, {total_tokens:,} tokens so far")


def main():
    parser = argparse.ArgumentParser(description="Run the framing-effect prompts on AI models.")
    parser.add_argument("--list-models", action="store_true", help="print the model names each provider offers")
    parser.add_argument("--dry-run", action="store_true", help="show sample prompts and call counts, no API calls")
    parser.add_argument("--pilot", metavar="MODEL", help="1 call per condition for one model")
    parser.add_argument("--models", nargs="+", help="only run these models")
    parser.add_argument("--mock", action="store_true", help="use the fake models (free)")
    parser.add_argument("--workers", type=int, default=4, help="calls sent at the same time per model")
    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    models = MOCK_MODELS if args.mock else MODELS
    if args.models:
        models = [m for m in models if m["name"] in args.models]

    n_runs = N_RUNS
    dirs = model_dirs(mock=args.mock)
    raw_dir = dirs["raw"]

    if args.pilot:
        models = [m for m in models if m["name"] == args.pilot]
        n_runs = 2  # one of each option order
        raw_dir = raw_dir.parent / "pilot"

    if not models:
        print("No matching model. Check the name against config.py.")
        return

    calls = plan_calls(n_runs)

    if args.dry_run:
        print(f"{len(models)} models x {len(calls)} calls = {len(models) * len(calls)} calls in total\n")
        for c in [calls[0], calls[n_runs]]:
            prompt, meaning = build_prompt(c["scenario"], c["frame"], c["mode"], c["order"])
            print(f"--- {c} -> {meaning}\n{prompt}\n")
        return

    raw_dir.mkdir(parents=True, exist_ok=True)
    for m in models:
        run_model(m, calls, raw_dir, args.workers)
    print(f"\nDone. Logs are in {raw_dir}")


if __name__ == "__main__":
    main()
