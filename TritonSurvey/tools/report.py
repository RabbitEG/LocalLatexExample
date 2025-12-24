import argparse
import os
import re
import sys
from collections import defaultdict


SECTION_LEVELS = {
    "section": 1,
    "subsection": 2,
    "subsubsection": 3,
    "paragraph": 4,
    "subparagraph": 5,
}

MATH_ENVS = [
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "eqnarray",
    "eqnarray*",
]

COMMANDS_STRIP_ARGS = [
    "label",
    "ref",
    "pageref",
    "eqref",
    "cite",
    "includegraphics",
    "input",
    "include",
    "bibliography",
    "bibliographystyle",
    "usepackage",
    "documentclass",
    "graphicspath",
    "geometry",
    "lstset",
    "ctexset",
    "definecolor",
    "setlength",
    "linespread",
    "IfFileExists",
    "PassOptionsToPackage",
    "appendix",
    "tableofcontents",
    "newpage",
    "clearpage",
    "sloppy",
]


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def strip_comments(line):
    out = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "%":
            if i > 0 and line[i - 1] == "\\":
                out.append(ch)
                i += 1
                continue
            break
        out.append(ch)
        i += 1
    return "".join(out)


def resolve_tex_path(name, base_dir):
    name = name.strip().replace("/", os.sep)
    path = os.path.normpath(os.path.join(base_dir, name))
    if os.path.isfile(path):
        return path
    if not os.path.splitext(path)[1]:
        tex_path = path + ".tex"
        if os.path.isfile(tex_path):
            return tex_path
    return None


def expand_file(path, seen):
    path = os.path.normpath(path)
    if path in seen:
        return []
    seen.add(path)
    lines = []
    base_dir = os.path.dirname(path)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw_lines = f.readlines()
    except OSError:
        return []

    include_re = re.compile(r"\\(input|include)\{([^}]+)\}")
    for raw in raw_lines:
        line = strip_comments(raw.rstrip("\n"))
        if not line:
            lines.append("")
            continue
        matches = list(include_re.finditer(line))
        if not matches:
            lines.append(line)
            continue
        pos = 0
        for match in matches:
            pre = line[pos : match.start()]
            if pre.strip():
                lines.append(pre)
            inc_name = match.group(2)
            inc_path = resolve_tex_path(inc_name, base_dir)
            if inc_path:
                lines.extend(expand_file(inc_path, seen))
            pos = match.end()
        post = line[pos:]
        if post.strip():
            lines.append(post)
    return lines


def collect_tex_files(path, seen):
    path = os.path.normpath(path)
    if path in seen:
        return []
    seen.add(path)
    files = [path]
    base_dir = os.path.dirname(path)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw_lines = f.readlines()
    except OSError:
        return files

    include_re = re.compile(r"\\(input|include)\{([^}]+)\}")
    for raw in raw_lines:
        line = strip_comments(raw.rstrip("\n"))
        if not line:
            continue
        for match in include_re.finditer(line):
            inc_name = match.group(2)
            inc_path = resolve_tex_path(inc_name, base_dir)
            if inc_path:
                files.extend(collect_tex_files(inc_path, seen))
    return files


def remove_math(text):
    for env in MATH_ENVS:
        pattern = r"\\begin\{%s\}.*?\\end\{%s\}" % (re.escape(env), re.escape(env))
        text = re.sub(pattern, "", text, flags=re.S)
    text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.S)
    text = re.sub(r"\\\[(.*?)\\\]", "", text, flags=re.S)
    text = re.sub(r"\\\((.*?)\\\)", "", text, flags=re.S)
    text = re.sub(r"(?<!\$)\$(?!\$).*?(?<!\\)\$", "", text, flags=re.S)
    return text


def strip_commands(text):
    text = re.sub(r"\\begin\{[^}]+\}", "", text)
    text = re.sub(r"\\end\{[^}]+\}", "", text)
    cmd_group = "|".join(COMMANDS_STRIP_ARGS)
    text = re.sub(
        r"\\(%s)\*?(?:\[[^\]]*\])?(?:\{[^}]*\})*" % cmd_group,
        "",
        text,
    )
    text = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?", "", text)
    text = text.replace("\\%", "%").replace("\\_", "_").replace("\\&", "&")
    text = re.sub(r"[{}]", "", text)
    return text


def strip_for_count(text):
    text = remove_math(text)
    text = strip_commands(text)
    return text


def compute_text_counts(lines):
    total_counts = {"chinese": 0, "english": 0, "digits": 0, "unknown": 0, "total": 0}
    total_words = 0
    for line in lines:
        cleaned = strip_for_count(line)
        if not cleaned:
            continue
        line_counts = count_chars(cleaned)
        for key in total_counts:
            total_counts[key] += line_counts[key]
        total_words += count_english_words(cleaned)
    return total_counts, total_words


def count_chars(text):
    text = re.sub(r"\s+", "", text)
    counts = {
        "chinese": len(re.findall(r"[\u4e00-\u9fff]", text)),
        "english": len(re.findall(r"[A-Za-z]", text)),
        "digits": len(re.findall(r"[0-9]", text)),
        "unknown": len(re.findall(r"[^\s\u4e00-\u9fffA-Za-z0-9]", text)),
    }
    counts["total"] = sum(counts.values())
    return counts


def count_english_words(text):
    words = re.findall(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b", text)
    return len(words)


def count_formulas(text):
    text = strip_comments(text)
    env_count = 0
    for env in MATH_ENVS:
        env_count += len(re.findall(r"\\begin\{%s\}" % re.escape(env), text))

    display_count = len(re.findall(r"\$\$.*?\$\$", text, flags=re.S))
    bracket_count = len(re.findall(r"\\\[(.*?)\\\]", text, flags=re.S))
    paren_count = len(re.findall(r"\\\((.*?)\\\)", text, flags=re.S))

    tmp = re.sub(r"\$\$.*?\$\$", "", text, flags=re.S)
    inline_count = len(re.findall(r"(?<!\$)\$(?!\$).*?(?<!\\)\$", tmp, flags=re.S))

    total = env_count + display_count + bracket_count + paren_count + inline_count
    return {
        "total": total,
        "env": env_count,
        "display": display_count,
        "bracket": bracket_count,
        "paren": paren_count,
        "inline": inline_count,
    }


def count_code_blocks(text):
    lstlisting = len(re.findall(r"\\begin\{lstlisting\}", text))
    verbatim = len(re.findall(r"\\begin\{verbatim\}", text))
    lstinput = len(re.findall(r"\\lstinputlisting(?:\[[^\]]*\])?\{[^}]+\}", text))
    total = lstlisting + verbatim + lstinput
    return {
        "total": total,
        "lstlisting": lstlisting,
        "verbatim": verbatim,
        "lstinput": lstinput,
    }


def count_cites(text):
    return len(re.findall(r"\\cite[a-zA-Z]*\s*\{[^}]+\}", text))


def count_refs(text):
    return len(re.findall(r"\\ref\s*\{[^}]+\}", text))


def find_bib_files(text, base_dir):
    files = []
    for match in re.findall(r"\\bibliography\{([^}]+)\}", text):
        parts = [p.strip() for p in match.split(",") if p.strip()]
        for part in parts:
            name = part
            if not name.lower().endswith(".bib"):
                name += ".bib"
            files.append(os.path.normpath(os.path.join(base_dir, name)))

    for match in re.findall(r"\\addbibresource\{([^}]+)\}", text):
        name = match.strip()
        if name:
            files.append(os.path.normpath(os.path.join(base_dir, name)))
    return files


def count_bib_entries(files):
    total = 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        except OSError:
            continue
        total += len(re.findall(r"^@\w+\s*\{", data, flags=re.M))
    return total


def parse_graphicspaths(text, base_dir):
    paths = []
    match = re.search(r"\\graphicspath\{([^}]*)\}", text)
    if not match:
        return paths
    for inner in re.findall(r"\{([^}]*)\}", match.group(1)):
        if not inner:
            continue
        paths.append(os.path.normpath(os.path.join(base_dir, inner)))
    return paths


def resolve_image(path, base_dirs):
    path = path.strip().strip('"').strip("'")
    path = path.replace("/", os.sep)
    root, ext = os.path.splitext(path)
    exts = [ext] if ext else [".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg"]
    for base in base_dirs:
        for e in exts:
            candidate = os.path.normpath(os.path.join(base, root + e))
            if os.path.isfile(candidate):
                return candidate
    return None


def find_images(text, base_dirs):
    include_re = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    images = []
    for path in include_re.findall(text):
        resolved = resolve_image(path, base_dirs)
        if resolved:
            images.append(resolved)
        else:
            images.append(path)
    return images


def compute_section_stats(lines):
    section_re = re.compile(
        r"\\(section|subsection|subsubsection|paragraph|subparagraph)\*?\{([^}]*)\}"
    )
    counts = defaultdict(int)
    text_counts = defaultdict(int)
    stack = []

    for line in lines:
        matches = list(section_re.finditer(line))
        if matches:
            for match in matches:
                level_name = match.group(1)
                level = SECTION_LEVELS[level_name]
                counts[level] += 1
                stack = [lvl for lvl in stack if lvl < level]
                stack.append(level)

        cleaned = strip_for_count(line)
        cleaned = re.sub(r"\s+", "", cleaned)
        if cleaned and stack:
            for lvl in stack:
                text_counts[lvl] += len(cleaned)

    return counts, text_counts


def compute_section_breakdowns(lines):
    section_re = re.compile(
        r"\\(section|subsection|subsubsection|paragraph|subparagraph)\*?\{([^}]*)\}"
    )
    entries = []
    stack = []

    def new_entry(level, title):
        entry = {
            "level": level,
            "title": title,
            "counts": {"chinese": 0, "english": 0, "digits": 0, "unknown": 0, "total": 0},
            "english_words": 0,
        }
        entries.append(entry)
        return entry

    for line in lines:
        matches = list(section_re.finditer(line))
        if matches:
            for match in matches:
                level_name = match.group(1)
                level = SECTION_LEVELS[level_name]
                title = strip_for_count(match.group(2)).strip()
                stack = [entry for entry in stack if entry["level"] < level]
                stack.append(new_entry(level, title))

        cleaned = strip_for_count(line)
        if cleaned and stack:
            line_counts = count_chars(cleaned)
            line_words = count_english_words(cleaned)
            for entry in stack:
                for key in ("chinese", "english", "digits", "unknown", "total"):
                    entry["counts"][key] += line_counts[key]
                entry["english_words"] += line_words

    return entries


def find_title(text, lines):
    title_match = re.search(r"\\title\{([^}]*)\}", text)
    if title_match:
        return strip_for_count(title_match.group(1)).strip()

    titlepage = re.search(r"\\begin\{titlepage\}(.*?)\\end\{titlepage\}", text, re.S)
    if titlepage:
        candidates = []
        for raw in titlepage.group(1).splitlines():
            cleaned = strip_for_count(raw).strip()
            if cleaned:
                chinese_count = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
                candidates.append((chinese_count, len(cleaned), cleaned))
        if candidates:
            candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
            return candidates[0][2]

    section_re = re.compile(r"\\section\*?\{([^}]*)\}")
    for line in lines:
        match = section_re.search(line)
        if match:
            return strip_for_count(match.group(1)).strip()
    return "unknown"


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def main():
    parser = argparse.ArgumentParser(description="Generate a LaTeX document info report.")
    parser.add_argument("--main", required=True, help="Main .tex file path")
    parser.add_argument("--out", required=True, help="Output report file path")
    parser.add_argument(
        "--out-sections",
        required=False,
        default="",
        help="Output per-section report file path",
    )
    args = parser.parse_args()

    main_path = os.path.normpath(args.main)
    if not os.path.isabs(main_path):
        main_path = os.path.normpath(os.path.join(os.getcwd(), main_path))
    if not os.path.isfile(main_path):
        print(f"[report] Main file not found: {main_path}", file=sys.stderr)
        return 2

    report_root = os.getcwd()
    main_dir = os.path.dirname(main_path)
    main_text = read_text(main_path)
    graphic_paths = parse_graphicspaths(main_text, main_dir)
    base_dirs = [main_dir] + graphic_paths

    lines = expand_file(main_path, set())
    full_text = "\n".join(lines)
    counted_files = collect_tex_files(main_path, set())

    title = find_title(full_text, lines)

    counts, english_words = compute_text_counts(lines)

    formula = count_formulas(full_text)
    code_blocks = count_code_blocks(full_text)
    cite_count = count_cites(full_text)
    ref_count = count_refs(full_text)
    bib_files = find_bib_files(full_text, main_dir)
    bib_entries = count_bib_entries(bib_files)

    images = find_images(full_text, base_dirs)
    image_sizes = []
    total_image_size = 0
    for img in images:
        if os.path.isfile(img):
            size = os.path.getsize(img)
            total_image_size += size
            image_sizes.append((img, size))
        else:
            image_sizes.append((img, None))

    section_counts, section_text = compute_section_stats(lines)
    section_breakdowns = compute_section_breakdowns(lines)

    out_path = os.path.normpath(args.out)
    sections_out_path = os.path.normpath(args.out_sections) if args.out_sections else ""
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    if sections_out_path:
        sections_dir = os.path.dirname(sections_out_path)
        if sections_dir and not os.path.isdir(sections_dir):
            os.makedirs(sections_dir, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("Document Info Report\n")
        f.write("====================\n\n")
        f.write(f"Main file: {os.path.relpath(main_path, report_root)}\n")
        f.write(f"Title: {title}\n\n")
        f.write(
            "Note: Statistics are derived from source text heuristics (e.g. stripping TeX "
            "commands and math), not from the compiled PDF.\n\n"
        )
        f.write("Counted files:\n")
        for path in counted_files:
            f.write(f"  - {os.path.relpath(path, report_root)}\n")
        f.write("\n")

        f.write("Character counts (stripped of TeX and math):\n")
        f.write(f"  Chinese: {counts['chinese']}\n")
        f.write(f"  English: {counts['english']}\n")
        f.write(f"  English words: {english_words}\n")
        f.write(f"  Digits:  {counts['digits']}\n")
        f.write(f"  Unknown: {counts['unknown']}\n")
        f.write(f"  Total:   {counts['total']}\n\n")

        f.write("Formula counts:\n")
        f.write(f"  Total:   {formula['total']}\n")
        f.write(f"  Env:     {formula['env']}\n")
        f.write(f"  $$:      {formula['display']}\n")
        f.write(f"  \\[\\]:    {formula['bracket']}\n")
        f.write(f"  \\(\\):    {formula['paren']}\n")
        f.write(f"  Inline $: {formula['inline']}\n\n")

        f.write("Code blocks:\n")
        f.write(f"  Total:     {code_blocks['total']}\n")
        f.write(f"  lstlisting:{code_blocks['lstlisting']}\n")
        f.write(f"  verbatim:  {code_blocks['verbatim']}\n")
        f.write(f"  lstinput:  {code_blocks['lstinput']}\n")
        f.write("\n")

        f.write("References:\n")
        f.write(f"  Cite commands: {cite_count}\n")
        f.write(f"  Ref commands:  {ref_count}\n")
        f.write(f"  Bib entries:   {bib_entries}\n\n")

        f.write("Section levels:\n")
        for name, level in SECTION_LEVELS.items():
            f.write(f"  {name}: {section_counts.get(level, 0)}\n")
        f.write("\n")

        f.write("Images:\n")
        f.write(f"  Count: {len(images)}\n")
        f.write(f"  Total size: {format_size(total_image_size)}\n")
        for img, size in image_sizes:
            if size is None:
                f.write(f"  - {img} (missing)\n")
            else:
                f.write(f"  - {os.path.relpath(img, report_root)} ({format_size(size)})\n")

    if sections_out_path:
        with open(sections_out_path, "w", encoding="utf-8") as f:
            f.write("Per-section Character Counts\n")
            f.write("============================\n\n")
            f.write(
                "Note: Statistics are derived from source text heuristics (e.g. stripping TeX "
                "commands and math), not from the compiled PDF.\n\n"
            )
            f.write(f"Main file: {os.path.relpath(main_path, report_root)}\n")
            f.write(f"Title: {title}\n\n")
            f.write("Per-section character counts (inclusive of sublevels):\n")
            for entry in section_breakdowns:
                level_name = next(
                    (name for name, lvl in SECTION_LEVELS.items() if lvl == entry["level"]),
                    f"level{entry['level']}",
                )
                title = entry["title"] or "untitled"
                c = entry["counts"]
                indent = "\t" * max(entry["level"] - 1, 0)
                f.write(f"{indent}[{level_name}] {title}\n")
                f.write(f"{indent}\tChinese: {c['chinese']}\n")
                f.write(f"{indent}\tEnglish: {c['english']}\n")
                f.write(f"{indent}\tEnglish words: {entry['english_words']}\n")
                f.write(f"{indent}\tDigits:  {c['digits']}\n")
                f.write(f"{indent}\tUnknown: {c['unknown']}\n")
                f.write(f"{indent}\tTotal:   {c['total']}\n")

    print(f"[report] {out_path}")
    if sections_out_path:
        print(f"[report] {sections_out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
