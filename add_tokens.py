"""Quick verify + add bot tokens to pool via SSH to server."""
import subprocess, sys

TOKENS = [
    "8481599466:AAG5Sw_f2asJQgF8dOikWYmkMuHeC1wGbB4",
    "8638742414:AAEIGgDGHQI0tfqETiyP6cENzES5CGjgZuA",
    "8652845860:AAFyzr_n9uTDU79ZkjKis-g7ywnDN-NYEY4",
    "8775214696:AAFaXWvy_Xkrf4F_u1qvpzw_BQ_LMIhn83Q",
    "8665818792:AAEbqXKf8DFscS-gtVtV080NfIVSdffzMoI",
    "8725083177:AAFcvVJTaOhx_YZvsrn354pZ1RI511KKLHY",
    "8721488448:AAGMOTs2bepcNma_lMD9wZ9J94qBebZOKUY",
    "8699834359:AAG2POU6xWX-CCJVHufcO0zTLS_juK6Z6ug",
]

args = " ".join(TOKENS)
cmd = f'ssh -o ConnectTimeout=10 root@5.42.112.91 "cd /root/meeposite/backend && python -m scripts.seed_bots {args}"'
print(f"Running seed_bots with {len(TOKENS)} tokens...")
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)
