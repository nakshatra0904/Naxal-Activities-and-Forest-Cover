"""Download the official FSI 2001 PDF for optional table re-extraction."""
from pathlib import Path
import hashlib
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "work" / "sfr_2001.pdf"
URL = "https://fsi.nic.in/documents/sfr_2001_hindi.pdf"
EXPECTED = "4fe576566d1561f37b420a38e9229678ccb183c43b5be29aaae580ce2b6b00f1"

if DEST.exists():
    digest = hashlib.sha256(DEST.read_bytes()).hexdigest()
    if digest == EXPECTED:
        print(f"Verified existing report: {DEST}")
        raise SystemExit(0)
    raise ValueError(f"Unexpected existing PDF checksum at {DEST}: {digest}")

DEST.parent.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen(URL, timeout=90) as response:
    payload = response.read()
digest = hashlib.sha256(payload).hexdigest()
if digest != EXPECTED:
    raise ValueError(f"Source PDF changed; expected {EXPECTED}, got {digest}")
DEST.write_bytes(payload)
print(f"Downloaded and verified {DEST}")
