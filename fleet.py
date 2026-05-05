"""
Synthetic device fleet for the Nexthink Test Harness.
Generates 100 realistic devices: 80% St. Paul MN, 20% Monheim Germany.
Seeded so the fleet is stable across restarts.
"""

import random
from datetime import datetime, timezone, timedelta

SEED = 42
RNG = random.Random(SEED)

# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------
SITES = {
    "St. Paul": {
        "weight": 0.80,
        "country": "US",
        "timezone": "America/Chicago",
        "departments": ["IT", "Finance", "HR", "Operations", "Legal", "Marketing", "Sales"],
    },
    "Monheim": {
        "weight": 0.20,
        "country": "DE",
        "timezone": "Europe/Berlin",
        "departments": ["IT", "Finance", "Operations", "Engineering", "R&D"],
    },
}

OS_POOL = [
    {"name": "Windows 11", "version": "11", "builds": ["22H2", "23H2", "24H2"], "weight": 0.55},
    {"name": "Windows 10", "version": "10", "builds": ["21H2", "22H2"], "weight": 0.40},
    {"name": "Windows 11 SE", "version": "11", "builds": ["22H2"], "weight": 0.05},
]

AGENT_VERSIONS = ["6.33.1", "6.33.2", "6.34.0", "6.34.1", "6.35.0"]

COMPLIANCE_STATES = [
    ("compliant", 0.70),
    ("non-compliant", 0.20),
    ("pending", 0.10),
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Susan", "Richard", "Jessica", "Joseph", "Karen",
    "Thomas", "Sarah", "Charles", "Lisa", "Klaus", "Heike", "Jürgen", "Petra",
    "Hans", "Sabine", "Stefan", "Monika", "Andreas", "Christine",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris",
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner",
    "Becker", "Hoffmann", "Schulz",
]


def _weighted_choice(pool, key="weight"):
    """Pick a random item from pool using weighted probabilities."""
    weights = [item[key] for item in pool]
    return RNG.choices(pool, weights=weights, k=1)[0]


def _weighted_choice_dict(d):
    """Pick from a dict of {value: weight}."""
    items = list(d.items())
    weights = [w for _, w in items]
    return RNG.choices([v for v, _ in items], weights=weights, k=1)[0]


def _days_ago(n):
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_device(index):
    """Generate a single synthetic device."""
    # Site
    site_name = RNG.choices(
        list(SITES.keys()),
        weights=[s["weight"] for s in SITES.values()],
        k=1,
    )[0]
    site = SITES[site_name]

    # OS
    os_entry = _weighted_choice(OS_POOL)
    os_build = RNG.choice(os_entry["builds"])

    # User
    first = RNG.choice(FIRST_NAMES)
    last = RNG.choice(LAST_NAMES)
    username = f"{first[0].lower()}{last.lower()}"
    department = RNG.choice(site["departments"])

    # Hardware
    ram_gb = RNG.choice([8, 8, 8, 16, 16, 16, 32, 32, 64])
    disk_total_gb = RNG.choice([256, 256, 512, 512, 512, 1024])
    disk_free_pct = round(RNG.uniform(5, 85), 1)
    cpu_usage = round(RNG.uniform(1, 95), 1)

    # Health signals — bias non-compliant/stale devices toward worse metrics
    compliance = _weighted_choice_dict(dict(COMPLIANCE_STATES))
    last_seen_days = RNG.choices(
        [0, 1, 2, 3, 7, 14, 30],
        weights=[40, 20, 15, 10, 7, 5, 3],
        k=1,
    )[0]

    agent_version = RNG.choice(AGENT_VERSIONS)

    # Non-compliant devices skew toward stale / high CPU
    if compliance == "non-compliant":
        last_seen_days = RNG.choices([3, 7, 14, 30], weights=[20, 30, 30, 20], k=1)[0]
        cpu_usage = round(RNG.uniform(40, 95), 1)
        disk_free_pct = round(RNG.uniform(5, 25), 1)

    device_id = f"dev-{index:04d}"
    hostname = f"{site_name[:3].upper().replace(' ', '')}-{department[:3].upper()}-{index:04d}"

    return {
        "device_id": device_id,
        "device_name": hostname,
        "site": site_name,
        "country": site["country"],
        "timezone": site["timezone"],
        "department": department,
        "os_name": os_entry["name"],
        "os_version": os_entry["version"],
        "os_build": os_build,
        "ram_gb": ram_gb,
        "disk_total_gb": disk_total_gb,
        "disk_free_pct": disk_free_pct,
        "cpu_usage": cpu_usage,
        "compliance_status": compliance,
        "agent_version": agent_version,
        "last_seen_days": last_seen_days,
        "last_seen": _days_ago(last_seen_days),
        "user": {
            "username": username,
            "display_name": f"{first} {last}",
            "department": department,
            "email": f"{username}@corp.example.com",
        },
    }


def generate_fleet(count=100):
    """Generate the full synthetic fleet. Stable due to seeded RNG."""
    return [_generate_device(i + 1) for i in range(count)]


# Module-level singleton — generated once on import
FLEET = generate_fleet(100)


def get_fleet():
    return FLEET


def get_device(device_id):
    for d in FLEET:
        if d["device_id"] == device_id:
            return d
    return None
