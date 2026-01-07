import json
import os

TRANSFORMS = {
    "trim": lambda value: value.strip() if isinstance(value, str) else value,
    "upper": lambda value: value.upper() if isinstance(value, str) else value,
    "lower": lambda value: value.lower() if isinstance(value, str) else value,
}


def date_yyyymmdd(value):
    if not isinstance(value, str):
        return value
    if len(value) != 8 or not value.isdigit():
        return value
    return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"


TRANSFORMS["date_yyyymmdd"] = date_yyyymmdd


def load_mapping(file_path):
    with open(file_path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if "extends" in raw:
        base_path = os.path.abspath(os.path.join(os.path.dirname(file_path), raw["extends"]))
        base = load_mapping(base_path)
        return merge_mappings(base, raw)
    return raw


def merge_mappings(base, overlay):
    merged = {**base, **overlay}

    base_fields = base.get("fields", {})
    overlay_fields = overlay.get("fields", {})
    override_fields = overlay.get("overrides", {}).get("fields", {})
    merged["fields"] = {**base_fields, **overlay_fields, **override_fields}

    base_rules = base.get("segmentRules", [])
    overlay_rules = overlay.get("segmentRules", [])
    override_rules = overlay.get("overrides", {}).get("segmentRules", [])
    merged["segmentRules"] = [*base_rules, *overlay_rules, *override_rules]

    merged.pop("extends", None)
    merged.pop("overrides", None)

    return merged


def map_segments(segments, mapping):
    output = {}

    for out_path, definition in (mapping.get("fields") or {}).items():
        matches = []
        for segment in segments:
            if segment.get("id") != definition.get("segment"):
                continue
            if not condition_matches(segment, definition.get("when")):
                continue
            value = extract_value(segment, definition)
            if value is not None:
                matches.append(value)

        if not matches:
            continue

        occurrence = definition.get("occurrence", "first")
        if isinstance(occurrence, int):
            if 1 <= occurrence <= len(matches):
                set_path(output, out_path, matches[occurrence - 1])
        elif occurrence == "all":
            set_path(output, out_path, matches)
        elif occurrence == "last":
            set_path(output, out_path, matches[-1])
        else:
            set_path(output, out_path, matches[0])

    for segment in segments:
        for rule in mapping.get("segmentRules", []) or []:
            if segment.get("id") != rule.get("segment"):
                continue
            if not rule_matches(segment, rule):
                continue
            for out_path, definition in (rule.get("map") or {}).items():
                value = extract_value(segment, definition)
                if value is not None:
                    set_path(output, out_path, value)

    return output


def rule_matches(segment, rule):
    if rule.get("when"):
        return condition_matches(segment, rule["when"])
    if rule.get("whenAny"):
        return any(condition_matches(segment, condition) for condition in rule["whenAny"])
    return True


def condition_matches(segment, condition):
    if not condition:
        return True
    value = get_element(segment, condition.get("element"), condition.get("component"))
    if value is None:
        return False
    if "equals" in condition:
        return value == condition["equals"]
    if isinstance(condition.get("in"), list):
        return value in condition["in"]
    return True


def extract_value(segment, definition):
    raw = get_element(segment, definition.get("element"), definition.get("component"))
    if raw is None:
        return None

    value = raw
    value_map = definition.get("valueMap") or {}
    if raw in value_map:
        value = value_map[raw]

    transform = definition.get("transform")
    if transform in TRANSFORMS:
        value = TRANSFORMS[transform](value)

    return value


def get_element(segment, element_index, component_index=None):
    if not element_index:
        return None
    elements = segment.get("elements", [])
    if element_index - 1 >= len(elements):
        return None
    element = elements[element_index - 1]
    if component_index is None:
        return element
    if isinstance(element, list) and component_index - 1 < len(element):
        return element[component_index - 1]
    return None


def set_path(obj, out_path, value):
    if value is None:
        return
    parts = out_path.split(".")
    cursor = obj
    for key in parts[:-1]:
        if key not in cursor or not isinstance(cursor[key], dict):
            cursor[key] = {}
        cursor = cursor[key]
    cursor[parts[-1]] = value


__all__ = ["load_mapping", "map_segments"]
