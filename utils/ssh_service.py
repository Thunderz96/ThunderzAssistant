"""
SSH Service — Thunderz Assistant Phase 2

Singleton SSH client with connection pooling.
Provides remote script execution and SFTP file upload via paramiko.

Usage (from Lab_planner_module.py):
    from ssh_service import ssh_execute, ssh_upload
    ssh_execute(ip, user, pw, command, on_line_cb, on_done_cb)
    ssh_upload(ip, user, pw, content_str, remote_path, on_done_cb)
"""

import threading
import io
from typing import Callable, Dict, Optional

try:
    import paramiko
    _PARAMIKO_AVAILABLE = True
except ImportError:
    _PARAMIKO_AVAILABLE = False


class SSHService:
    """Singleton SSH client with per-host connection pooling.

    Connections are keyed by "user@ip" and reused across calls.
    All execution and upload operations run on daemon threads so the
    tkinter main thread is never blocked.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._pool: Dict[str, object] = {}   # "user@ip" → paramiko.SSHClient
        self._pool_lock = threading.Lock()

    # ── Internal connection management ────────────────────────────────────────

    def _get_connection(self, host_ip: str, username: str, password: str):
        """Return a live SSHClient, reusing from pool if still active."""
        if not _PARAMIKO_AVAILABLE:
            raise RuntimeError(
                "paramiko is not installed.\n"
                "Run:  pip install paramiko>=3.4.0")

        key = f"{username}@{host_ip}"
        with self._pool_lock:
            client = self._pool.get(key)
            if client:
                transport = client.get_transport()
                if transport and transport.is_active():
                    return client
                # Stale connection — close and reconnect
                try:
                    client.close()
                except Exception:
                    pass
                del self._pool[key]

            # Establish new connection
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                host_ip,
                username=username,
                password=password,
                timeout=15,
                banner_timeout=30,
                auth_timeout=20,
            )
            self._pool[key] = client
            return client

    def _remove_from_pool(self, host_ip: str, username: str):
        key = f"{username}@{host_ip}"
        with self._pool_lock:
            client = self._pool.pop(key, None)
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    # ── Public API ─────────────────────────────────────────────────────────────

    def execute(
        self,
        host_ip: str,
        username: str,
        password: str,
        command: str,
        on_line_cb: Callable[[str, bool], None],
        on_done_cb: Callable[[int], None],
        on_channel_cb: Optional[Callable] = None,
    ) -> None:
        """Execute *command* on the remote host.

        Runs in a daemon thread.  Calls:
          on_line_cb(line: str, is_stderr: bool)  — for each output line
          on_done_cb(exit_code: int)              — when command finishes
            exit_code == -1  →  SSH / runtime error
            exit_code == -2  →  cancelled by user (channel.close() called)
          on_channel_cb(channel)                  — fired immediately after
            exec_command so the caller can store a reference and call
            channel.close() to cancel the running command at any time.
        """

        def _run():
            channel = None
            try:
                client = self._get_connection(host_ip, username, password)
                # get_pty=True merges stderr into stdout and enables progress
                # bars / colour output from apt, docker, etc.
                _, stdout, _ = client.exec_command(command, get_pty=True)
                channel = stdout.channel
                if on_channel_cb:
                    on_channel_cb(channel)
                for raw_line in iter(stdout.readline, ""):
                    if raw_line:
                        on_line_cb(raw_line.rstrip("\r\n"), False)
                # If the channel was closed externally the readline sentinel
                # fires before recv_exit_status — detect and report cancelled.
                if channel.closed:
                    on_done_cb(-2)
                    return
                exit_code = channel.recv_exit_status()
                on_done_cb(exit_code)
            except Exception as exc:
                # A closed channel may raise during readline — treat as cancel.
                if channel is not None and channel.closed:
                    on_done_cb(-2)
                else:
                    on_line_cb(f"SSH Error: {exc}", True)
                    # Drop the pool entry so the next attempt reconnects clean
                    self._remove_from_pool(host_ip, username)
                    on_done_cb(-1)

        threading.Thread(target=_run, daemon=True).start()

    def upload_file(
        self,
        host_ip: str,
        username: str,
        password: str,
        content: str,
        remote_path: str,
        on_done_cb: Callable[[bool], None],
    ) -> None:
        """Upload *content* (string) to *remote_path* via SFTP.

        Runs in a daemon thread.
        Calls on_done_cb(True) on success, on_done_cb(False) on failure.
        The remote parent directory is created automatically via SSH first.
        """

        def _upload():
            try:
                client = self._get_connection(host_ip, username, password)
                # Ensure remote parent directory exists
                remote_dir = remote_path.rsplit("/", 1)[0]
                if remote_dir:
                    _, stdout, _ = client.exec_command(
                        f"mkdir -p {remote_dir}", get_pty=False)
                    stdout.channel.recv_exit_status()
                # SFTP upload
                sftp = client.open_sftp()
                try:
                    sftp.putfo(io.BytesIO(content.encode("utf-8")), remote_path)
                finally:
                    sftp.close()
                on_done_cb(True)
            except Exception as exc:
                print(f"[SSHService] upload_file error: {exc}")
                self._remove_from_pool(host_ip, username)
                on_done_cb(False)

        threading.Thread(target=_upload, daemon=True).start()

    def close_all(self) -> None:
        """Close all pooled connections.  Call on app shutdown."""
        with self._pool_lock:
            for client in self._pool.values():
                try:
                    client.close()
                except Exception:
                    pass
            self._pool.clear()


# ── Module-level singleton & convenience wrappers ─────────────────────────────

_ssh_service = SSHService()


def ssh_execute(
    host_ip: str,
    username: str,
    password: str,
    command: str,
    on_line_cb: Callable[[str, bool], None],
    on_done_cb: Callable[[int], None],
    on_channel_cb: Optional[Callable] = None,
) -> None:
    """Execute *command* on *host_ip*.  Non-blocking (daemon thread).

    Pass *on_channel_cb* to receive the paramiko Channel immediately after
    exec_command — store it and call channel.close() to cancel the command.
    """
    _ssh_service.execute(host_ip, username, password, command,
                         on_line_cb, on_done_cb, on_channel_cb)


def ssh_upload(
    host_ip: str,
    username: str,
    password: str,
    content: str,
    remote_path: str,
    on_done_cb: Callable[[bool], None],
) -> None:
    """Upload *content* string to *remote_path* on *host_ip*.  Non-blocking."""
    _ssh_service.upload_file(host_ip, username, password, content,
                             remote_path, on_done_cb)


def ssh_close_all() -> None:
    """Close all pooled SSH connections."""
    _ssh_service.close_all()


def ssh_available() -> bool:
    """Returns True if paramiko is installed."""
    return _PARAMIKO_AVAILABLE
