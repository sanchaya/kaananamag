import json
import sys
import time
from internetarchive import get_item, modify_metadata

PREFIX = (
    "ಕಾನನ ನಿಸರ್ಗದೆಡೆಗೆ ಪಯಣ — ಪ್ರಕೃತಿ, ವನ್ಯಜೀವಿ ಮತ್ತು ಪರಿಸರದ ಬಗೆಗಿನ "
    "ಕನ್ನಡದ ಮಾಸ ಪತ್ರಿಕೆ. Wildlife Conservation Group ಪ್ರಕಟಣೆ. "
    "2011 ರಿಂದ ನಿರಂತರವಾಗಿ ಪ್ರಕಟವಾಗುತ್ತಿದೆ. https://kaananamag.in\n\n"
)

def main():
    with open("issues.json") as f:
        data = json.load(f)

    identifiers = [b["identifier"] for b in data["books"]]
    total = len(identifiers)
    success = 0
    skipped = 0
    failed = 0

    for i, identifier in enumerate(identifiers, 1):
        print(f"[{i}/{total}] Processing: {identifier} ...", end=" ", flush=True)
        try:
            item = get_item(identifier)
            md = item.item_metadata
            current = md.get("metadata", {}).get("description", "")

            if current.startswith(PREFIX.strip()):
                print("SKIP (already has prefix)")
                skipped += 1
                continue

            new_description = PREFIX + current
            resp = modify_metadata(identifier, {"description": new_description})
            success += 1
            print("DONE")
            time.sleep(1)
        except Exception as e:
            print(f"FAIL: {e}")
            failed += 1

    print(f"\nDone. Updated: {success}, Skipped: {skipped}, Failed: {failed}")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
