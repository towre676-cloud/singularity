Connected volume-eight result — November 4, 2026

Read CONNECTED_VOLUME8.md for the complete theorem, proof, scope and proposed changes.
The connected minimum is SIX, while the original disconnected minimum remains seven.

Replay (Python 3 standard library only, no network):
  cd replay
  python connected_check.py --optimize --enumerate-connected

The six large witnesses are compact exact recipes. The Theta223 pair is also
provided as two complete 1,666-vertex edge lists and independently enumerated.
The new replay relies on the established exact source law bundled here.

proposed.patch adds five files only; it has not been applied to the repository.
Apply after review from the pinned repository root with: git apply proposed.patch

The original reader was separately replayed unchanged; see existing_reader_replay.log.
SHA256SUMS.json records all packaged files except itself.
