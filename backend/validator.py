import os
import re


class ValidationError(Exception):
    """Raised when a DBC file fails validation"""
    pass


# Known required DBC keywords
DBC_REQUIRED_SECTIONS = ["VERSION", "NS_", "BS_", "BU_"]
DBC_MESSAGE_PATTERN = re.compile(r"^BO_\s+\d+\s+\w+\s*:\s*\d+\s+\w+", re.MULTILINE)
DBC_SIGNAL_PATTERN = re.compile(r"^\s+SG_\s+\w+\s*:", re.MULTILINE)


def validate_dbc_file(filepath):
    """
    Validate a DBC file for structure and basic correctness.

    Returns a dict with:
        - valid (bool)
        - warnings (list of strings)
        - stats (dict: message_count, signal_count, file_size_kb)
    """
    warnings = []
    stats = {}

    # --- File-level checks ---
    if not os.path.exists(filepath):
        raise ValidationError(f"File not found: {filepath}")

    if not filepath.lower().endswith(".dbc"):
        raise ValidationError("File must have a .dbc extension")

    file_size = os.path.getsize(filepath)
    if file_size == 0:
        raise ValidationError("File is empty")

    stats["file_size_kb"] = round(file_size / 1024, 2)

    # --- Encoding check ---
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                content = f.read()
            warnings.append("File is not UTF-8 encoded; latin-1 fallback used. Consider re-saving as UTF-8.")
        except Exception as e:
            raise ValidationError(f"Cannot read file: {e}")

    # --- Required section checks ---
    for section in DBC_REQUIRED_SECTIONS:
        if section not in content:
            warnings.append(f"Missing expected DBC section: '{section}'")

    # --- Version line ---
    if not content.strip().startswith("VERSION"):
        warnings.append("File does not start with VERSION keyword — may not be a valid DBC file")

    # --- Message and signal counts ---
    messages = DBC_MESSAGE_PATTERN.findall(content)
    signals = DBC_SIGNAL_PATTERN.findall(content)
    stats["message_count"] = len(messages)
    stats["signal_count"] = len(signals)

    if stats["message_count"] == 0:
        warnings.append("No BO_ message definitions found — file may be empty or malformed")

    # --- Bracket / quote balance (basic) ---
    if content.count('"') % 2 != 0:
        warnings.append("Odd number of double-quotes detected — possible unclosed string literal")

    return {
        "valid": True,
        "warnings": warnings,
        "stats": stats,
    }