"""
Health Polling Service — Thunderz Assistant

Global singleton that polls all IPAM hosts on a background thread.
Started by main.py at boot.  Persists results to service_health_log.
Fires notifications via notification_manager on state transitions.

Other modules import the convenience functions at the bottom of this file:
    from health_service import start_health_service, get_health_status, ...
"""

import threading
import time
import socket
import subprocess
from datetime import datetime
from typing import Dict, List, Callable, Optional

import database_manager as db


# ── Data class ────────────────────────────────────────────────────────────────

class ServiceStatus:
    """Immutable snapshot of a single service's health-check result."""
    __slots__ = ('ip', 'hostname', 'port', 'online', 'latency_ms', 'checked_at')

    def __init__(self, ip: str, hostname: str, port: str,
                 online: bool, latency_ms: int, checked_at: str):
        self.ip = ip
        self.hostname = hostname
        self.port = port
        self.online = online
        self.latency_ms = latency_ms
        self.checked_at = checked_at

    @property
    def key(self) -> str:
        """Composite key used to identify this service uniquely."""
        return f"{self.ip}:{self.port}" if self.port else self.ip


# ── Singleton service ─────────────────────────────────────────────────────────

class HealthService:
    """
    Background health-polling service.

    Lifecycle
    ---------
    1. main.py calls ``start_health_service(root)`` during init.
    2. A daemon thread polls every ``poll_interval`` seconds.
    3. Each cycle: read ip_allocations → check each host → persist to
       service_health_log → detect transitions → fire notifications.
    4. UI modules register / unregister observer callbacks for live updates.
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

        self.poll_interval: int = 60            # seconds between automatic polls
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._root = None                        # tk root, for .after() marshaling

        # Current state: "ip:port" → ServiceStatus
        self._current_status: Dict[str, ServiceStatus] = {}

        # Previous online state for transition detection: "ip:port" → bool
        self._previous_online: Dict[str, bool] = {}

        # Suppress notifications on the very first poll cycle
        self._initial_poll_complete: bool = False

        # Prevent two poll cycles from overlapping
        self._poll_lock = threading.Lock()

        # Observers called after each completed poll cycle
        self._observers: List[Callable] = []
        self._observer_lock = threading.Lock()

        self._initialized = True

    # ── Public API ────────────────────────────────────────────────────────

    def start(self, root) -> None:
        """Start the polling thread.  Called once from main.py."""
        if self._running:
            return
        self._root = root
        db.init_db()
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the polling thread gracefully."""
        self._running = False

    def get_current_status(self) -> Dict[str, "ServiceStatus"]:
        """Return a snapshot of the latest poll results."""
        return dict(self._current_status)

    def run_poll_now(self) -> None:
        """Trigger an immediate out-of-band poll cycle."""
        threading.Thread(target=self._do_poll_cycle, daemon=True).start()

    def register_observer(self, callback: Callable) -> None:
        with self._observer_lock:
            if callback not in self._observers:
                self._observers.append(callback)

    def unregister_observer(self, callback: Callable) -> None:
        with self._observer_lock:
            if callback in self._observers:
                self._observers.remove(callback)

    # ── Internal ──────────────────────────────────────────────────────────

    def _poll_loop(self) -> None:
        """Background loop: poll, sleep, repeat."""
        while self._running:
            try:
                self._do_poll_cycle()
            except Exception as e:
                print(f"[HealthService] poll error: {e}")
            # Sleep in 1-second ticks so stop() is responsive
            for _ in range(self.poll_interval):
                if not self._running:
                    return
                time.sleep(1)

    def _do_poll_cycle(self) -> None:
        """One full poll: read hosts, check, persist, notify."""
        if not self._poll_lock.acquire(blocking=False):
            return                       # another cycle already running
        try:
            self._poll_cycle_inner()
        finally:
            self._poll_lock.release()

    def _poll_cycle_inner(self) -> None:
        hosts = db.execute_query(
            "SELECT ip_address, hostname, port, device_type "
            "FROM ip_allocations ORDER BY ip_address"
        ) or []

        if not hosts:
            return                       # IPAM empty — nothing to poll

        results: Dict[str, ServiceStatus] = {}
        result_lock = threading.Lock()

        def check_one(ip, hostname, port):
            online, latency = self._check_host(ip, port)
            status = ServiceStatus(
                ip=ip, hostname=hostname, port=port,
                online=online, latency_ms=latency,
                checked_at=datetime.now().isoformat(),
            )
            with result_lock:
                results[status.key] = status

        threads: list[threading.Thread] = []
        for ip, hostname, port, _dtype in hosts:
            t = threading.Thread(target=check_one,
                                 args=(ip, hostname, port), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        # Persist every result to the health log
        for _key, status in results.items():
            db.execute_query(
                "INSERT INTO service_health_log "
                "(ip_address, hostname, port, online, latency_ms, checked_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (status.ip, status.hostname, status.port,
                 1 if status.online else 0, status.latency_ms,
                 status.checked_at),
            )

        # Detect transitions (skip on the very first poll)
        if self._initial_poll_complete:
            self._detect_transitions(results)

        # Update internal state
        self._current_status = results
        self._previous_online = {k: s.online for k, s in results.items()}

        if not self._initial_poll_complete:
            self._initial_poll_complete = True

        # Notify observers on the main thread
        self._notify_observers()

    # ── Host check ────────────────────────────────────────────────────────

    @staticmethod
    def _check_host(ip: str, port: str) -> tuple:
        """Check a single host.  Returns ``(online, latency_ms)``."""
        start = time.time()
        online = False
        try:
            if port:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((ip, int(port)))
                sock.close()
                online = (result == 0)
            else:
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "2000", ip],
                    capture_output=True, timeout=5,
                )
                online = (result.returncode == 0)
        except Exception:
            online = False
        latency_ms = int((time.time() - start) * 1000)
        return online, latency_ms

    # ── Transition detection ──────────────────────────────────────────────

    def _detect_transitions(self, new_results: Dict[str, ServiceStatus]) -> None:
        """Compare new results against previous state; fire notifications."""
        # Lazy import to avoid circular dependencies at load time
        from notification_manager import send_notification

        for key, status in new_results.items():
            prev = self._previous_online.get(key)
            if prev is None:
                continue                 # new host appeared — skip

            label = status.hostname or status.ip
            port_str = f":{status.port}" if status.port else ""

            if prev and not status.online:
                # ── went offline ──
                send_notification(
                    title=f"{label} went OFFLINE",
                    message=f"{status.ip}{port_str} is unreachable.",
                    module="Lab Planner",
                    notification_type="error",
                    play_sound=True,
                )
            elif not prev and status.online:
                # ── recovered ──
                send_notification(
                    title=f"{label} is back ONLINE",
                    message=(f"{status.ip}{port_str} recovered "
                             f"({status.latency_ms} ms)."),
                    module="Lab Planner",
                    notification_type="success",
                    play_sound=True,
                )

    # ── Observer dispatch ─────────────────────────────────────────────────

    def _notify_observers(self) -> None:
        with self._observer_lock:
            observers = list(self._observers)
        for cb in observers:
            try:
                if self._root:
                    self._root.after(0, cb)
                else:
                    cb()
            except Exception as e:
                print(f"[HealthService] observer error: {e}")


# ── Module-level singleton + convenience functions ────────────────────────────

_health_service = HealthService()


def start_health_service(root) -> None:
    """Start the global health polling service.  Called from main.py."""
    _health_service.start(root)


def stop_health_service() -> None:
    """Stop the global health polling service."""
    _health_service.stop()


def get_health_status() -> Dict[str, ServiceStatus]:
    """Snapshot of current health status for all hosts."""
    return _health_service.get_current_status()


def trigger_health_poll() -> None:
    """Trigger an immediate health poll cycle."""
    _health_service.run_poll_now()


def register_health_observer(callback: Callable) -> None:
    """Register a callback invoked after each poll cycle."""
    _health_service.register_observer(callback)


def unregister_health_observer(callback: Callable) -> None:
    """Unregister a health observer."""
    _health_service.unregister_observer(callback)
