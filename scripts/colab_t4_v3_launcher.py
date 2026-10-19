"""Paste this whole file into ONE Colab cell, select a T4 GPU, and run.

Runs the separately frozen v3 cap-127 experiment. Saves and downloads a ZIP
of evidence/logs even on failure; never includes model weights or caches.
This launcher does not change or rerun the frozen v2 experiment.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import zipfile

SOURCE_COMMIT = "1b54e3cbf78d7732a2986dd216bcb758e01ddc56"
MODEL = "Qwen/Qwen2.5-1.5B"
MODEL_REVISION = "8faed761d45a263340a0528343f099c05c9a4323"
MAXIMUM_CAP = 127
REPOSITORY = "https://github.com/towre676-cloud/singularity.git"
EVIDENCE_NAMES = {"protocol.json", "selection_started.json", "observations.json", "frozen_panels.json",
                  "package.json", "certificate.json", "results.json", "numerical_health.json", "infeasible.json"}


def utc():
    return datetime.now(timezone.utc).isoformat()


def execute(command, log_path, label):
    """Stream subprocess output and print a heartbeat during silent phases."""
    print("\n" + label, flush=True)
    started = time.monotonic()
    messages = queue.Queue()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1)

    def read():
        for line in process.stdout:
            messages.put(line)
        messages.put(None)

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        with log_path.open("a") as log:
            log.write("\n" + label + "\n" + json.dumps(command) + "\n")
            while True:
                try:
                    line = messages.get(timeout=20)
                except queue.Empty:
                    print(f"Still running: {label} ({int(time.monotonic()-started)} seconds)", flush=True)
                    continue
                if line is None:
                    break
                print(line, end="", flush=True)
                log.write(line)
                log.flush()
        if process.wait():
            raise RuntimeError(label + " failed; the ZIP will retain the error log and any partial evidence")
    finally:
        # A stopped notebook cell must not leave an orphan GPU process running.
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        reader.join(timeout=2)
        process.stdout.close()


def save_archive(folder, evidence, status):
    """Use a file allowlist: never archive scratch exports or model caches."""
    files = sorted(p for p in evidence.iterdir() if p.is_file() and p.name in EVIDENCE_NAMES) if evidence.exists() else []
    status["evidence_files_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (folder / "launcher_status.json").write_text(json.dumps(status, indent=2) + "\n")
    archive = folder.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in files:
            output.write(path, "evidence/" + path.name)
        for name in ("execution.log", "environment.txt", "hardware.json", "launcher_status.json"):
            path = folder / name
            if path.is_file():
                output.write(path, name)
    return archive


def print_results(evidence):
    result = json.loads((evidence / "results.json").read_text())
    print("\nVERIFIED V3 RESULT — this run, not a projected cost", flush=True)
    for name, panel in result["comparison"]["panels"].items():
        row = result["evaluation"][name]
        print(f"{name}: {panel['cost']} tokens; meets all coverage requirements: {panel['satisfies_requirement']}; "
              f"clean false alarms: {len(row['false_alarms'])}")
        print("  New held-out cases missed:", ", ".join(row["new_heldout_missed"]) or "none")
    print("Numerical-health failures:", json.dumps(result["numerical_health"]))
    print("Uniform logit translation is an intentionally invisible control in exact arithmetic.")
    print("Token cost is recorded; this experiment does not measure standalone-panel latency.")


def main():
    root = Path("/content") if Path("/content").is_dir() else Path.cwd()
    folder = root / ("singularity_v3_t4_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
    folder.mkdir()
    checkout, evidence = folder / "source_checkout", folder / "evidence"
    log = folder / "execution.log"
    status = {"started_at_utc": utc(), "source_commit": SOURCE_COMMIT, "model": MODEL,
              "expected_model_revision": MODEL_REVISION, "maximum_cap": MAXIMUM_CAP, "verified": False,
              "claim_boundary": "Fresh hardware coverage/clean controls; no standalone-panel timing or semantic equivalence claim."}
    error = None
    try:
        probe = subprocess.run([sys.executable, "-c", "import json,torch; print(json.dumps({'cuda':torch.cuda.is_available(),'torch':torch.__version__,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))"],
                               capture_output=True, text=True)
        if probe.returncode:
            raise RuntimeError("Colab's CUDA PyTorch is unavailable. Select Runtime > Change runtime type > T4 GPU.")
        machine = json.loads(probe.stdout.strip().splitlines()[-1])
        (folder / "hardware.json").write_text(json.dumps(machine, indent=2) + "\n")
        if not machine["cuda"] or "T4" not in (machine["gpu"] or ""):
            raise RuntimeError("This launcher expects a T4. Select Runtime > Change runtime type > T4 GPU and run again.")
        print("Using", machine["gpu"], "with Colab's existing CUDA PyTorch", machine["torch"], flush=True)
        execute([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade-strategy", "only-if-needed",
                 "transformers>=4.57,<6", "safetensors>=0.4", "accelerate>=1,<2", "bitsandbytes"], log,
                "Preparing model dependencies (keeping the installed CUDA PyTorch when compatible)")
        frozen = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
        (folder / "environment.txt").write_text(frozen.stdout)
        execute(["git", "init", "--quiet", str(checkout)], log, "Creating a separate source checkout")
        execute(["git", "-C", str(checkout), "remote", "add", "origin", REPOSITORY], log, "Connecting the public source")
        execute(["git", "-C", str(checkout), "fetch", "--quiet", "--depth", "1", "origin", SOURCE_COMMIT], log,
                "Fetching the immutable, tested v3 source")
        execute(["git", "-C", str(checkout), "checkout", "--quiet", "--detach", "FETCH_HEAD"], log, "Selecting the pinned code")
        actual = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        if actual != SOURCE_COMMIT:
            raise RuntimeError("source identity mismatch")
        # V3 resolves the model SHA itself. Refuse an unnoticed checkpoint change
        # before freezing; verify the frozen SHA too. No monkey-patching of v3.
        preflight = "import torch,accelerate,bitsandbytes; from transformers import AutoTokenizer,AutoModelForCausalLM; from huggingface_hub import HfApi; got=HfApi().model_info(" + repr(MODEL) + ").sha; print('Model revision:',got,flush=True); assert got==" + repr(MODEL_REVISION) + ", 'Model revision changed: this run must be reviewed before comparison with v2'"
        execute([sys.executable, "-u", "-c", preflight], log, "Checking CUDA dependencies and the original Qwen checkpoint")
        runner = str(checkout / "scripts/colab_deployment_audit_v3.py")
        execute([sys.executable, "-u", runner, "--phase", "freeze", "--model", MODEL,
                 "--maximum-cap", str(MAXIMUM_CAP), "--output", str(evidence)], log, "Freezing the v3 protocol before inference")
        protocol = json.loads((evidence / "protocol.json").read_text())
        if protocol["revision"] != MODEL_REVISION or protocol["dtype"] != "float16":
            raise RuntimeError("frozen checkpoint or dtype differs from the intended T4 comparison")
        execute([sys.executable, "-u", runner, "--phase", "run", "--output", str(evidence)], log,
                "Running reference, calibration, construction, frozen selection and evaluation")
        execute([sys.executable, "-u", runner, "--phase", "verify", "--output", str(evidence)], log,
                "Independently replaying the saved evidence and exact-optimum certificates")
        status["verified"] = True
        print_results(evidence)
    except BaseException as failure:
        status["error"] = type(failure).__name__ + ": " + str(failure)
        error = failure
        print("\nRun incomplete:", failure, flush=True)
    finally:
        status["finished_at_utc"] = utc()
        archive = save_archive(folder, evidence, status)
        print("\nEvidence ZIP:", archive, flush=True)
        if not status["verified"]:
            print("This ZIP is labelled incomplete. It contains diagnostics, not a successful result.", flush=True)
        try:
            from google.colab import files
            files.download(str(archive))
        except ImportError:
            pass
        except Exception as download_error:
            print("Automatic download did not start. Download the ZIP from Colab's Files panel:", download_error)
    if isinstance(error, (KeyboardInterrupt, SystemExit)):
        raise error
    if error:
        raise RuntimeError("The v3 run stopped; inspect the downloaded diagnostic ZIP.") from error


if __name__ == "__main__":
    main()
