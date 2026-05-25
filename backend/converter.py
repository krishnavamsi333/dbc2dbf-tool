import sys
import os
import canmatrix.formats


def validate_input_file(input_file):
    """
    Validate input DBC file
    """
    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)

    if not input_file.lower().endswith(".dbc"):
        print("[ERROR] Input file must be a .dbc file")
        sys.exit(1)


def validate_output_file(output_file):
    """
    Validate output DBF file
    """
    if not output_file.lower().endswith(".dbf"):
        print("[ERROR] Output file must be a .dbf file")
        sys.exit(1)


def convert_dbc_to_dbf(input_file, output_file):
    """
    Convert DBC to DBF using canmatrix
    """
    try:
        print("[INFO] Loading DBC file...")

        db = canmatrix.formats.loadp(input_file)

        print("[INFO] Converting to DBF...")

        canmatrix.formats.dumpp(db, output_file)

        print("[SUCCESS] Conversion completed")
        print(f"[OUTPUT] {output_file}")

    except Exception as e:
        print("[ERROR] Conversion failed")
        print(e)
        sys.exit(1)


def main():
    """
    CLI entry point.

    Usage:
        python3 backend/converter.py input.dbc output.dbf [--clean]

    Options:
        --clean   Sanitize the DBC file before converting
    """
    args = sys.argv[1:]
    do_clean = "--clean" in args
    args = [a for a in args if not a.startswith("--")]

    if len(args) != 2:
        print("Usage:")
        print("  python3 backend/converter.py input.dbc output.dbf [--clean]")
        print("")
        print("Options:")
        print("  --clean   Sanitize the DBC file before converting")
        sys.exit(1)

    input_file = args[0]
    output_file = args[1]

    validate_input_file(input_file)
    validate_output_file(output_file)

    if do_clean:
        import tempfile
        from cleaner import clean_dbc_file

        tmp_cleaned = tempfile.mktemp(suffix=".dbc")
        try:
            print("[INFO] Cleaning DBC file...")
            result = clean_dbc_file(input_file, tmp_cleaned)
            if result["cleaned"]:
                print(f"[INFO] Applied fixes: {', '.join(result['changes'])}")
            else:
                print("[INFO] No issues found, file is clean")
            convert_dbc_to_dbf(tmp_cleaned, output_file)
        finally:
            if os.path.exists(tmp_cleaned):
                os.remove(tmp_cleaned)
    else:
        convert_dbc_to_dbf(input_file, output_file)


if __name__ == "__main__":
    main()