"""Re-record the demo's committed recording from the stand-in model.

Run after changing DocQA's prompt, its tools or the demo's documents, when `redline demo` reports
a missing recording:

    uv run --locked python scripts/record_demo.py

It writes `src/redline/data/demo.cassette.json`. When a real model is attached, this script is where
the stand-in is swapped for it, and the recording then stops being a stand-in recording.
"""

from redline.demo import RECORDING, run_demo
from redline.models.cassette import Cassette, Recorder
from redline.models.standin import MODEL_ID, CredulousStandIn


def main() -> int:
    """Record both demo trials and save the recording. Returns a process exit code."""
    cassette = Cassette()
    run_demo(Recorder(CredulousStandIn(), cassette), MODEL_ID)
    cassette.save(RECORDING)
    print(f"recorded {len(cassette)} calls to {RECORDING}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
