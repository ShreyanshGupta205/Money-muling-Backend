import json

with open("test_result.json", "rb") as f:
    d = json.loads(f.read())

print("=== SUMMARY ===")
for k, v in d["summary"].items():
    print("  %s: %s" % (k, v))

print("\n=== FRAUD RINGS (%d) first 5 ===" % len(d["fraud_rings"]))
for r in d["fraud_rings"][:5]:
    print("  %s: %s | risk=%s | members=%s" % (r["ring_id"], r["pattern_type"], r["risk_score"], r["member_accounts"]))

print("\n=== TOP 10 SUSPICIOUS ACCOUNTS ===")
for a in d["suspicious_accounts"][:10]:
    print("  %s: score=%s | patterns=%s | ring=%s" % (a["account_id"], a["suspicion_score"], a["detected_patterns"], a["ring_id"]))

# Check known fraud accounts
known_fraud = ["ACC_C01","ACC_C02","ACC_C03","ACC_C04","ACC_C05","ACC_C06","ACC_C07",
               "ACC_C08","ACC_C09","ACC_C10","ACC_C11","ACC_C12",
               "ACC_SMURF_IN","ACC_SMURF_OUT"]
known_fp = ["ACC_PAYROLL","ACC_SALARY_RX","ACC_MERCHANT"]

detected_ids = set(a["account_id"] for a in d["suspicious_accounts"])

print("\n=== KNOWN FRAUD DETECTION ===")
for acc in known_fraud:
    marker = "HIT" if acc in detected_ids else "MISS"
    sa = None
    for a in d["suspicious_accounts"]:
        if a["account_id"] == acc:
            sa = a
            break
    score = sa["suspicion_score"] if sa else 0
    print("  [%s] %s: score=%s" % (marker, acc, score))

print("\n=== FALSE POSITIVE CHECK ===")
for acc in known_fp:
    marker = "WRONGLY FLAGGED" if acc in detected_ids else "OK excluded"
    print("  [%s] %s" % (marker, acc))

# Count normal accounts flagged
normal_flagged = [a for a in d["suspicious_accounts"] if a["account_id"].startswith("ACC_N")]
print("\n=== NORMAL ACCOUNTS FLAGGED: %d ===" % len(normal_flagged))
for a in normal_flagged[:5]:
    print("  %s: score=%s" % (a["account_id"], a["suspicion_score"]))

# Schema validation
assert "suspicious_accounts" in d
assert "fraud_rings" in d
assert "summary" in d
assert "graph_data" in d
print("\n=== Schema validation passed ===")
