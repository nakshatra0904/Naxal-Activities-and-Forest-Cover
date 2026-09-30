"""Fetch and verify public-domain USGS GMTED2010 30-second mean elevation."""
from pathlib import Path
import hashlib
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
ZIP = WORK / "mn30_grd.zip"
URL = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/topo/downloads/GMTED/Grid_ZipFiles/mn30_grd.zip"
SHA256 = "dfd0d6c6486f4da22109be6107c93a70ef9917a5b6f954cd82d87cf8b920149d"

if not ZIP.exists():
    temporary = ZIP.with_suffix(".zip.part")
    with urllib.request.urlopen(URL, timeout=900) as response, temporary.open("wb") as target:
        shutil.copyfileobj(response, target)
    temporary.replace(ZIP)
sha = hashlib.sha256()
with ZIP.open("rb") as source:
    for block in iter(lambda: source.read(1024 * 1024), b""):
        sha.update(block)
digest = sha.hexdigest()
if digest != SHA256:
    raise ValueError(f"USGS terrain archive changed; expected {SHA256}, got {digest}")

destination = WORK / "terrain"
destination.mkdir(exist_ok=True)
with zipfile.ZipFile(ZIP) as archive:
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if not target.is_relative_to(destination.resolve()):
            raise ValueError(f"Unsafe archive member: {member.filename}")
    archive.extractall(destination)
assert (destination / "mn30_grd" / "hdr.adf").exists()
print(f"Verified USGS terrain archive and extracted grid to {destination}")
