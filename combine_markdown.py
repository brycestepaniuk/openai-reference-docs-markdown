import pathlib

root = pathlib.Path(__file__).parent

# Order of folders in the unified markdown file
FOLDERS_IN_ORDER = [
    "openai-docs-api-reference",
    "openai-docs-guides",
    "openai-python-docs",
    "openai-node-js-docs",
    "openai-agents-python-docs",
    "openai-cookbook",
]

output = root / "openai-docs-unified.md"

def main():
    with output.open("w", encoding="utf-8") as out:
        for folder in FOLDERS_IN_ORDER:
            folder_path = root / folder
            if not folder_path.exists():
                print(f"Skipping missing folder: {folder}")
                continue

            for md_file in sorted(folder_path.rglob("*.md")):
                rel = md_file.relative_to(root)
                out.write("\n\n---\n\n")
                out.write(f"# {rel}\n\n")
                out.write(md_file.read_text(encoding="utf-8"))
                out.write("\n")

    print(f"\n🎉 Unified markdown written to: {output}\n")

if __name__ == "__main__":
    main()
