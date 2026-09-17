"""
p2p_observer.py - Real Bitcoin P2P Network Observer.
Connects directly to live Bitcoin full nodes across the globe via port 8333,
performing real Bitcoin wire protocol handshakes and capturing live transaction INVs
with microsecond/millisecond arrival timestamps.
"""

import socket
import struct
import hashlib
import time
import asyncio
import io
from typing import Dict, List, Any, Optional, Set
from backend.realtime.geolocation import resolve_ip

MAGIC_MAINNET = b'\xf9\xbe\xb4\xd9'

# Curated high-uptime geographically diverse Bitcoin listening nodes (fallback if DNS seeds are slow)
STATIC_SEED_NODES = [
    {"ip": "45.79.195.29", "label": "Node US-East", "expected_country": "United States"},
    {"ip": "172.236.224.184", "label": "Node US-Central", "expected_country": "United States"},
    {"ip": "94.130.9.224", "label": "Node DE-Hetzner", "expected_country": "Germany"},
    {"ip": "65.108.110.58", "label": "Node FI-Helsinki", "expected_country": "Finland"},
    {"ip": "212.132.193.81", "label": "Node UK-London", "expected_country": "United Kingdom"},
    {"ip": "213.156.1.109", "label": "Node NL-Amsterdam", "expected_country": "The Netherlands"},
    {"ip": "123.243.159.11", "label": "Node AU-Sydney", "expected_country": "Australia"},
    {"ip": "198.16.196.238", "label": "Node CA-Montreal", "expected_country": "Canada"}
]

DNS_SEEDS = [
    "seed.bitcoin.sipa.be",
    "dnsseed.bluematt.me",
    "seed.bitcoinstats.com",
    "seed.btc.petertodd.org"
]

def double_sha256(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()

def make_message(cmd: str, payload: bytes) -> bytes:
    cmd_bytes = cmd.encode('ascii').ljust(12, b'\x00')
    length = struct.pack('<I', len(payload))
    checksum = double_sha256(payload)[:4]
    return MAGIC_MAINNET + cmd_bytes + length + checksum + payload

def make_version_payload(peer_ip: str, peer_port: int = 8333) -> bytes:
    version = 70015
    services = 0
    timestamp = int(time.time())
    
    # Receiver addr
    try:
        ip_bytes = socket.inet_aton(peer_ip)
    except socket.error:
        ip_bytes = b'\x00\x00\x00\x00'
    addr_recv = struct.pack('>Q', 1) + b'\x00'*10 + b'\xff\xff' + ip_bytes + struct.pack('>H', peer_port)
    
    # Sender addr
    addr_from = struct.pack('>Q', 0) + b'\x00'*10 + b'\xff\xff' + socket.inet_aton('127.0.0.1') + struct.pack('>H', 8333)
    nonce = 0xbeefcafe
    ua = b'/BitcoinOriginObserver:2.0/'
    ua_bytes = bytes([len(ua)]) + ua
    start_height = 0
    relay = True
    
    return struct.pack('<iQQ', version, services, timestamp) + addr_recv + addr_from + struct.pack('<Q', nonce) + ua_bytes + struct.pack('<i?', start_height, relay)

def read_varint(stream: io.BytesIO) -> int:
    b = stream.read(1)
    if not b:
        return 0
    val = b[0]
    if val < 0xfd:
        return val
    elif val == 0xfd:
        data = stream.read(2)
        return struct.unpack('<H', data)[0] if len(data) == 2 else 0
    elif val == 0xfe:
        data = stream.read(4)
        return struct.unpack('<I', data)[0] if len(data) == 4 else 0
    else:
        data = stream.read(8)
        return struct.unpack('<Q', data)[0] if len(data) == 8 else 0

class P2PObserver:
    def __init__(self):
        self.observations: Dict[str, List[Dict[str, Any]]] = {}
        self.active_peers: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []

    def discover_nodes(self, max_nodes: int = 10) -> List[Dict[str, Any]]:
        discovered_ips: Set[str] = set()
        for seed in DNS_SEEDS:
            try:
                addrs = socket.getaddrinfo(seed, 8333, socket.AF_INET, socket.SOCK_STREAM)
                for a in addrs:
                    discovered_ips.add(a[4][0])
            except Exception:
                continue

        nodes = []
        countries_seen = set()
        for ip in discovered_ips:
            geo = resolve_ip(ip)
            country = geo.get("country", "Unknown")
            if country not in countries_seen and country != "Unknown":
                countries_seen.add(country)
                nodes.append({
                    "ip": ip,
                    "label": f"Node ({geo.get('city') or country})",
                    "country": country,
                    "country_code": geo.get("country_code", "??")
                })
            if len(nodes) >= max_nodes:
                break

        if len(nodes) < 4:
            for s in STATIC_SEED_NODES:
                geo = resolve_ip(s["ip"])
                nodes.append({
                    "ip": s["ip"],
                    "label": s["label"],
                    "country": geo.get("country") or s["expected_country"],
                    "country_code": geo.get("country_code", "??")
                })
        return nodes

    async def _handle_peer(self, node: Dict[str, Any]):
        ip = node["ip"]
        label = node.get("label", ip)
        country = node.get("country", "Unknown")
        country_code = node.get("country_code", "??")

        while self._running:
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, 8333), timeout=4.0)
                writer.write(make_message('version', make_version_payload(ip)))
                await writer.drain()

                hdr = await asyncio.wait_for(reader.readexactly(24), timeout=5.0)
                cmd = hdr[4:16].rstrip(b'\x00').decode('ascii', errors='ignore')
                plen = struct.unpack('<I', hdr[16:20])[0]
                await reader.readexactly(plen)

                writer.write(make_message('verack', b''))
                await writer.drain()

                self.active_peers[ip] = {"label": label, "country": country, "country_code": country_code}

                while self._running:
                    hdr = await asyncio.wait_for(reader.readexactly(24), timeout=30.0)
                    if hdr[:4] != MAGIC_MAINNET:
                        break
                    cmd = hdr[4:16].rstrip(b'\x00').decode('ascii', errors='ignore')
                    plen = struct.unpack('<I', hdr[16:20])[0]
                    payload = await asyncio.wait_for(reader.readexactly(plen), timeout=30.0)
                    arrival_time = time.time()

                    if cmd == 'inv':
                        stream = io.BytesIO(payload)
                        count = read_varint(stream)
                        for _ in range(min(count, 500)):
                            item_data = stream.read(36)
                            if len(item_data) < 36:
                                break
                            inv_type, h_bytes = struct.unpack('<I32s', item_data)
                            if inv_type in (1, 5):
                                txid = h_bytes[::-1].hex()
                                if txid not in self.observations:
                                    self.observations[txid] = []
                                
                                if not any(obs["peer_ip"] == ip for obs in self.observations[txid]):
                                    self.observations[txid].append({
                                        "peer_ip": ip,
                                        "node_label": label,
                                        "country": country,
                                        "country_code": country_code,
                                        "timestamp": arrival_time
                                    })
                    elif cmd == 'ping':
                        writer.write(make_message('pong', payload))
                        await writer.drain()

                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            finally:
                self.active_peers.pop(ip, None)
            
            if self._running:
                await asyncio.sleep(5.0)

    async def start(self):
        self._running = True
        nodes = self.discover_nodes(max_nodes=8)
        for n in nodes:
            t = asyncio.create_task(self._handle_peer(n))
            self._tasks.append(t)

    async def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    def get_tx_propagation(self, txid: str) -> Optional[List[Dict[str, Any]]]:
        """
        Returns real observed propagation timing if this transaction was captured by 2+ P2P nodes.
        """
        obs_list = self.observations.get(txid)
        if not obs_list or len(obs_list) < 2:
            return None

        sorted_obs = sorted(obs_list, key=lambda x: x["timestamp"])
        t0 = sorted_obs[0]["timestamp"]

        hops = []
        for i, obs in enumerate(sorted_obs):
            delta_ms = int((obs["timestamp"] - t0) * 1000)
            hops.append({
                "node_label": obs["node_label"],
                "peer_ip": obs["peer_ip"],
                "country": obs["country"],
                "country_code": obs["country_code"],
                "delta_ms": delta_ms,
                "is_first_seen": (i == 0)
            })
        return hops

_global_observer: Optional[P2PObserver] = None

def get_p2p_observer() -> P2PObserver:
    global _global_observer
    if _global_observer is None:
        _global_observer = P2PObserver()
    return _global_observer
