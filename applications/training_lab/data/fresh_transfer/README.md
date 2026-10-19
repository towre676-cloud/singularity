# Fresh transfer corpus

These 36 readable document fragments were acquired before the deployment-transfer
prediction experiment. Each of three domains has four development documents and
eight heldout documents. The names, fixed character offsets and split hash rule
are declared by `scripts/fetch_fresh_transfer_corpus.py`; `manifest.json` records
the source URLs, source and fragment SHA-256 identities, split ranks, and licenses.
Every individual JSON contains the exact selected text and overlap evidence.

The literary fragments are from twelve different English-language books in the
public domain in the United States, obtained from Project Gutenberg. Gutenberg
headers and footers are excluded. Selection starts 2,000 Unicode characters after
the book's START marker and retains 16,384 characters, so some fragments include
introductions or contents pages. Every declared title is checked against its
source START marker. During acquisition QA, the Great Expectations URL was
corrected from ebook 140 (The Jungle) to ebook 1400 before protocol freeze or any
model scoring; this correction did not depend on model results.

The technical reference and Python source fragments come from CPython v3.12.0,
commit `0fb18b02c8ad56299d6a2910be0bab8ad601ef24`, and retain the first 16,384
characters, including any initial license comments. Their license and copyright
notices are retained in [CPYTHON_LICENSE.txt](CPYTHON_LICENSE.txt). The annotated
release tag and immutable commit are recorded separately in the manifest.

All fragments were checked against all 40 documents in the earlier cross-domain
corpus and against the other 35 new fragments. Exact UTF-8 SHA-256 matches and
case-folded word-five-shingle containment of at least 0.35 cause acquisition to
stop without substituting another document. The Python modules also exclude every
module name in the previous source-code corpus. The full acquisition downloads
remain outside Git; only the selected fragments are published.

Run `python scripts/fetch_fresh_transfer_corpus.py --verify` from the repository
root to verify the retained fragments and split counts without network access.
Acquisition into a new output directory additionally requires `--cache` pointing
outside the repository. Gutenberg source URLs can change over time: the retained
fragment and source hashes bind this acquisition. These documents are fresh to
this repository's experiments; absence from model pretraining is not established.
