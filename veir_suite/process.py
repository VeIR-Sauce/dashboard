"""Bounded subprocess execution; only processes started here are terminated."""
from __future__ import annotations

import os
from pathlib import Path
import selectors
import signal
import subprocess
import time


def _stop(process: subprocess.Popen) -> None:
    # start_new_session gives this invocation its own group, including descendants.
    # The PID comes directly from Popen, never a process-name search.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def execute(command: list[str], *, cwd: Path, timeout: float = 15,
            output_limit: int = 1024 * 1024, env: dict | None = None) -> dict:
    start = time.monotonic()
    record = {"command": [str(x) for x in command], "kind": "exit", "exit_code": None,
              "stdout": "", "stderr": "", "seconds": 0.0}
    try:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    except (OSError, ValueError) as error:
        record.update(kind="not_found", stderr=str(error))
        return record
    outputs = {"stdout": bytearray(), "stderr": bytearray()}
    used = 0
    try:
        with selectors.DefaultSelector() as selector:
            for name in outputs:
                pipe = getattr(process, name)
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            while selector.get_map():
                remaining = timeout - (time.monotonic() - start)
                if remaining <= 0:
                    record["kind"] = "timeout"
                    _stop(process)
                    break
                for key, _ in selector.select(min(0.1, remaining)):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    available = max(0, output_limit - used)
                    outputs[key.data].extend(chunk[:available])
                    used += len(chunk)
                    if used > output_limit:
                        record["kind"] = "output_limit"
                        _stop(process)
                        break
                if record["kind"] != "exit":
                    break
            if record["kind"] == "exit":
                try:
                    process.wait(timeout=max(0.001, timeout - (time.monotonic() - start)))
                except subprocess.TimeoutExpired:
                    record["kind"] = "timeout"
                    _stop(process)
            record["exit_code"] = process.returncode
            if record["kind"] == "exit" and process.returncode < 0:
                record["kind"] = "crash"
    finally:
        # Also clean up a child that outlives a normally exiting parent. Its
        # process group is the one created by this Popen call, never a name match.
        _stop(process)
        process.stdout.close()
        process.stderr.close()
    record.update({name: bytes(value).decode("utf-8", errors="replace") for name, value in outputs.items()})
    record["seconds"] = round(time.monotonic() - start, 6)
    return record


def process_problem(record: dict) -> str | None:
    return {"not_found": "ENV_ERROR", "timeout": "TIMEOUT", "crash": "CRASH",
            "output_limit": "OUTPUT_LIMIT"}.get(record["kind"])
