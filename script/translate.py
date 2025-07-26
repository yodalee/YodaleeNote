import oyaml as yaml  # pip install pyyaml
from pathlib import Path

def parse_markdown_with_frontmatter(filepath):
    """
    Parse markdown file, separating YAML front matter and content.
    Returns (metadata_dict, content_str)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if lines and lines[0].strip() == "---":
        # Find end of front matter
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                metadata = yaml.safe_load("".join(lines[1:i]))
                content = "".join(lines[i+1:])
                return metadata or {}, content
    # No front matter
    return {}, "".join(lines)

def dump_markdown_with_frontmatter(metadata, content):
    """
    Dump metadata and content to markdown with YAML front matter.
    """
    front = "---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\n"
    return front + content

def translate(text, target_lang="en"):
    """
    Dummy translation function, replace with your translation API.
    """
    return f"[{target_lang}] {text}"

def translate_post(input_path: Path, src_lang="zh-tw", target_lang="en"):
    # Parse markdown and front matter
    metadata, content = parse_markdown_with_frontmatter(input_path)

    # Translate the 'title' field if it exists
    if 'title' in metadata:
        metadata['title'] = translate(metadata['title'], target_lang)

    # Add the AITranslated flag
    metadata['AITranslated'] = True
    metadata['lang'] = target_lang  # optionally track the language

    # Translate the Markdown content body
    content = translate(content, target_lang)

    # Determine output path
    relative_path = input_path.relative_to(f"content/{src_lang}")
    output_path = Path(f"content/{target_lang}") / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save translated post
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(dump_markdown_with_frontmatter(metadata, content))

    print(f"Translated: {input_path} → {output_path}")

def main():
    import sys
    if len(sys.argv) != 3:
        print("Usage: python translate.py <input_md_file> <target_lang>")
        exit(1)
    input_md_file = Path(sys.argv[1])
    target_lang = sys.argv[2]

    if not input_md_file.exists() or not input_md_file.is_file() or input_md_file.suffix.lower() != ".md":
        print(f"Error: Input file {input_md_file} does not exist or is not a markdown (.md) file.")
        exit(1)

    src_lang = "zh-tw"
    # Check if input file is under content/zh-tw
    try:
        relative_path = input_md_file.relative_to(f"content/{src_lang}")
    except ValueError:
        print(f"Error: Input file must be under content/{src_lang}/")
        exit(1)

    output_dir = Path(f"content/{target_lang}") / relative_path.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    translate_post(input_md_file, src_lang, target_lang)

if __name__ == '__main__':
    main()
