import re
import os


def clean_dbc_file(input_path, output_path):
    """
    Sanitize and fix common issues in a DBC file before conversion.

    Fixes applied:
        - Re-encode to UTF-8 (strips non-ASCII junk)
        - Normalize line endings to LF
        - Remove BOM if present
        - Strip trailing whitespace from each line
        - Remove duplicate blank lines (collapse to single blank)
        - Fix missing space after BO_ message ID
        - Fix missing quotes around empty signal units
        - Fix Windows-style carriage returns inside strings
        - Remove NULL bytes

    Returns a dict describing what was cleaned.
    """
    changes = []

    # FIX: Detect BOM from raw bytes BEFORE reading, since utf-8-sig strips it
    # on both reads — making the old comparison always equal (always False).
    with open(input_path, "rb") as f:
        raw_start = f.read(3)
    has_bom = raw_start == b'\xef\xbb\xbf'

    # --- Read with encoding fallback ---
    try:
        with open(input_path, "r", encoding="utf-8-sig") as f:  # utf-8-sig strips BOM
            content = f.read()
        if has_bom:
            changes.append("Removed UTF-8 BOM")
    except UnicodeDecodeError:
        with open(input_path, "r", encoding="latin-1") as f:
            content = f.read()
        changes.append("Re-encoded from latin-1 to UTF-8")

    # FIX: Capture original AFTER reading (and after BOM strip) so that
    # was_modified correctly reflects all subsequent text changes.
    original = content

    # --- Remove NULL bytes ---
    cleaned = content.replace("\x00", "")
    if cleaned != content:
        changes.append("Removed NULL bytes")
    content = cleaned

    # --- Normalize line endings to LF ---
    cleaned = content.replace("\r\n", "\n").replace("\r", "\n")
    if cleaned != content:
        changes.append("Normalized line endings to LF")
    content = cleaned

    # --- Strip trailing whitespace per line ---
    lines = content.split("\n")
    stripped = [line.rstrip() for line in lines]
    if stripped != lines:
        changes.append("Stripped trailing whitespace from lines")
    lines = stripped

    # --- Collapse multiple consecutive blank lines into one ---
    collapsed = []
    blank_streak = 0
    for line in lines:
        if line.strip() == "":
            blank_streak += 1
            if blank_streak <= 1:
                collapsed.append(line)
        else:
            blank_streak = 0
            collapsed.append(line)
    if collapsed != lines:
        changes.append("Collapsed consecutive blank lines")
    lines = collapsed

    content = "\n".join(lines)

    # --- Fix missing space in BO_ definitions: "BO_ 123Name" → "BO_ 123 Name" ---
    fixed = re.sub(r"(BO_\s+)(\d+)(\w)", r"\1\2 \3", content)
    if fixed != content:
        changes.append("Fixed missing space in BO_ message definitions")
    content = fixed

    # FIX: Corrected signal unit regex.
    # Old pattern used (?!") + \s which almost never matched (requires a
    # non-quote char followed by whitespace — misses end-of-line cases entirely).
    # New pattern: matches a signal bit layout + value range followed by
    # nothing or only spaces before end-of-line, and injects empty quotes.
    fixed = re.sub(
        r'(\|\d+@\d+[+-]\s*\([^)]+\)\s*\[[^\]]*\])([ \t]*)$',
        r'\1 ""',
        content,
        flags=re.MULTILINE,
    )
    if fixed != content:
        changes.append("Added missing quotes around empty signal units")
    content = fixed

    # --- Ensure file ends with a newline ---
    if not content.endswith("\n"):
        content += "\n"
        changes.append("Added missing trailing newline")

    # --- Write cleaned file ---
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    was_modified = content != original

    return {
        "cleaned": was_modified,
        "changes": changes,
        "original_size_bytes": os.path.getsize(input_path),
        "cleaned_size_bytes": os.path.getsize(output_path),
    }
