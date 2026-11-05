from pathlib import Path
import lzma
r=Path(__file__).parent
for p in (r/"input").glob("*.xz"):
 (r/p.stem).write_bytes(lzma.decompress(p.read_bytes()))
print("Exact input rows and patterns prepared")
