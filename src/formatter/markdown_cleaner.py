import re
from dataclasses import dataclass


@dataclass(slots=True)
class MarkdownCleanOptions:
    fix_headings: bool = True
    fix_lists: bool = True
    merge_paragraphs: bool = True
    remove_noise: bool = True
    normalize_punctuation: bool = True
    preserve_tables: bool = True


class MarkdownCleaner:
    def clean(self, markdown: str, options: MarkdownCleanOptions | None = None) -> str:
        return self.clean_with_report(markdown, options)["markdown"]

    def clean_with_report(self, markdown: str, options: MarkdownCleanOptions | None = None) -> dict:
        opts = options or MarkdownCleanOptions()
        original = markdown or ""
        text = self._normalize_line_breaks(original)
        stats = {
            "source_chars": len(original),
            "source_lines": len(text.split("\n")) if text else 0,
            "noise_removed": 0,
            "paragraphs_merged": 0,
            "symbol_only_lines_removed": 0,
            "heading_fixed": 0,
            "list_fixed": 0,
            "punctuation_fixed": 0,
            "blank_lines_reduced": 0,
        }

        blocks = self._split_blocks(text)
        cleaned_blocks = []
        for block_type, block_text in blocks:
            if block_type in {"code", "table"}:
                cleaned_blocks.append((block_type, block_text))
                continue
            cleaned_text, block_stats = self._clean_text_block(block_text, opts)
            cleaned_blocks.append((block_type, cleaned_text))
            for key, value in block_stats.items():
                stats[key] = stats.get(key, 0) + value

        text = "\n".join(block_text for _, block_text in cleaned_blocks)
        text, blank_reduced = self._remove_excessive_blank_lines(text)
        stats["blank_lines_reduced"] += blank_reduced
        text = self._fix_code_blocks(text)
        text = text.strip()
        if text:
            text += "\n"

        stats["result_chars"] = len(text)
        stats["result_lines"] = len(text.split("\n")) if text else 0
        stats["changed"] = text != (original.strip() + ("\n" if original.strip() else ""))
        stats["char_delta"] = stats["result_chars"] - stats["source_chars"]
        return {"markdown": text, "stats": stats}

    def _split_blocks(self, text: str) -> list[tuple[str, str]]:
        lines = text.split("\n")
        blocks: list[tuple[str, str]] = []
        buffer: list[str] = []
        in_code = False

        def flush_buffer() -> None:
            if buffer:
                blocks.append(("text", "\n".join(buffer)))
                buffer.clear()

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code:
                    buffer.append(line)
                    blocks.append(("code", "\n".join(buffer)))
                    buffer.clear()
                    in_code = False
                else:
                    flush_buffer()
                    buffer.append(line)
                    in_code = True
                continue

            if in_code:
                buffer.append(line)
                continue

            if "|" in line and stripped:
                flush_buffer()
                blocks.append(("table", line))
                continue

            buffer.append(line)

        if buffer:
            blocks.append(("code" if in_code else "text", "\n".join(buffer)))
        return blocks

    def _clean_text_block(self, text: str, options: MarkdownCleanOptions) -> tuple[str, dict]:
        stats = {
            "noise_removed": 0,
            "paragraphs_merged": 0,
            "symbol_only_lines_removed": 0,
            "heading_fixed": 0,
            "list_fixed": 0,
            "punctuation_fixed": 0,
        }
        lines = text.split("\n")
        cleaned_lines: list[str] = []

        for raw_line in lines:
            line = raw_line.rstrip()
            if not line.strip():
                cleaned_lines.append("")
                continue

            if self._is_symbol_only_line(line):
                stats["symbol_only_lines_removed"] += 1
                continue

            if options.remove_noise:
                line, removed = self._remove_noise_tokens(line)
                stats["noise_removed"] += removed

            if options.fix_headings:
                line, fixed = self._fix_heading_spacing(line)
                stats["heading_fixed"] += fixed

            if options.fix_lists:
                line, fixed = self._fix_list_spacing(line)
                stats["list_fixed"] += fixed

            if options.normalize_punctuation:
                line, fixed = self._normalize_punctuation(line)
                stats["punctuation_fixed"] += fixed

            cleaned_lines.append(line.rstrip())

        if options.merge_paragraphs:
            merged_lines, merged_count = self._merge_paragraph_lines(cleaned_lines)
            cleaned_lines = merged_lines
            stats["paragraphs_merged"] += merged_count

        return "\n".join(cleaned_lines), stats

    def _normalize_line_breaks(self, text: str) -> str:
        return (text or "").replace("\r\n", "\n").replace("\r", "\n")

    def _fix_heading_spacing(self, line: str) -> tuple[str, int]:
        if re.match(r"^#{1,6}(?!\s)", line):
            return re.sub(r"^(#{1,6})(\S)", r"\1 \2", line, count=1), 1
        return line, 0

    def _fix_list_spacing(self, line: str) -> tuple[str, int]:
        fixed = 0
        new_line = line
        if re.match(r"^[-*+](?!\s)", new_line):
            new_line = re.sub(r"^([-*+])(\S)", r"\1 \2", new_line, count=1)
            fixed += 1
        if re.match(r"^\d+[.)](?!\s)", new_line):
            new_line = re.sub(r"^(\d+[.)])(\S)", r"\1 \2", new_line, count=1)
            fixed += 1
        return new_line, fixed

    def _remove_excessive_blank_lines(self, text: str) -> tuple[str, int]:
        reduced = 0

        def repl(match: re.Match[str]) -> str:
            nonlocal reduced
            reduced += max(0, len(match.group(0)) - 3)
            return "\n\n\n"

        return re.sub(r"\n{4,}", repl, text), reduced

    def _fix_code_blocks(self, text: str) -> str:
        return re.sub(r"(?<!`)```(?!`)", "```", text)

    def _remove_noise_tokens(self, line: str) -> tuple[str, int]:
        patterns = [
            r"(?<!\w)(?:--|—{2,}|_{2,}|={2,}|&&|\*{2,})(?!\w)",
            r"[·•]{3,}",
        ]
        removed = 0
        new_line = line
        for pattern in patterns:
            matches = re.findall(pattern, new_line)
            if matches:
                removed += len(matches)
                new_line = re.sub(pattern, " ", new_line)
        new_line = re.sub(r"\s{2,}", " ", new_line).strip()
        return new_line, removed

    def _normalize_punctuation(self, line: str) -> tuple[str, int]:
        original = line
        line = re.sub(r"\s+([，。！？；：、）】》」』])", r"\1", line)
        line = re.sub(r"([（【《「『])\s+", r"\1", line)
        line = re.sub(r"([A-Za-z0-9])([，。！？；：])", r"\1\2", line)
        line = re.sub(r"([，。！？；：、])([A-Za-z0-9\u4e00-\u9fff])", r"\1 \2", line)
        line = re.sub(r"\s{2,}", " ", line)
        line = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[，。！？；：、])", "", line)
        return line.strip(), int(line.strip() != original.strip())

    def _merge_paragraph_lines(self, lines: list[str]) -> tuple[list[str], int]:
        merged: list[str] = []
        merge_count = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                merged.append("")
                continue

            if not merged:
                merged.append(stripped)
                continue

            previous = merged[-1].rstrip()
            if (
                previous
                and self._should_merge(previous, stripped)
            ):
                joiner = "" if self._needs_tight_join(previous, stripped) else " "
                merged[-1] = previous + joiner + stripped
                merge_count += 1
            else:
                merged.append(stripped)

        return merged, merge_count

    def _should_merge(self, previous: str, current: str) -> bool:
        if not previous or not current:
            return False
        if previous.startswith(("```", "#", ">", "-", "*", "+")):
            return False
        if current.startswith(("```", "#", ">", "-", "*", "+")):
            return False
        if re.match(r"^\d+[.)]\s", current):
            return False
        if "|" in previous or "|" in current:
            return False
        if previous.endswith(("：", ":")):
            return False
        if self._looks_like_title(previous) or self._looks_like_title(current):
            return False
        return not previous.endswith(("。", "！", "？", ".", "!", "?", "；", ";"))

    def _needs_tight_join(self, previous: str, current: str) -> bool:
        return bool(
            re.search(r"[\u4e00-\u9fff]$", previous)
            and re.match(r"^[\u4e00-\u9fff]", current)
        )

    def _is_symbol_only_line(self, line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        if re.fullmatch(r"[\W_·•—\-*=#|&~`]{2,}", stripped):
            return True
        return False

    def _looks_like_title(self, line: str) -> bool:
        stripped = line.strip()
        if len(stripped) <= 24 and not re.search(r"[，。！？；：,.!?;:]", stripped):
            return bool(re.search(r"[\u4e00-\u9fffA-Za-z]", stripped))
        return False
