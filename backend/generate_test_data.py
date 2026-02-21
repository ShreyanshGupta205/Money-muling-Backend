"""
Test Data Generator
===================
Creates a synthetic CSV with embedded fraud patterns and legitimate
activity for end-to-end testing of the Financial Forensics Engine.

Patterns embedded:
  • 3 currency cycle rings  (3, 4, and 5 members)
  • 2 smurfing accounts     (1 fan-in, 1 fan-out)
  • 1 shell chain           (5-hop)
  • 1 payroll hub           (false positive)
  • 1 merchant account      (false positive)
  • 1 salary receiver       (false positive)
  • ~700 normal random transactions

Usage:
    python generate_test_data.py           # writes test_data.csv
    python generate_test_data.py 5000      # writes 5000 normal txns
"""

import csv
import random
import sys
from datetime import datetime, timedelta

random.seed(42)

BASE_TIME = datetime(2025, 1, 1, 8, 0, 0)
TXN_COUNTER = 0


def _txn_id():
    global TXN_COUNTER
    TXN_COUNTER += 1
    return f"TXN_{TXN_COUNTER:06d}"


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generate(n_normal: int = 700, filename: str = "test_data.csv"):
    rows: list = []

    # ------------------------------------------------------------------
    # 1. Cycle rings
    # ------------------------------------------------------------------
    # Ring 1: 3-member cycle  ACC_C01 → ACC_C02 → ACC_C03 → ACC_C01
    ring1 = ["ACC_C01", "ACC_C02", "ACC_C03"]
    t = BASE_TIME + timedelta(days=5)
    for i in range(len(ring1)):
        for rep in range(3):
            rows.append([_txn_id(), ring1[i], ring1[(i + 1) % len(ring1)],
                         round(random.uniform(8000, 12000), 2),
                         _fmt(t + timedelta(hours=rep * 2 + i))])

    # Ring 2: 4-member cycle
    ring2 = ["ACC_C04", "ACC_C05", "ACC_C06", "ACC_C07"]
    t = BASE_TIME + timedelta(days=10)
    for i in range(len(ring2)):
        for rep in range(2):
            rows.append([_txn_id(), ring2[i], ring2[(i + 1) % len(ring2)],
                         round(random.uniform(15000, 25000), 2),
                         _fmt(t + timedelta(hours=rep * 3 + i))])

    # Ring 3: 5-member cycle
    ring3 = ["ACC_C08", "ACC_C09", "ACC_C10", "ACC_C11", "ACC_C12"]
    t = BASE_TIME + timedelta(days=15)
    for i in range(len(ring3)):
        rows.append([_txn_id(), ring3[i], ring3[(i + 1) % len(ring3)],
                     round(random.uniform(5000, 8000), 2),
                     _fmt(t + timedelta(hours=i))])

    # ------------------------------------------------------------------
    # 2. Smurfing — Fan-In: 12 senders → ACC_SMURF_IN within 48 hours
    # ------------------------------------------------------------------
    t = BASE_TIME + timedelta(days=20)
    for i in range(12):
        rows.append([_txn_id(), f"ACC_FI_{i:02d}", "ACC_SMURF_IN",
                     round(random.uniform(4900, 5100), 2),
                     _fmt(t + timedelta(hours=i * 3))])

    # ------------------------------------------------------------------
    # 3. Smurfing — Fan-Out: ACC_SMURF_OUT → 12 receivers within 48 hrs
    # ------------------------------------------------------------------
    t = BASE_TIME + timedelta(days=22)
    for i in range(12):
        rows.append([_txn_id(), "ACC_SMURF_OUT", f"ACC_FO_{i:02d}",
                     round(random.uniform(4900, 5100), 2),
                     _fmt(t + timedelta(hours=i * 3))])

    # ------------------------------------------------------------------
    # 4. Shell chain:  SRC → SH1 → SH2 → SH3 → SH4 → DEST
    #    SH1-SH4 each have degree ≤ 3
    # ------------------------------------------------------------------
    chain = ["ACC_SRC", "ACC_SH1", "ACC_SH2", "ACC_SH3", "ACC_SH4", "ACC_DEST"]
    t = BASE_TIME + timedelta(days=25)
    for i in range(len(chain) - 1):
        rows.append([_txn_id(), chain[i], chain[i + 1],
                     round(random.uniform(20000, 30000), 2),
                     _fmt(t + timedelta(hours=i * 2))])

    # ------------------------------------------------------------------
    # 5. FALSE POSITIVE — Payroll hub: ACC_PAYROLL → 25 employees, same amount
    # ------------------------------------------------------------------
    for month in range(6):
        t = BASE_TIME + timedelta(days=30 * month + 1)
        for emp in range(25):
            rows.append([_txn_id(), "ACC_PAYROLL", f"ACC_EMP_{emp:02d}",
                         5000.00,
                         _fmt(t + timedelta(minutes=emp))])

    # ------------------------------------------------------------------
    # 6. FALSE POSITIVE — Salary receiver: gets same amount monthly
    # ------------------------------------------------------------------
    for month in range(6):
        t = BASE_TIME + timedelta(days=30 * month + 1)
        rows.append([_txn_id(), "ACC_EMPLOYER", "ACC_SALARY_RX",
                     75000.00, _fmt(t)])

    # ------------------------------------------------------------------
    # 7. FALSE POSITIVE — Merchant: 60 unique buyers, stable amounts
    # ------------------------------------------------------------------
    for buyer in range(60):
        t = BASE_TIME + timedelta(days=random.randint(1, 180),
                                  hours=random.randint(8, 20))
        rows.append([_txn_id(), f"ACC_BUYER_{buyer:03d}", "ACC_MERCHANT",
                     round(random.choice([29.99, 49.99, 99.99]), 2),
                     _fmt(t)])

    # ------------------------------------------------------------------
    # 8. Normal random transactions
    # ------------------------------------------------------------------
    normal_accounts = [f"ACC_N{i:04d}" for i in range(200)]
    for _ in range(n_normal):
        sender = random.choice(normal_accounts)
        receiver = random.choice([a for a in normal_accounts if a != sender])
        amount = round(random.uniform(50, 50000), 2)
        t = BASE_TIME + timedelta(
            days=random.randint(0, 180),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        rows.append([_txn_id(), sender, receiver, amount, _fmt(t)])

    # Shuffle and write
    random.shuffle(rows)

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "sender_id", "receiver_id", "amount", "timestamp"])
        writer.writerows(rows)

    print(f"✓ Generated {len(rows)} transactions → {filename}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 700
    generate(n)
