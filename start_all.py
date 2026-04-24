#!/usr/bin/env python3
"""Bring up the full Z-Alpha stack on Docker Desktop's built-in Kubernetes.

Flow: load .env -> build images -> apply manifests -> seed database -> wait
for rollouts. Secrets are generated from .env and applied via stdin, never
written to disk. Assumes `kubectl` context points at `docker-desktop`.
"""

import base64
import datetime
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

NAMESPACE = "zalpha"
EXPECTED_CONTEXT = "docker-desktop"
# Per-run image tag. With a stable `:local` tag, kubelet keeps reusing the
# cached image under that name and never notices the rebuild. A fresh tag
# makes `kubectl set image` see a real change and triggers a real rollout.
IMAGE_TAG = datetime.datetime.now().strftime("r%Y%m%d%H%M%S")
BACKEND_IMAGE = f"zalpha-backend:{IMAGE_TAG}"
FRONTEND_IMAGE = f"zalpha-frontend:{IMAGE_TAG}"
REQUIRED_ENV = ["POSTGRES_PASSWORD", "ADMIN_PASSWORD", "USER_PASSWORD", "AUTH_SECRET"]


def setup_logging():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"run_{ts}.log"

    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(log_path, encoding="utf-8")):
        h.setFormatter(fmt)
        root.addHandler(h)
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    for old in sorted(logs_dir.glob("run_*.log"), key=lambda p: p.stat().st_mtime)[:-20]:
        try: old.unlink()
        except Exception: pass

    logger.info("Run %s | log: %s", ts, log_path)


def load_env_file():
    for candidate in (".env", "config.env"):
        path = Path(candidate)
        if not path.exists():
            continue
        logger.info("Loading env from %s", candidate)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().split("#", 1)[0].strip().strip('"')
            os.environ.setdefault(key.strip(), value)
        return
    logger.warning("No .env found. Copy config.env.example and fill it in.")


def _run(cmd, input_=None, check=True, capture=False):
    logger.info("$ %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        input=input_,
        text=True,
        capture_output=capture,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    if capture and result.stdout:
        for line in result.stdout.splitlines():
            logger.info(line)
    if check and result.returncode != 0:
        if capture and result.stderr:
            logger.error(result.stderr.strip())
        raise RuntimeError(f"command failed (exit {result.returncode}): {' '.join(cmd)}")
    return result


def check_tools():
    missing = [t for t in ("docker", "kubectl") if not shutil.which(t)]
    if missing:
        logger.error("Missing CLI tools on PATH: %s", ", ".join(missing))
        sys.exit(1)


def check_env():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        logger.error("Missing env vars: %s", ", ".join(missing))
        sys.exit(1)


def check_context():
    """kubectl context must point at docker-desktop's built-in cluster."""
    ctx = _run(["kubectl", "config", "current-context"], capture=True, check=False).stdout.strip()
    if ctx != EXPECTED_CONTEXT:
        logger.error("kubectl context is '%s', expected '%s'", ctx or "(none)", EXPECTED_CONTEXT)
        logger.error("  Enable Kubernetes in Docker Desktop settings, then:")
        logger.error("  kubectl config use-context %s", EXPECTED_CONTEXT)
        sys.exit(1)
    logger.info("kubectl context: %s", ctx)


def check_ibkr():
    import socket
    host = os.environ.get("IBKR_HOST", "127.0.0.1")
    port = int(os.environ.get("IBKR_PORT", "7496"))
    try:
        with socket.create_connection((host, port), timeout=5):
            logger.info("IBKR TWS reachable at %s:%s", host, port)
            return
    except (OSError, socket.timeout) as e:
        logger.error("IBKR TWS not reachable at %s:%s (%s) -- start TWS with API enabled", host, port, e)
        sys.exit(1)


def build_images():
    _run(["docker", "build", "-f", "Dockerfile.backend",  "-t", BACKEND_IMAGE,  "."])
    _run(["docker", "build", "-f", "Dockerfile.frontend", "-t", FRONTEND_IMAGE, "."])


def apply_manifests():
    _run(["kubectl", "apply", "-f", "deploy/namespace.yaml"])
    _apply_secrets()
    for f in ("postgres.yaml", "user-api.yaml", "backend.yaml", "frontend.yaml"):
        _run(["kubectl", "apply", "-f", f"deploy/{f}"])


def set_images():
    """Point each Deployment at the freshly-built tag. `set image` bumps the
    PodSpec so K8s does a real rollout (unlike `rollout restart` which would
    just reuse whatever image is cached under the stable tag)."""
    updates = [
        ("backend",  "backend",  BACKEND_IMAGE),
        ("user-api", "user-api", BACKEND_IMAGE),
        ("frontend", "frontend", FRONTEND_IMAGE),
    ]
    for deploy, container, image in updates:
        _run(["kubectl", "-n", NAMESPACE, "set", "image",
              f"deployment/{deploy}", f"{container}={image}"])


def _apply_secrets():
    """Render a Secret from .env and pipe it through `kubectl apply -f -`.
    Using base64 `data:` so arbitrary characters in secrets are safe."""
    def b64(s: str) -> str:
        return base64.b64encode(s.encode("utf-8")).decode("ascii")

    body = (
        "apiVersion: v1\n"
        "kind: Secret\n"
        f"metadata:\n  name: zalpha-secrets\n  namespace: {NAMESPACE}\n"
        "type: Opaque\ndata:\n"
        + "".join(f"  {k}: {b64(os.environ[k])}\n" for k in REQUIRED_ENV)
    )
    _run(["kubectl", "apply", "-f", "-"], input_=body)


def wait_ready(name, timeout="180s"):
    _run(["kubectl", "-n", NAMESPACE, "rollout", "status", f"deployment/{name}", f"--timeout={timeout}"])


def seed_database():
    logger.info("Seeding database inside the backend pod...")
    _run(["kubectl", "-n", NAMESPACE, "exec", "deploy/backend", "--", "python", "setup_database.py"])


def main():
    setup_logging()
    load_env_file()
    check_env()
    check_tools()
    check_context()
    check_ibkr()

    logger.info("=" * 60)
    logger.info("Z-ALPHA on docker-desktop Kubernetes")
    logger.info("=" * 60)

    build_images()
    apply_manifests()
    set_images()

    wait_ready("postgres")
    wait_ready("backend")
    seed_database()
    wait_ready("user-api")
    wait_ready("frontend")

    logger.info("=" * 60)
    logger.info("Running:")
    logger.info("  Frontend  http://localhost:3000")
    logger.info("  Backend   http://localhost:8000")
    logger.info("  User API  http://localhost:8001")
    logger.info("Teardown: kubectl delete namespace %s", NAMESPACE)
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyboardInterrupt) as e:
        logger.error("%s", e)
        sys.exit(1)
