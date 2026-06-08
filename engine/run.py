from __future__ import annotations

import argparse
import asyncio
import os

from config import DATA_DIR
from engine.simulation import run_crucible
from transport.bridge import Bridge


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="seed", choices=["seed", "generate"])
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()

    bridge = Bridge()
    await run_crucible(bridge, mode=args.mode)
    print(f"phase={bridge.state['phase']} wedge={bridge.state['hud']['wedge']}")
    if args.record:
        path = os.path.join(DATA_DIR, "recorded_run.json")
        bridge.dump_recording(path)
        print(f"recorded={path}")


if __name__ == "__main__":
    asyncio.run(main())
