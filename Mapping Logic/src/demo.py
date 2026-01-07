import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.mapper import load_mapping, map_segments


def parse_x12(text, element_sep="*", segment_sep="~", component_sep=":"):
    segments = []
    for raw_segment in text.split(segment_sep):
        raw_segment = raw_segment.strip()
        if not raw_segment:
            continue
        parts = raw_segment.split(element_sep)
        segment_id = parts[0]
        elements = []
        for element in parts[1:]:
            if component_sep in element:
                elements.append(element.split(component_sep))
            else:
                elements.append(element)
        segments.append({"id": segment_id, "elements": elements})
    return segments


def main():
    parser = argparse.ArgumentParser(description="Demo X12 to JSON mapping")
    parser.add_argument(
        "edi_file",
        nargs="?",
        default="samples/850_acme.edi",
        help="Path to an X12 file",
    )
    parser.add_argument(
        "--mapping",
        default="mapping/clients/acme/850.json",
        help="Path to mapping JSON",
    )
    args = parser.parse_args()

    edi_path = Path(args.edi_file)
    mapping_path = Path(args.mapping)

    segments = parse_x12(edi_path.read_text(encoding="utf-8"))
    mapping = load_mapping(mapping_path)
    output = map_segments(segments, mapping)

    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
