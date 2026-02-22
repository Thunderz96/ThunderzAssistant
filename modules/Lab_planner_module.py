"""
Lab Deployment Center — Thunderz Assistant

Tabs:
  🌐 Network Mapper  — IPAM with UniFi sync, port tracking, SSH launcher
  🐳 Docker Stacks   — Compose editor/store with copy-to-clipboard
  🏥 Service Health  — Live ping/HTTP status for all IPAM entries
  📓 Runbook         — Per-project freeform lab notes / journal
  🔑 Credentials     — PIN-gated local credential store
  📜 Script Vault    — Categorised deployment scripts
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import socket
import subprocess
import hashlib
import base64
import os
import time
import requests
import urllib3
import database_manager as db

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Lab network config (git-ignored) ──────────────────────────────────────────
_LAB_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'lab_config.json')

def _load_lab_config() -> dict:
    """Load lab_config.json from the data/ folder (git-ignored).
    Returns an empty dict if the file doesn't exist yet."""
    try:
        if os.path.exists(_LAB_CONFIG_PATH):
            import json
            with open(_LAB_CONFIG_PATH, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


# ── Docker Compose defaults ────────────────────────────────────────────────────
_DEFAULT_STACKS = [
    ("Portainer CE",
     """services:
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./portainer-data:/data
    ports:
      - 9000:9000
      - 8000:8000""",
     "Not Deployed", "Docker management UI — deploy this first"),
    ("Pi-Hole",
     """services:
  pihole:
    container_name: pihole
    image: pihole/pihole:latest
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "80:80/tcp"
    environment:
      TZ: 'America/New_York'
      WEBPASSWORD: 'your_secure_password'
    volumes:
      - './etc-pihole:/etc/pihole'
      - './etc-dnsmasq.d:/etc/dnsmasq.d'
    restart: unless-stopped""",
     "Not Deployed", "Network-wide ad blocking + local DNS"),
    ("Plex Media Server",
     """services:
  plex:
    image: lscr.io/linuxserver/plex:latest
    container_name: plex
    network_mode: host
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
      - VERSION=docker
    volumes:
      - ./plex-config:/config
      - /mnt/unas_storage/media:/data/media
    restart: unless-stopped""",
     "Not Deployed", "Media server — mounts NAS share at /mnt/unas_storage/media"),
    ("Nginx Proxy Manager",
     """services:
  npm:
    image: jc21/nginx-proxy-manager:latest
    container_name: nginx-proxy-manager
    restart: unless-stopped
    ports:
      - 80:80
      - 81:81
      - 443:443
    volumes:
      - ./npm-data:/data
      - ./npm-letsencrypt:/etc/letsencrypt""",
     "Not Deployed", "Reverse proxy with SSL — access services by subdomain"),
    ("Uptime Kuma",
     """services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    container_name: uptime-kuma
    restart: always
    ports:
      - 3001:3001
    volumes:
      - ./uptime-kuma-data:/app/data""",
     "Not Deployed", "Self-hosted service health monitor"),
]

_STATUS_COLOURS = {
    "Running":      "#2E7D32",
    "Stopped":      "#B71C1C",
    "Not Deployed": "#5D4037",
    "Updating":     "#1565C0",
}

# Default runbook notes seeded on first run
_DEFAULT_NOTES = [
    ("Proxmox Initial Setup",
     "## Proxmox Initial Setup\n\n"
     "### Post-install checklist\n"
     "- [ ] Disable enterprise repo (use Script Vault → Proxmox Free Repo Setup)\n"
     "- [ ] Run apt update && apt dist-upgrade\n"
     "- [ ] Set static IP on proxmox host\n"
     "- [ ] Create non-root admin user\n"
     "- [ ] Enable IOMMU if GPU passthrough needed\n\n"
     "### IPs assigned\n"
     "- Proxmox Web UI: https://<PROXMOX_IP>:8006\n\n"
     "### Notes\n"
     "(record your decisions here — storage layout, VM IDs, etc.)"),
    ("Docker Host Setup",
     "## Docker Host Setup\n\n"
     "### Checklist\n"
     "- [ ] Install Docker & Compose (Script Vault → Install Docker & Compose)\n"
     "- [ ] Deploy Portainer CE first (Docker Stacks tab)\n"
     "- [ ] Create /mnt/unas_storage and mount SMB share\n"
     "- [ ] Deploy Pi-Hole\n"
     "- [ ] Point router DNS to <DOCKER_IP>\n"
     "- [ ] Deploy Plex\n\n"
     "### PUID / PGID\n"
     "Run `id` on the docker host and record here:\n"
     "- PUID: \n"
     "- PGID: \n\n"
     "### Notes\n"),
    ("Pi-Hole Config",
     "## Pi-Hole Configuration Notes\n\n"
     "- Web UI: http://<DOCKER_IP>/admin\n"
     "- DNS set on router: <DOCKER_IP>\n\n"
     "### Blocklists added\n"
     "(paste URLs here)\n\n"
     "### Local DNS records added\n"
     "(e.g. proxmox.lan → <PROXMOX_IP>)\n\n"
     "### Notes\n"),
]

# Default credentials seeded on first run (placeholders only)
_DEFAULT_CREDS = [
    ("Proxmox Root",        "root",  "",  "https://<PROXMOX_IP>:8006",  "Proxmox web UI login"),
    ("Pi-Hole Web",         "admin", "",  "http://<DOCKER_IP>/admin",   "Pi-Hole dashboard — set WEBPASSWORD in compose"),
    ("Portainer Admin",     "admin", "",  "http://<DOCKER_IP>:9000",    "Created on first Portainer boot"),
    ("Home Assistant",      "",      "",  "http://<DOCKER_IP>:8123",    "Home Assistant dashboard"),
    ("Uptime Kuma",         "",      "",  "http://<DOCKER_IP>:3001",    "Uptime Kuma dashboard"),
    ("UNAS2 SMB",           "",      "",  "//<NAS_IP>",                 "NAS SMB share credentials"),
    ("UniFi Network App",   "admin", "",  "https://<GATEWAY_IP>",       "UniFi local admin"),
]


def _pin_hash(pin: str) -> str:
    """SHA-256 hash of the PIN — used only for unlock verification."""
    return hashlib.sha256(pin.encode()).hexdigest()


def _make_fernet_key(pin: str, salt: bytes) -> Fernet:
    """Derive a 32-byte Fernet key from the PIN using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(pin.encode()))
    return Fernet(key)


def _encrypt_password(pin: str, salt: bytes, plaintext: str) -> str:
    """Return Fernet-encrypted ciphertext as a UTF-8 string (empty → empty)."""
    if not plaintext:
        return ""
    return _make_fernet_key(pin, salt).encrypt(plaintext.encode()).decode()


def _decrypt_password(pin: str, salt: bytes, ciphertext: str) -> str:
    """Decrypt a Fernet ciphertext. Returns plaintext, or the original value
    on failure (handles legacy plaintext rows gracefully)."""
    if not ciphertext:
        return ""
    try:
        return _make_fernet_key(pin, salt).decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        # Legacy plaintext row — return as-is so the user can re-save to encrypt
        return ciphertext


class LabPlannerModule:
    ICON     = "🏗️"
    PRIORITY = 4

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        self._vault_unlocked = False   # credentials vault state

        db.init_db()
        self._seed_initial_data()
        self._configure_styles()
        self.create_ui()

    # ── Styles ────────────────────────────────────────────────────────────────

    def _configure_styles(self):
        s = ttk.Style()
        s.theme_use('default')
        s.configure("TNotebook",     background=self.colors['background'], borderwidth=0)
        s.configure("TNotebook.Tab", background=self.colors['secondary'],
                    foreground=self.colors['text_dim'], padding=[14, 5],
                    font=("Segoe UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", self.colors['primary'])],
              foreground=[("selected", "white")])
        s.configure("Treeview", background=self.colors['card_bg'],
                    foreground=self.colors['text'],
                    fieldbackground=self.colors['card_bg'],
                    rowheight=25, borderwidth=0)
        s.configure("Treeview.Heading", background=self.colors['secondary'],
                    foreground=self.colors['text'],
                    font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("Treeview",
              background=[("selected", self.colors['accent'])],
              foreground=[("selected", "white")])
        s.map("Treeview.Heading",
              background=[("active", self.colors['primary'])])

    # ── Seed ──────────────────────────────────────────────────────────────────

    def _seed_initial_data(self):
        if not db.execute_query("SELECT * FROM ip_allocations"):
            # Load real IPs from lab_config.json (git-ignored) with safe fallbacks
            lab = _load_lab_config()
            gw   = lab.get("gateway_ip",  "192.168.1.1")
            px   = lab.get("proxmox_ip",  "YOUR_PROXMOX_IP")
            nas  = lab.get("nas_ip",      "YOUR_NAS_IP")
            dock = lab.get("docker_ip",   "YOUR_DOCKER_IP")

            for dev in [
                (gw,   'Cloud Gateway',  'Default', 'Gateway',    '',      'Main Router / UniFi Cloud Gateway'),
                (px,   'Proxmox-Host',   'Default', 'Hypervisor', '8006',  f'Proxmox Web UI — https://{px}:8006'),
                (nas,  'UNAS2',          'Default', 'NAS',        '445',   'Primary Storage / SMB share'),
                (dock, 'Pi-Hole',        'Default', 'Container',  '80',    f'Pi-Hole DNS — http://{dock}/admin'),
                (dock, 'Plex',           'Default', 'Container',  '32400', 'Plex Media Server'),
                (dock, 'Home Assistant',  'Default', 'Container',  '8123',  f'Home Assistant — http://{dock}:8123'),
                (dock, 'Uptime Kuma',    'Default', 'Container',  '3001',  f'Uptime Kuma — http://{dock}:3001'),
                (dock, 'Portainer',      'Default', 'Container',  '9000',  f'Portainer CE — http://{dock}:9000'),
            ]:
                db.execute_query(
                    'INSERT OR IGNORE INTO ip_allocations '
                    '(ip_address,hostname,vlan,device_type,port,notes) '
                    'VALUES (?,?,?,?,?,?)', dev)

        if not db.execute_query("SELECT * FROM scripts"):
            for title, content, cat in [
                ('Proxmox Free Repo Setup',
                 "sed -i 's/^/#/g' /etc/apt/sources.list.d/pve-enterprise.list\n"
                 "apt update && apt dist-upgrade -y", 'Proxmox'),
                ('Install Docker & Compose',
                 "curl -fsSL https://get.docker.com -o get-docker.sh\n"
                 "sudo sh get-docker.sh\nsudo usermod -aG docker $USER\nnewgrp docker",
                 'Linux'),
                ('Mount UNAS2 SMB Share',
                 "sudo apt install cifs-utils -y\nsudo mkdir -p /mnt/unas_storage\n"
                 "# Add to /etc/fstab:\n"
                 "# //YOUR_NAS_IP/YourShare /mnt/unas_storage cifs "
                 "username=USER,password=PASS,iocharset=utf8,file_mode=0777,dir_mode=0777 0 0\n"
                 "sudo mount -a", 'Linux'),
                ('Proxmox — Create Unprivileged LXC',
                 "pct create 100 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \\\n"
                 "  --hostname mycontainer --memory 512 --cores 1 \\\n"
                 "  --net0 name=eth0,bridge=vmbr0,ip=dhcp \\\n"
                 "  --storage local-lvm --rootfs local-lvm:8\npct start 100", 'Proxmox'),
                ('Proxmox — Enable IOMMU (GPU Passthrough prep)',
                 "sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=\"quiet\"/GRUB_CMDLINE_LINUX_DEFAULT=\"quiet "
                 "intel_iommu=on iommu=pt\"/' /etc/default/grub\nupdate-grub\n"
                 "echo -e 'vfio\\nvfio_iommu_type1\\nvfio_pci\\nvfio_virqfd' >> /etc/modules\n"
                 "update-initramfs -u -k all", 'Proxmox'),
            ]:
                db.execute_query(
                    'INSERT INTO scripts (title,content,category) VALUES (?,?,?)',
                    (title, content, cat))

        if not db.execute_query("SELECT * FROM docker_stacks"):
            for name, compose, status, notes in _DEFAULT_STACKS:
                db.execute_query(
                    'INSERT INTO docker_stacks (name,compose,status,notes) VALUES (?,?,?,?)',
                    (name, compose, status, notes))

        if not db.execute_query("SELECT * FROM lab_notes"):
            for title, content in _DEFAULT_NOTES:
                db.execute_query(
                    'INSERT INTO lab_notes (title,content) VALUES (?,?)',
                    (title, content))

        if not db.execute_query("SELECT * FROM credentials"):
            for label, user, pw, url, notes in _DEFAULT_CREDS:
                db.execute_query(
                    'INSERT INTO credentials (label,username,password,url,notes) '
                    'VALUES (?,?,?,?,?)',
                    (label, user, pw, url, notes))

    # ── Top-level UI ──────────────────────────────────────────────────────────

    def create_ui(self):
        tk.Label(self.parent, text="🏗️ Lab Deployment Center",
                 font=("Segoe UI", 16, "bold"),
                 bg=self.colors['background'], fg=self.colors['text']).pack(pady=10)

        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for attr, label, builder in [
            ('tab_ipam',    '🌐 Network Mapper', self.build_ipam_tab),
            ('tab_docker',  '🐳 Docker Stacks',  self.build_docker_tab),
            ('tab_health',  '🏥 Service Health', self.build_health_tab),
            ('tab_runbook', '📓 Runbook',         self.build_runbook_tab),
            ('tab_creds',   '🔑 Credentials',     self.build_credentials_tab),
            ('tab_scripts', '📜 Script Vault',    self.build_scripts_tab),
        ]:
            frame = tk.Frame(self.notebook, bg=self.colors['content_bg'])
            setattr(self, attr, frame)
            self.notebook.add(frame, text=label)
            builder()

    # ═════════════════════════════════════════════════════════════════════════
    # 🌐 NETWORK MAPPER (IPAM)
    # ═════════════════════════════════════════════════════════════════════════

    def build_ipam_tab(self):
        cols = ("IP", "Hostname", "VLAN", "Type", "Port", "Notes")
        self.ip_tree = ttk.Treeview(self.tab_ipam, columns=cols,
                                    show="headings", height=14)
        for col, w in zip(cols, [120, 140, 100, 110, 60, 260]):
            self.ip_tree.heading(col, text=col)
            self.ip_tree.column(col, width=w)

        sb = ttk.Scrollbar(self.tab_ipam, orient="vertical",
                           command=self.ip_tree.yview)
        self.ip_tree.configure(yscrollcommand=sb.set)
        self.ip_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                          padx=(10, 0), pady=10)
        sb.pack(side=tk.LEFT, fill=tk.Y, pady=10)
        self.ip_tree.bind("<Double-1>", lambda e: self.open_ip_modal(edit_mode=True))
        self.load_ip_data()

        btn = tk.Frame(self.tab_ipam, bg=self.colors['content_bg'])
        btn.pack(fill=tk.X, padx=10, pady=(0, 10))
        for text, bg, cmd in [
            ("＋ Add New IP",   self.colors['accent'],   lambda: self.open_ip_modal(False)),
            ("✏️ Edit Selected", self.colors['card_bg'],  lambda: self.open_ip_modal(True)),
            ("💻 SSH Connect",   self.colors['secondary'], self._ssh_connect),
            ("🔄 Sync UniFi",    self.colors['primary'],   self.trigger_unifi_sync),
        ]:
            fg = "white" if bg != self.colors['card_bg'] else self.colors['text']
            tk.Button(btn, text=text, bg=bg, fg=fg, relief=tk.FLAT,
                      cursor="hand2", command=cmd
                      ).pack(side=tk.LEFT, padx=(0, 6))

    def load_ip_data(self):
        for r in self.ip_tree.get_children():
            self.ip_tree.delete(r)
        rows = db.execute_query(
            "SELECT ip_address,hostname,vlan,device_type,port,notes "
            "FROM ip_allocations ORDER BY ip_address") or []
        for r in rows:
            self.ip_tree.insert("", tk.END, values=r)

    def open_ip_modal(self, edit_mode=False):
        vals = ("", "", "Default", "", "", "")
        orig_ip = ""
        orig_port = ""
        if edit_mode:
            sel = self.ip_tree.selection()
            if not sel:
                return
            vals      = self.ip_tree.item(sel[0], 'values')
            orig_ip   = vals[0]
            orig_port = vals[4] if len(vals) > 4 else ""

        dlg = tk.Toplevel(self.parent)
        dlg.title("Edit IP" if edit_mode else "Add IP")
        dlg.configure(bg=self.colors['background'])
        dlg.geometry("420x480")
        dlg.resizable(False, False)
        dlg.grab_set()

        entries = {}
        for label, key, default in [
            ("IP Address",                                        "ip",   vals[0]),
            ("Hostname",                                          "host", vals[1]),
            ("VLAN / Network  (leave 'Default' if not using VLANs)", "vlan", vals[2] or "Default"),
            ("Device Type  (e.g. Hypervisor, NAS, Container)",   "type", vals[3]),
            ("Service Port  (e.g. 8006, 9000 — optional)",       "port", vals[4] if len(vals) > 4 else ""),
            ("Notes",                                             "note", vals[5] if len(vals) > 5 else ""),
        ]:
            tk.Label(dlg, text=label, bg=self.colors['background'],
                     fg=self.colors['text'], font=("Segoe UI", 9)
                     ).pack(anchor="w", padx=20, pady=(9, 0))
            e = tk.Entry(dlg, bg=self.colors['card_bg'], fg=self.colors['text'],
                         insertbackground="white", relief=tk.FLAT, font=("Segoe UI", 10))
            e.pack(fill=tk.X, padx=20, pady=2)
            e.insert(0, default)
            entries[key] = e

        def save():
            ip = entries["ip"].get().strip()
            if not ip:
                messagebox.showwarning("Missing IP", "IP Address cannot be empty.", parent=dlg)
                return
            if edit_mode:
                db.execute_query(
                    "UPDATE ip_allocations SET ip_address=?,hostname=?,vlan=?,"
                    "device_type=?,port=?,notes=? "
                    "WHERE ip_address=? AND port=?",
                    (ip, entries["host"].get(), entries["vlan"].get(),
                     entries["type"].get(), entries["port"].get(),
                     entries["note"].get(), orig_ip, orig_port))
            else:
                r = db.execute_query(
                    "INSERT OR IGNORE INTO ip_allocations "
                    "(ip_address,hostname,vlan,device_type,port,notes) "
                    "VALUES (?,?,?,?,?,?)",
                    (ip, entries["host"].get(), entries["vlan"].get(),
                     entries["type"].get(), entries["port"].get(),
                     entries["note"].get()))
                if r is None:
                    messagebox.showerror("Duplicate Entry",
                        f"{ip}:{entries['port'].get()} already exists.",
                        parent=dlg)
                    return
            dlg.destroy()
            self.load_ip_data()

        br = tk.Frame(dlg, bg=self.colors['background'])
        br.pack(fill=tk.X, padx=20, pady=14)
        tk.Button(br, text="💾 Save", bg=self.colors['accent'], fg="white",
                  width=10, relief=tk.FLAT, cursor="hand2",
                  command=save).pack(side=tk.RIGHT, padx=4)
        tk.Button(br, text="Cancel", bg=self.colors['card_bg'],
                  fg=self.colors['text'], width=10, relief=tk.FLAT, cursor="hand2",
                  command=dlg.destroy).pack(side=tk.RIGHT, padx=4)
        if edit_mode:
            def delete():
                if messagebox.askyesno("Delete",
                        f"Remove {orig_ip} ({vals[1]})?", parent=dlg):
                    db.execute_query(
                        "DELETE FROM ip_allocations "
                        "WHERE ip_address=? AND port=?", (orig_ip, orig_port))
                    dlg.destroy()
                    self.load_ip_data()
            tk.Button(br, text="🗑 Delete", bg="#D32F2F", fg="white",
                      width=10, relief=tk.FLAT, cursor="hand2",
                      command=delete).pack(side=tk.LEFT, padx=4)

    # ── SSH Quick-Connect ─────────────────────────────────────────────────────

    def _ssh_connect(self):
        sel = self.ip_tree.selection()
        if not sel:
            messagebox.showinfo("No Selection",
                "Select a host in the table first.", parent=self.parent)
            return
        vals = self.ip_tree.item(sel[0], 'values')
        ip   = vals[0]
        host = vals[1] or ip

        dlg = tk.Toplevel(self.parent)
        dlg.title(f"SSH — {host}")
        dlg.configure(bg=self.colors['background'])
        dlg.geometry("340x180")
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text=f"Connect to  {host}  ({ip})",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors['background'], fg=self.colors['text']
                 ).pack(pady=(14, 6))

        user_row = tk.Frame(dlg, bg=self.colors['background'])
        user_row.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(user_row, text="Username:", width=10, anchor="w",
                 bg=self.colors['background'], fg=self.colors['text']
                 ).pack(side=tk.LEFT)
        user_var = tk.StringVar(value="root")
        tk.Entry(user_row, textvariable=user_var, width=18,
                 bg=self.colors['card_bg'], fg=self.colors['text'],
                 insertbackground="white", relief=tk.FLAT, font=("Segoe UI", 10)
                 ).pack(side=tk.LEFT, padx=6)

        def _launch(terminal):
            user = user_var.get().strip() or "root"
            target = f"{user}@{ip}"
            try:
                if terminal == "wt":
                    subprocess.Popen(["wt", "ssh", target])
                elif terminal == "putty":
                    subprocess.Popen(["putty", "-ssh", target])
                else:
                    subprocess.Popen(["cmd", "/c", "start", "cmd", "/k",
                                      f"ssh {target}"])
            except FileNotFoundError:
                messagebox.showerror("Not Found",
                    f"'{terminal}' not found on PATH.\n"
                    "Try a different terminal option.", parent=dlg)
            dlg.destroy()

        btn_row = tk.Frame(dlg, bg=self.colors['background'])
        btn_row.pack(pady=12)
        for label, term in [
            ("Windows Terminal", "wt"),
            ("PuTTY",            "putty"),
            ("CMD",              "cmd"),
        ]:
            tk.Button(btn_row, text=label,
                      bg=self.colors['primary'], fg="white",
                      relief=tk.FLAT, cursor="hand2",
                      command=lambda t=term: _launch(t)
                      ).pack(side=tk.LEFT, padx=4)

    # ── UniFi Sync ────────────────────────────────────────────────────────────

    def trigger_unifi_sync(self):
        ip  = db.execute_query("SELECT value FROM settings WHERE key='unifi_ip'")
        key = db.execute_query("SELECT value FROM settings WHERE key='unifi_api_key'")
        if not (ip and key):
            self.prompt_unifi_credentials()
        else:
            threading.Thread(target=self._run_unifi_sync,
                             args=(ip[0][0], key[0][0]), daemon=True).start()

    def prompt_unifi_credentials(self):
        dlg = tk.Toplevel(self.parent)
        dlg.title("UniFi API Config")
        dlg.configure(bg=self.colors['background'])
        dlg.geometry("360x220")
        dlg.resizable(False, False)
        dlg.grab_set()
        for label, show in [("Gateway IP (e.g. 192.168.1.1):", ""),
                             ("Local API Key (Network App → Settings):", "*")]:
            tk.Label(dlg, text=label, bg=self.colors['background'],
                     fg=self.colors['text']).pack(pady=(12, 0))
            e = tk.Entry(dlg, show=show, bg=self.colors['card_bg'],
                         fg=self.colors['text'], insertbackground="white",
                         relief=tk.FLAT, font=("Segoe UI", 10))
            e.pack(fill=tk.X, padx=20, pady=4)
            if not show:
                ip_e = e
            else:
                key_e = e

        def save_and_sync():
            db.execute_query(
                "INSERT OR REPLACE INTO settings (key,value) VALUES ('unifi_ip',?)",
                (ip_e.get().strip(),))
            db.execute_query(
                "INSERT OR REPLACE INTO settings (key,value) VALUES ('unifi_api_key',?)",
                (key_e.get().strip(),))
            dlg.destroy()
            self.trigger_unifi_sync()

        tk.Button(dlg, text="Save & Sync", bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2",
                  command=save_and_sync).pack(pady=12)

    def _run_unifi_sync(self, ip, api_key):
        s = requests.Session()
        s.headers.update({"Accept": "application/json", "X-API-Key": api_key})
        try:
            r = s.get(f"https://{ip}/proxy/network/integration/v1/sites",
                      verify=False, timeout=8)
            if r.status_code == 401:
                print("❌ 401 — use a LOCAL API key from Network App, not a Cloud key.")
                return
            if r.status_code != 200:
                print(f"❌ Sites: {r.status_code}")
                return
            sites = r.json().get('data', [])
            if not sites:
                print("❌ No sites found.")
                return
            site_id = sites[0].get('id', 'default')
            r2 = s.get(
                f"https://{ip}/proxy/network/integration/v1/sites/{site_id}/clients",
                verify=False, timeout=8)
            if r2.status_code != 200:
                print(f"❌ Clients: {r2.status_code}")
                return
            for c in r2.json().get('data', []):
                cip  = c.get('ip') or c.get('lastIp') or c.get('ipAddress')
                host = c.get('hostname') or c.get('name') or c.get('mac', 'Unknown')
                if not cip:
                    continue
                note = "Fixed IP" if c.get('isFixedIp') else "DHCP Client"
                # Only match portless rows so we don't clobber service entries
                if db.execute_query(
                        "SELECT id FROM ip_allocations "
                        "WHERE ip_address=? AND (port='' OR port IS NULL)", (cip,)):
                    db.execute_query(
                        "UPDATE ip_allocations SET hostname=?,vlan=?,notes=? "
                        "WHERE ip_address=? AND (port='' OR port IS NULL)",
                        (host, c.get('network', 'Default'), note, cip))
                else:
                    db.execute_query(
                        "INSERT OR IGNORE INTO ip_allocations "
                        "(ip_address,hostname,vlan,device_type,port,notes) "
                        "VALUES (?,?,?,?,?,?)",
                        (cip, host, c.get('network', 'Default'),
                         'UniFi Client', '', note))
            self.ip_tree.after(0, self.load_ip_data)
            print("🎉 UniFi Sync complete!")
        except requests.exceptions.Timeout:
            print(f"❌ Timed out — is {ip} reachable?")
        except Exception as e:
            print(f"❌ Sync error: {e}")

    # ═════════════════════════════════════════════════════════════════════════
    # 🐳 DOCKER STACKS
    # ═════════════════════════════════════════════════════════════════════════

    def build_docker_tab(self):
        self._cur_stack_id = None
        paned = tk.PanedWindow(self.tab_docker, orient=tk.HORIZONTAL,
                               bg=self.colors['content_bg'], bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = tk.Frame(paned, bg=self.colors['content_bg'])
        paned.add(left, minsize=200)
        tk.Label(left, text="Stacks", font=("Segoe UI", 11, "bold"),
                 bg=self.colors['content_bg'], fg=self.colors['text']
                 ).pack(anchor="w", padx=6, pady=(4, 2))
        self._stack_lb = tk.Listbox(
            left, bg=self.colors['card_bg'], fg=self.colors['text'],
            selectbackground=self.colors['primary'], selectforeground="white",
            font=("Segoe UI", 10), relief=tk.FLAT, activestyle="none", bd=0)
        self._stack_lb.pack(fill=tk.BOTH, expand=True)
        self._stack_lb.bind("<<ListboxSelect>>", self._on_stack_select)
        lb = tk.Frame(left, bg=self.colors['content_bg'])
        lb.pack(fill=tk.X, pady=4)
        tk.Button(lb, text="＋ New Stack", bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self._new_stack
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        tk.Button(lb, text="🗑", bg=self.colors['card_bg'], fg="#D32F2F",
                  relief=tk.FLAT, cursor="hand2", command=self._delete_stack
                  ).pack(side=tk.LEFT)

        right = tk.Frame(paned, bg=self.colors['card_bg'])
        paned.add(right, minsize=420)
        meta = tk.Frame(right, bg=self.colors['card_bg'])
        meta.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(meta, text="Name:", bg=self.colors['card_bg'],
                 fg=self.colors['text'], font=("Segoe UI", 9)
                 ).grid(row=0, column=0, sticky="w")
        self._stack_name_var = tk.StringVar()
        tk.Entry(meta, textvariable=self._stack_name_var,
                 bg=self.colors['background'], fg=self.colors['text'],
                 insertbackground="white", relief=tk.FLAT, font=("Segoe UI", 10)
                 ).grid(row=0, column=1, sticky="ew", padx=5)
        tk.Label(meta, text="Status:", bg=self.colors['card_bg'],
                 fg=self.colors['text'], font=("Segoe UI", 9)
                 ).grid(row=0, column=2, sticky="w", padx=(12, 0))
        self._stack_status_var = tk.StringVar(value="Not Deployed")
        ttk.Combobox(meta, textvariable=self._stack_status_var,
                     values=list(_STATUS_COLOURS.keys()),
                     state="readonly", width=14, font=("Segoe UI", 9)
                     ).grid(row=0, column=3, padx=5)
        meta.columnconfigure(1, weight=1)
        nr = tk.Frame(right, bg=self.colors['card_bg'])
        nr.pack(fill=tk.X, padx=10, pady=(0, 4))
        tk.Label(nr, text="Notes:", bg=self.colors['card_bg'],
                 fg=self.colors['text_dim'], font=("Segoe UI", 9)
                 ).pack(side=tk.LEFT, padx=(0, 6))
        self._stack_notes_var = tk.StringVar()
        tk.Entry(nr, textvariable=self._stack_notes_var,
                 bg=self.colors['background'], fg=self.colors['text_dim'],
                 insertbackground="white", relief=tk.FLAT, font=("Segoe UI", 9)
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(right, text="docker-compose.yml",
                 bg=self.colors['card_bg'], fg=self.colors['text_dim'],
                 font=("Segoe UI", 8, "italic")).pack(anchor="w", padx=12)
        self._stack_text = tk.Text(
            right, font=("Consolas", 11), bg="#1E1E1E", fg="#D4D4D4",
            insertbackground="white", relief=tk.FLAT, padx=8, pady=6)
        self._stack_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 4))
        ab = tk.Frame(right, bg=self.colors['card_bg'])
        ab.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Button(ab, text="📋 Copy Compose", bg=self.colors['primary'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self._copy_compose
                  ).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(ab, text="💾 Save Stack", bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self._save_stack
                  ).pack(side=tk.LEFT)
        self._load_stack_list()

    def _load_stack_list(self):
        self._stack_lb.delete(0, tk.END)
        self._stack_data = db.execute_query(
            "SELECT id,name,status FROM docker_stacks ORDER BY name") or []
        for _, name, _ in self._stack_data:
            self._stack_lb.insert(tk.END, f"  {name}")

    def _on_stack_select(self, _=None):
        sel = self._stack_lb.curselection()
        if not sel:
            return
        sid, _, _ = self._stack_data[sel[0]]
        self._cur_stack_id = sid
        row = db.execute_query(
            "SELECT name,compose,status,notes FROM docker_stacks WHERE id=?", (sid,))
        if not row:
            return
        name, compose, status, notes = row[0]
        self._stack_name_var.set(name)
        self._stack_status_var.set(status or "Not Deployed")
        self._stack_notes_var.set(notes or "")
        self._stack_text.delete("1.0", tk.END)
        self._stack_text.insert(tk.END, compose or "")

    def _new_stack(self):
        self._stack_lb.selection_clear(0, tk.END)
        self._cur_stack_id = None
        self._stack_name_var.set("")
        self._stack_status_var.set("Not Deployed")
        self._stack_notes_var.set("")
        self._stack_text.delete("1.0", tk.END)
        self._stack_text.insert(tk.END,
            "services:\n  myservice:\n    image: \n    container_name: \n"
            "    restart: unless-stopped\n    ports:\n      - 8080:8080\n")

    def _save_stack(self):
        name    = self._stack_name_var.get().strip()
        compose = self._stack_text.get("1.0", tk.END).strip()
        status  = self._stack_status_var.get()
        notes   = self._stack_notes_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name",
                "Stack name cannot be empty.", parent=self.parent)
            return
        if self._cur_stack_id:
            db.execute_query(
                "UPDATE docker_stacks SET name=?,compose=?,status=?,notes=? WHERE id=?",
                (name, compose, status, notes, self._cur_stack_id))
        else:
            self._cur_stack_id = db.execute_query(
                "INSERT INTO docker_stacks (name,compose,status,notes) VALUES (?,?,?,?)",
                (name, compose, status, notes))
        self._load_stack_list()

    def _delete_stack(self):
        if not self._cur_stack_id:
            return
        if not messagebox.askyesno("Delete Stack",
                f"Delete '{self._stack_name_var.get()}'?", parent=self.parent):
            return
        db.execute_query("DELETE FROM docker_stacks WHERE id=?", (self._cur_stack_id,))
        self._cur_stack_id = None
        self._stack_name_var.set("")
        self._stack_text.delete("1.0", tk.END)
        self._load_stack_list()

    def _copy_compose(self):
        content = self._stack_text.get("1.0", tk.END).strip()
        if not content:
            return
        self.parent.clipboard_clear()
        self.parent.clipboard_append(content)
        messagebox.showinfo("Copied",
            "Compose content copied to clipboard!", parent=self.parent)

    # ═════════════════════════════════════════════════════════════════════════
    # 🏥 SERVICE HEALTH
    # ═════════════════════════════════════════════════════════════════════════

    def build_health_tab(self):
        # key is "ip:port" so multiple services on the same host each get a row
        self._health_rows: dict[str, dict] = {}
        self._health_observer_cb = None

        hdr = tk.Frame(self.tab_health, bg=self.colors['secondary'])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="  Service Health Monitor",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors['secondary'], fg=self.colors['text']
                 ).pack(side=tk.LEFT, pady=8)

        tk.Button(hdr, text="🔄 Check Now",
                  bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2",
                  command=self._trigger_manual_check
                  ).pack(side=tk.RIGHT, padx=12, pady=6)

        self._poll_status_lbl = tk.Label(
            hdr, text="Auto-polling every 60 s",
            font=("Segoe UI", 8, "italic"),
            bg=self.colors['secondary'], fg=self.colors['text_dim'])
        self._poll_status_lbl.pack(side=tk.RIGHT, padx=8)

        # Scrollable card area
        outer = tk.Frame(self.tab_health, bg=self.colors['background'])
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        canvas = tk.Canvas(outer, bg=self.colors['background'], highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self._health_inner = tk.Frame(canvas, bg=self.colors['background'])
        self._health_inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._health_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._health_canvas_ref = canvas
        self._build_health_rows()

        # Wire up to the global health service for live updates
        try:
            from health_service import register_health_observer, get_health_status
            self._health_observer_cb = self._on_health_update
            register_health_observer(self._health_observer_cb)

            # Immediately populate from the service's current snapshot
            current = get_health_status()
            if current:
                for key, status in current.items():
                    self._apply_health_result(key, status.online, status.latency_ms)
        except ImportError:
            pass   # health service not available — manual only

    # ── Build the health-check rows from IPAM ─────────────────────────────

    def _build_health_rows(self):
        for w in self._health_inner.winfo_children():
            w.destroy()
        self._health_rows.clear()

        hosts = db.execute_query(
            "SELECT ip_address,hostname,port,device_type FROM ip_allocations "
            "ORDER BY ip_address") or []

        # Column headers
        hdr = tk.Frame(self._health_inner, bg=self.colors['secondary'])
        hdr.pack(fill=tk.X, pady=(0, 4))
        for txt, w in [("", 28), ("Status", 80), ("Host", 160),
                       ("IP", 120), ("Port", 60), ("Type", 110), ("Latency", 80)]:
            tk.Label(hdr, text=txt, width=w//8,
                     font=("Segoe UI", 9, "bold"),
                     bg=self.colors['secondary'], fg=self.colors['text_dim']
                     ).pack(side=tk.LEFT, padx=4, pady=4)

        for ip, hostname, port, dtype in hosts:
            row_key = f"{ip}:{port}" if port else ip

            row = tk.Frame(self._health_inner, bg=self.colors['card_bg'])
            row.pack(fill=tk.X, pady=1)

            # Status dot
            dot = tk.Canvas(row, width=16, height=16,
                            bg=self.colors['card_bg'], highlightthickness=0)
            dot.pack(side=tk.LEFT, padx=(8, 4))
            dot.create_oval(2, 2, 14, 14, fill="#555555", outline="")

            status_lbl = tk.Label(row, text="—", width=8,
                                  font=("Segoe UI", 9, "bold"),
                                  bg=self.colors['card_bg'], fg=self.colors['text_dim'])
            status_lbl.pack(side=tk.LEFT, padx=4)

            tk.Label(row, text=hostname or "—", width=18, anchor="w",
                     font=("Segoe UI", 10),
                     bg=self.colors['card_bg'], fg=self.colors['text']
                     ).pack(side=tk.LEFT, padx=4)
            tk.Label(row, text=ip, width=14, anchor="w",
                     font=("Consolas", 10),
                     bg=self.colors['card_bg'], fg=self.colors['text_dim']
                     ).pack(side=tk.LEFT, padx=4)
            tk.Label(row, text=port or "ping", width=6,
                     font=("Segoe UI", 9),
                     bg=self.colors['card_bg'], fg=self.colors['text_dim']
                     ).pack(side=tk.LEFT, padx=4)
            tk.Label(row, text=dtype or "—", width=13, anchor="w",
                     font=("Segoe UI", 9),
                     bg=self.colors['card_bg'], fg=self.colors['text_dim']
                     ).pack(side=tk.LEFT, padx=4)
            lat_lbl = tk.Label(row, text="", width=8,
                               font=("Segoe UI", 9),
                               bg=self.colors['card_bg'], fg=self.colors['text_dim'])
            lat_lbl.pack(side=tk.LEFT, padx=4)

            self._health_rows[row_key] = {
                "dot":     dot,
                "status":  status_lbl,
                "latency": lat_lbl,
                "port":    port,
            }

    # ── Health service integration ────────────────────────────────────────

    def _on_health_update(self):
        """Observer callback — called on main thread after each poll cycle."""
        try:
            from health_service import get_health_status
            current = get_health_status()
            # Rebuild rows in case IPAM changed, then apply statuses
            self._build_health_rows()
            for key, status in current.items():
                self._apply_health_result(key, status.online, status.latency_ms)
        except Exception:
            pass   # widget was destroyed (user navigated away)

    def _trigger_manual_check(self):
        """'Check Now' button — triggers an immediate poll cycle."""
        try:
            from health_service import trigger_health_poll
            # Mark all rows as checking
            for _key, data in self._health_rows.items():
                data["status"].config(text="Checking…", fg=self.colors['text_dim'])
                data["dot"].itemconfig(1, fill="#888888")
            trigger_health_poll()
        except ImportError:
            # Fallback: run checks directly if health service is unavailable
            self._check_all_health()

    # ── Fallback manual check (used only if health_service is missing) ────

    def _check_all_health(self):
        self._build_health_rows()
        for key, data in self._health_rows.items():
            ip = key.split(":")[0]
            data["status"].config(text="Checking…", fg=self.colors['text_dim'])
            data["dot"].itemconfig(1, fill="#888888")
            threading.Thread(
                target=self._check_host_fallback,
                args=(key, ip, data["port"]), daemon=True).start()

    def _check_host_fallback(self, key: str, ip: str, port: str):
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
                    capture_output=True, timeout=5)
                online = (result.returncode == 0)
        except Exception:
            online = False
        latency_ms = int((time.time() - start) * 1000)
        self.parent.after(0, self._apply_health_result, key, online, latency_ms)

    # ── Apply a single result to the UI ───────────────────────────────────

    def _apply_health_result(self, key: str, online: bool, latency_ms: int):
        data = self._health_rows.get(key)
        if not data:
            return
        if online:
            data["dot"].itemconfig(1, fill="#4CAF50")
            data["status"].config(text="Online", fg="#4CAF50")
            data["latency"].config(text=f"{latency_ms} ms")
        else:
            data["dot"].itemconfig(1, fill="#F44336")
            data["status"].config(text="Offline", fg="#F44336")
            data["latency"].config(text="—")

    # ═════════════════════════════════════════════════════════════════════════
    # 📓 RUNBOOK / LAB NOTES
    # ═════════════════════════════════════════════════════════════════════════

    def build_runbook_tab(self):
        self._cur_note_id = None
        paned = tk.PanedWindow(self.tab_runbook, orient=tk.HORIZONTAL,
                               bg=self.colors['content_bg'], bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: note list
        left = tk.Frame(paned, bg=self.colors['content_bg'])
        paned.add(left, minsize=200)
        tk.Label(left, text="Notes", font=("Segoe UI", 11, "bold"),
                 bg=self.colors['content_bg'], fg=self.colors['text']
                 ).pack(anchor="w", padx=6, pady=(4, 2))
        self._note_lb = tk.Listbox(
            left, bg=self.colors['card_bg'], fg=self.colors['text'],
            selectbackground=self.colors['primary'], selectforeground="white",
            font=("Segoe UI", 10), relief=tk.FLAT, activestyle="none", bd=0)
        self._note_lb.pack(fill=tk.BOTH, expand=True)
        self._note_lb.bind("<<ListboxSelect>>", self._on_note_select)
        nb = tk.Frame(left, bg=self.colors['content_bg'])
        nb.pack(fill=tk.X, pady=4)
        tk.Button(nb, text="＋ New Note", bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self._new_note
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        tk.Button(nb, text="🗑", bg=self.colors['card_bg'], fg="#D32F2F",
                  relief=tk.FLAT, cursor="hand2", command=self._delete_note
                  ).pack(side=tk.LEFT)

        # Right: editor
        right = tk.Frame(paned, bg=self.colors['card_bg'])
        paned.add(right, minsize=420)
        title_row = tk.Frame(right, bg=self.colors['card_bg'])
        title_row.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(title_row, text="Title:", bg=self.colors['card_bg'],
                 fg=self.colors['text'], font=("Segoe UI", 9)
                 ).pack(side=tk.LEFT, padx=(0, 6))
        self._note_title_var = tk.StringVar()
        tk.Entry(title_row, textvariable=self._note_title_var,
                 bg=self.colors['background'], fg=self.colors['text'],
                 insertbackground="white", relief=tk.FLAT,
                 font=("Segoe UI", 11, "bold")
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._note_text = tk.Text(
            right, font=("Segoe UI", 10), wrap=tk.WORD,
            bg=self.colors['card_bg'], fg=self.colors['text'],
            insertbackground=self.colors['text'],
            relief=tk.FLAT, padx=10, pady=8,
            selectbackground=self.colors['primary'])
        self._note_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 4))

        ab = tk.Frame(right, bg=self.colors['card_bg'])
        ab.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Label(ab, text="Supports plain text and markdown-style checklists  [ ] / [x]",
                 font=("Segoe UI", 8, "italic"),
                 bg=self.colors['card_bg'], fg=self.colors['text_dim']
                 ).pack(side=tk.LEFT)
        tk.Button(ab, text="💾 Save Note", bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self._save_note
                  ).pack(side=tk.RIGHT)

        self._load_note_list()

    def _load_note_list(self):
        self._note_lb.delete(0, tk.END)
        self._note_data = db.execute_query(
            "SELECT id,title FROM lab_notes ORDER BY updated_at DESC") or []
        for _, title in self._note_data:
            self._note_lb.insert(tk.END, f"  {title}")

    def _on_note_select(self, _=None):
        sel = self._note_lb.curselection()
        if not sel:
            return
        nid, _ = self._note_data[sel[0]]
        self._cur_note_id = nid
        row = db.execute_query(
            "SELECT title,content FROM lab_notes WHERE id=?", (nid,))
        if not row:
            return
        title, content = row[0]
        self._note_title_var.set(title)
        self._note_text.delete("1.0", tk.END)
        self._note_text.insert(tk.END, content or "")

    def _new_note(self):
        self._note_lb.selection_clear(0, tk.END)
        self._cur_note_id = None
        self._note_title_var.set("")
        self._note_text.delete("1.0", tk.END)
        self._note_text.focus_set()

    def _save_note(self):
        title   = self._note_title_var.get().strip()
        content = self._note_text.get("1.0", tk.END).strip()
        if not title:
            messagebox.showwarning("Missing Title",
                "Note title cannot be empty.", parent=self.parent)
            return
        if self._cur_note_id:
            db.execute_query(
                "UPDATE lab_notes SET title=?,content=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE id=?",
                (title, content, self._cur_note_id))
        else:
            self._cur_note_id = db.execute_query(
                "INSERT INTO lab_notes (title,content) VALUES (?,?)",
                (title, content))
        self._load_note_list()

    def _delete_note(self):
        if not self._cur_note_id:
            return
        if not messagebox.askyesno("Delete Note",
                f"Delete '{self._note_title_var.get()}'?", parent=self.parent):
            return
        db.execute_query("DELETE FROM lab_notes WHERE id=?", (self._cur_note_id,))
        self._cur_note_id = None
        self._note_title_var.set("")
        self._note_text.delete("1.0", tk.END)
        self._load_note_list()

    # ═════════════════════════════════════════════════════════════════════════
    # 🔑 CREDENTIALS VAULT
    # ═════════════════════════════════════════════════════════════════════════

    def build_credentials_tab(self):
        self._creds_frame = tk.Frame(self.tab_creds, bg=self.colors['background'])
        self._creds_frame.pack(fill=tk.BOTH, expand=True)
        self._vault_pin  = None   # plaintext PIN, held in memory while unlocked
        self._vault_salt = None   # bytes salt, held in memory while unlocked
        self._show_vault_lock_screen()

    def _show_vault_lock_screen(self):
        for w in self._creds_frame.winfo_children():
            w.destroy()

        pin_row  = db.execute_query("SELECT value FROM settings WHERE key='vault_pin'")
        salt_row = db.execute_query("SELECT value FROM settings WHERE key='vault_salt'")
        has_pin  = bool(pin_row and pin_row[0][0])

        lock = tk.Frame(self._creds_frame, bg=self.colors['background'])
        lock.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(lock, text="🔑", font=("Segoe UI", 48),
                 bg=self.colors['background'], fg=self.colors['text']
                 ).pack()
        tk.Label(lock,
                 text="Credentials Vault" if has_pin else "Set Up Credentials Vault",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors['background'], fg=self.colors['text']
                 ).pack(pady=(4, 2))
        tk.Label(lock,
                 text="Enter your PIN to unlock" if has_pin
                      else "Choose a PIN to protect your credentials",
                 font=("Segoe UI", 9, "italic"),
                 bg=self.colors['background'], fg=self.colors['text_dim']
                 ).pack(pady=(0, 16))

        pin_var = tk.StringVar()
        pin_entry = tk.Entry(lock, textvariable=pin_var, show="●", width=14,
                             font=("Segoe UI", 14), justify="center",
                             bg=self.colors['card_bg'], fg=self.colors['text'],
                             insertbackground=self.colors['text'],
                             relief=tk.FLAT)
        pin_entry.pack(pady=4)
        pin_entry.focus_set()

        msg_lbl = tk.Label(lock, text="",
                           font=("Segoe UI", 9),
                           bg=self.colors['background'], fg="#F44336")
        msg_lbl.pack(pady=4)

        def attempt():
            pin = pin_var.get().strip()
            if not pin:
                return
            h = _pin_hash(pin)
            if has_pin:
                stored = pin_row[0][0]
                if h != stored:
                    msg_lbl.config(text="Incorrect PIN — try again")
                    pin_var.set("")
                    return
                # Load existing salt — if none exists (vault created before encryption
                # was added), generate one now and persist it
                if salt_row and salt_row[0][0]:
                    salt = base64.b64decode(salt_row[0][0])
                else:
                    salt = os.urandom(16)
                    db.execute_query(
                        "INSERT OR REPLACE INTO settings (key,value) VALUES "
                        "('vault_salt',?)",
                        (base64.b64encode(salt).decode(),))
                self._vault_pin  = pin
                self._vault_salt = salt
                self._vault_unlocked = True
                self._show_vault_contents()
            else:
                # First-time setup: generate salt, store hash + salt
                salt = os.urandom(16)
                db.execute_query(
                    "INSERT OR REPLACE INTO settings (key,value) VALUES ('vault_pin',?)",
                    (h,))
                db.execute_query(
                    "INSERT OR REPLACE INTO settings (key,value) VALUES "
                    "('vault_salt',?)",
                    (base64.b64encode(salt).decode(),))
                self._vault_pin  = pin
                self._vault_salt = salt
                self._vault_unlocked = True
                self._show_vault_contents()

        pin_entry.bind("<Return>", lambda e: attempt())
        tk.Button(lock, text="Unlock",
                  bg=self.colors['accent'], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  command=attempt).pack(pady=8)

        if has_pin:
            tk.Button(lock, text="Reset PIN (clears all credentials)",
                      bg=self.colors['background'], fg=self.colors['text_dim'],
                      font=("Segoe UI", 8), relief=tk.FLAT, cursor="hand2",
                      command=self._reset_vault).pack()

    def _reset_vault(self):
        if not messagebox.askyesno("Reset Vault",
                "This will DELETE all stored credentials and remove the PIN.\n"
                "Are you sure?", parent=self.parent):
            return
        db.execute_query("DELETE FROM credentials")
        db.execute_query("DELETE FROM settings WHERE key='vault_pin'")
        db.execute_query("DELETE FROM settings WHERE key='vault_salt'")
        self._vault_unlocked = False
        self._vault_pin  = None
        self._vault_salt = None
        self._show_vault_lock_screen()

    def _show_vault_contents(self):
        for w in self._creds_frame.winfo_children():
            w.destroy()

        self._cur_cred_id = None

        paned = tk.PanedWindow(self._creds_frame, orient=tk.HORIZONTAL,
                               bg=self.colors['background'], bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: list
        left = tk.Frame(paned, bg=self.colors['content_bg'])
        paned.add(left, minsize=200)
        hdr = tk.Frame(left, bg=self.colors['content_bg'])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Credentials", font=("Segoe UI", 11, "bold"),
                 bg=self.colors['content_bg'], fg=self.colors['text']
                 ).pack(side=tk.LEFT, padx=6, pady=(4, 2))
        tk.Button(hdr, text="🔒 Lock",
                  bg=self.colors['content_bg'], fg=self.colors['text_dim'],
                  font=("Segoe UI", 8), relief=tk.FLAT, cursor="hand2",
                  command=self._lock_vault).pack(side=tk.RIGHT, padx=4)

        self._cred_lb = tk.Listbox(
            left, bg=self.colors['card_bg'], fg=self.colors['text'],
            selectbackground=self.colors['primary'], selectforeground="white",
            font=("Segoe UI", 10), relief=tk.FLAT, activestyle="none", bd=0)
        self._cred_lb.pack(fill=tk.BOTH, expand=True)
        self._cred_lb.bind("<<ListboxSelect>>", self._on_cred_select)
        cb = tk.Frame(left, bg=self.colors['content_bg'])
        cb.pack(fill=tk.X, pady=4)
        tk.Button(cb, text="＋ Add", bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self._new_cred
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        tk.Button(cb, text="🗑", bg=self.colors['card_bg'], fg="#D32F2F",
                  relief=tk.FLAT, cursor="hand2", command=self._delete_cred
                  ).pack(side=tk.LEFT)

        # Right: editor
        right = tk.Frame(paned, bg=self.colors['card_bg'])
        paned.add(right, minsize=380)

        self._cred_vars = {}
        for label, key, show in [
            ("Label / Service",   "label",    False),
            ("Username",          "username", False),
            ("Password",          "password", True),
            ("URL",               "url",      False),
            ("Notes",             "notes",    False),
        ]:
            row = tk.Frame(right, bg=self.colors['card_bg'])
            row.pack(fill=tk.X, padx=10, pady=(10, 0))
            tk.Label(row, text=label, width=14, anchor="w",
                     bg=self.colors['card_bg'], fg=self.colors['text'],
                     font=("Segoe UI", 9)).pack(side=tk.LEFT)
            var = tk.StringVar()
            e = tk.Entry(row, textvariable=var, show="●" if show else "",
                         bg=self.colors['background'], fg=self.colors['text'],
                         insertbackground="white", relief=tk.FLAT,
                         font=("Segoe UI", 10))
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self._cred_vars[key] = var

            if show:
                # Toggle show/hide password
                eye_var = tk.BooleanVar(value=False)
                def _toggle(ev=e, bv=eye_var):
                    ev.config(show="" if bv.get() else "●")
                tk.Checkbutton(row, text="👁", variable=eye_var,
                               command=_toggle,
                               bg=self.colors['card_bg'],
                               fg=self.colors['text_dim'],
                               activebackground=self.colors['card_bg'],
                               selectcolor=self.colors['card_bg'],
                               font=("Segoe UI", 10), relief=tk.FLAT,
                               cursor="hand2").pack(side=tk.LEFT)

        ab = tk.Frame(right, bg=self.colors['card_bg'])
        ab.pack(fill=tk.X, padx=10, pady=14)
        tk.Button(ab, text="📋 Copy Password",
                  bg=self.colors['primary'], fg="white",
                  relief=tk.FLAT, cursor="hand2",
                  command=self._copy_password).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(ab, text="💾 Save",
                  bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2",
                  command=self._save_cred).pack(side=tk.LEFT)

        tk.Label(right,
                 text="🔒  Passwords encrypted with Fernet (PBKDF2-SHA256, 480k rounds). "
                      "Local SQLite only.",
                 font=("Segoe UI", 8, "italic"),
                 bg=self.colors['card_bg'], fg=self.colors['text_dim']
                 ).pack(anchor="w", padx=10, pady=(0, 8))

        self._load_cred_list()

    def _lock_vault(self):
        self._vault_unlocked = False
        self._vault_pin  = None
        self._vault_salt = None
        self._show_vault_lock_screen()

    def _load_cred_list(self):
        self._cred_lb.delete(0, tk.END)
        self._cred_data = db.execute_query(
            "SELECT id,label FROM credentials ORDER BY label") or []
        for _, label in self._cred_data:
            self._cred_lb.insert(tk.END, f"  {label}")

    def _on_cred_select(self, _=None):
        sel = self._cred_lb.curselection()
        if not sel:
            return
        cid, _ = self._cred_data[sel[0]]
        self._cur_cred_id = cid
        row = db.execute_query(
            "SELECT label,username,password,url,notes FROM credentials WHERE id=?",
            (cid,))
        if not row:
            return
        label, username, enc_pw, url, notes = row[0]
        # Decrypt password if we have the key material
        if self._vault_pin and self._vault_salt is not None:
            plaintext_pw = _decrypt_password(self._vault_pin, self._vault_salt,
                                             enc_pw or "")
        else:
            plaintext_pw = enc_pw or ""
        for key, val in zip(
            ("label", "username", "password", "url", "notes"),
            (label, username, plaintext_pw, url, notes)
        ):
            self._cred_vars[key].set(val or "")

    def _new_cred(self):
        self._cred_lb.selection_clear(0, tk.END)
        self._cur_cred_id = None
        for v in self._cred_vars.values():
            v.set("")

    def _save_cred(self):
        label = self._cred_vars["label"].get().strip()
        if not label:
            messagebox.showwarning("Missing Label",
                "Label / Service cannot be empty.", parent=self.parent)
            return
        # Encrypt the password before writing to DB
        plaintext_pw = self._cred_vars["password"].get()
        if self._vault_pin and self._vault_salt is not None:
            stored_pw = _encrypt_password(self._vault_pin, self._vault_salt,
                                          plaintext_pw)
        else:
            stored_pw = plaintext_pw   # fallback (shouldn't happen when vault is open)
        vals = (label,
                self._cred_vars["username"].get(),
                stored_pw,
                self._cred_vars["url"].get(),
                self._cred_vars["notes"].get())
        if self._cur_cred_id:
            db.execute_query(
                "UPDATE credentials SET label=?,username=?,password=?,url=?,notes=?,"
                "updated_at=CURRENT_TIMESTAMP WHERE id=?",
                vals + (self._cur_cred_id,))
        else:
            self._cur_cred_id = db.execute_query(
                "INSERT INTO credentials (label,username,password,url,notes) "
                "VALUES (?,?,?,?,?)", vals)
        self._load_cred_list()

    def _delete_cred(self):
        if not self._cur_cred_id:
            return
        label = self._cred_vars["label"].get() or "this entry"
        if not messagebox.askyesno("Delete Credential",
                f"Delete '{label}'?", parent=self.parent):
            return
        db.execute_query("DELETE FROM credentials WHERE id=?", (self._cur_cred_id,))
        self._cur_cred_id = None
        self._new_cred()
        self._load_cred_list()

    def _copy_password(self):
        pw = self._cred_vars["password"].get()
        if not pw:
            return
        self.parent.clipboard_clear()
        self.parent.clipboard_append(pw)
        messagebox.showinfo("Copied",
            "Password copied to clipboard!", parent=self.parent)

    # ═════════════════════════════════════════════════════════════════════════
    # 📜 SCRIPT VAULT
    # ═════════════════════════════════════════════════════════════════════════

    def build_scripts_tab(self):
        self.current_script_id = None
        paned = tk.PanedWindow(self.tab_scripts, orient=tk.HORIZONTAL,
                               bg=self.colors['content_bg'], bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = tk.Frame(paned, bg=self.colors['content_bg'])
        paned.add(left, minsize=200)
        self.script_tree = ttk.Treeview(left, show="tree", selectmode="browse")
        self.script_tree.tag_configure('category',
            foreground=self.colors['primary'], font=("Segoe UI", 10, "bold"))
        self.script_tree.tag_configure('script', foreground=self.colors['text'])
        self.script_tree.pack(fill=tk.BOTH, expand=True)
        self.script_tree.bind("<<TreeviewSelect>>", self.on_script_select)
        lb = tk.Frame(left, bg=self.colors['content_bg'])
        lb.pack(fill=tk.X, pady=4)
        tk.Button(lb, text="＋ New", bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self.add_new_script
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        tk.Button(lb, text="🗑 Delete", bg="#D32F2F", fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self.delete_script
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        right = tk.Frame(paned, bg=self.colors['card_bg'])
        paned.add(right, minsize=400)
        meta = tk.Frame(right, bg=self.colors['card_bg'])
        meta.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(meta, text="Title:", bg=self.colors['card_bg'],
                 fg=self.colors['text'], font=("Segoe UI", 9)
                 ).grid(row=0, column=0, sticky="w")
        self.script_title_var = tk.StringVar()
        tk.Entry(meta, textvariable=self.script_title_var,
                 bg=self.colors['background'], fg=self.colors['text'],
                 insertbackground="white", relief=tk.FLAT
                 ).grid(row=0, column=1, sticky="ew", padx=5)
        tk.Label(meta, text="Category:", bg=self.colors['card_bg'],
                 fg=self.colors['text'], font=("Segoe UI", 9)
                 ).grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.script_category_var = tk.StringVar()
        tk.Entry(meta, textvariable=self.script_category_var,
                 bg=self.colors['background'], fg=self.colors['text'],
                 insertbackground="white", relief=tk.FLAT, width=15
                 ).grid(row=0, column=3, sticky="ew", padx=5)
        meta.columnconfigure(1, weight=1)
        self.script_text = tk.Text(
            right, font=("Consolas", 11), bg="#1E1E1E", fg="#D4D4D4",
            insertbackground="white", relief=tk.FLAT, padx=8, pady=6)
        self.script_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))
        ab = tk.Frame(right, bg=self.colors['card_bg'])
        ab.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Button(ab, text="📋 Copy to Clipboard",
                  bg=self.colors['primary'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self._copy_script
                  ).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(ab, text="💾 Save Script",
                  bg=self.colors['accent'], fg="white",
                  relief=tk.FLAT, cursor="hand2", command=self.save_script
                  ).pack(side=tk.LEFT)
        self.load_script_data()

    def load_script_data(self):
        for r in self.script_tree.get_children():
            self.script_tree.delete(r)
        records = db.execute_query(
            "SELECT id,title,category FROM scripts ORDER BY category,title") or []
        cats = {}
        for sid, title, category in records:
            cat = category.strip() if category and category.strip() else "Uncategorized"
            if cat not in cats:
                iid = f"cat_{cat}"
                self.script_tree.insert("", tk.END, iid=iid,
                                        text=f"📂 {cat}", open=True, tags=('category',))
                cats[cat] = iid
            self.script_tree.insert(cats[cat], tk.END, iid=sid,
                                    text=f"📄 {title}", tags=('script',))

    def on_script_select(self, event):
        sel = self.script_tree.selection()
        if not sel:
            return
        iid = str(sel[0])
        if iid.startswith("cat_"):
            return
        self.current_script_id = iid
        row = db.execute_query(
            "SELECT title,category,content FROM scripts WHERE id=?",
            (self.current_script_id,))
        if row:
            title, cat, content = row[0]
            self.script_title_var.set(title)
            self.script_category_var.set(cat or "")
            self.script_text.delete("1.0", tk.END)
            self.script_text.insert(tk.END, content)

    def add_new_script(self):
        self.script_tree.selection_remove(self.script_tree.selection())
        self.current_script_id = None
        self.script_title_var.set("")
        self.script_category_var.set("")
        self.script_text.delete("1.0", tk.END)

    def save_script(self):
        title    = self.script_title_var.get().strip()
        category = self.script_category_var.get().strip()
        content  = self.script_text.get("1.0", tk.END).strip()
        if not title:
            messagebox.showwarning("Missing Title",
                "Script title cannot be empty.", parent=self.parent)
            return
        if self.current_script_id:
            db.execute_query(
                "UPDATE scripts SET title=?,category=?,content=? WHERE id=?",
                (title, category, content, self.current_script_id))
        else:
            nid = db.execute_query(
                "INSERT INTO scripts (title,category,content) VALUES (?,?,?)",
                (title, category, content))
            self.current_script_id = str(nid) if nid else None
        self.load_script_data()
        if self.current_script_id:
            try:
                self.script_tree.selection_set(self.current_script_id)
            except Exception:
                pass

    def delete_script(self):
        if not self.current_script_id:
            return
        title = self.script_title_var.get() or "this script"
        if not messagebox.askyesno("Delete Script",
                f"Delete '{title}'?", parent=self.parent):
            return
        db.execute_query("DELETE FROM scripts WHERE id=?", (self.current_script_id,))
        self.add_new_script()
        self.load_script_data()

    def _copy_script(self):
        content = self.script_text.get("1.0", tk.END).strip()
        if not content:
            return
        self.parent.clipboard_clear()
        self.parent.clipboard_append(content)
        messagebox.showinfo("Copied",
            "Script copied to clipboard!", parent=self.parent)
