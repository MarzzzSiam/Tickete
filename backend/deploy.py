"""Small demo deployment supervisor: all jobs share the free web instance.

This is not an always-on worker. Render suspends all children while idle;
durable ticket jobs resume after the next visitor wakes the service.
"""

import os
import signal
import subprocess
import sys
import time


def main():
    if os.environ.get("STORAGE_BACKEND") != "supabase":
        raise SystemExit("Hosted deployment requires persistent Supabase storage.")
    if os.environ.get("EMAIL_PROVIDER") != "brevo":
        raise SystemExit("Free hosted deployment requires the HTTPS email provider.")
    subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)
    commands = [
        [
            "gunicorn",
            "config.wsgi:application",
            "--bind",
            f"0.0.0.0:{os.environ.get('PORT', '10000')}",
            "--workers",
            "1",
            "--threads",
            "2",
            "--timeout",
            "120",
        ],
        [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "config",
            "worker",
            "--pool=solo",
            "--concurrency=1",
            "--loglevel=warning",
            "--without-gossip",
            "--without-mingle",
        ],
        [sys.executable, "manage.py", "process_ticket_jobs"],
    ]
    children = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for command in commands:
            children.append(subprocess.Popen(command))
        while not stopping:
            if any(child.poll() is not None for child in children):
                raise SystemExit("A service process stopped; restarting the instance is required.")
            time.sleep(1)
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        deadline = time.monotonic() + 20
        for child in children:
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
