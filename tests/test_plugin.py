"""Offline checks for the plugin files.

Run from the repository root: python -m unittest discover -s tests -v
Requirements in the Antigravity spec: https://antigravity.google/docs/build-plugins
"""

import json
import re
import struct
import subprocess
import unittest
import zlib
from pathlib import Path

import yaml  # installed from tests/requirements.txt

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SERVER_URL = "https://mcp.octen.ai/mcp"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
STABLE_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
FORBIDDEN_PREFIXES = ("Antigravity", "Gemini", "Claude", "Cursor")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def hosted_tools():
    return load_json(FIXTURES / "hosted-tools.json")["tools"]


def frontmatter(path):
    """Parse the YAML header of a SKILL.md; malformed YAML raises."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise AssertionError(f"{path}: no YAML frontmatter")
    fields = yaml.safe_load(match.group(1))
    if not isinstance(fields, dict):
        raise AssertionError(f"{path}: frontmatter is not a mapping")
    return fields


def table_tools(markdown, heading_cell, column):
    """Backticked names in one column of the table whose header row starts with `heading_cell`."""
    names, in_table = [], False
    for line in markdown.splitlines():
        if line.startswith("| " + heading_cell):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                break
            cell = line.split("|")[column + 1]
            names += re.findall(r"`([^`]+)`", cell)
    return names


def png_info(path):
    """Decode a non-interlaced 8-bit RGB or RGBA PNG, the formats this repository uses; anything else fails."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path}: not a PNG")
    pos, header, idat, ended = 8, None, b"", False
    if data[12:16] != b"IHDR":
        raise AssertionError(f"{path}: IHDR must be the first chunk")
    while pos < len(data):
        if pos + 8 > len(data):
            raise AssertionError(f"{path}: truncated chunk header")
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body, crc = data[pos + 8:pos + 8 + length], data[pos + 8 + length:pos + 12 + length]
        if len(body) != length or len(crc) != 4 or zlib.crc32(kind + body) & 0xFFFFFFFF != struct.unpack(">I", crc)[0]:
            raise AssertionError(f"{path}: corrupt {kind!r} chunk")
        if kind == b"IHDR":
            if header is not None:
                raise AssertionError(f"{path}: more than one IHDR chunk")
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            ended = True
            break
        pos += 12 + length
    if header is None or not ended or not idat:
        raise AssertionError(f"{path}: missing IHDR, IDAT or IEND")
    width, height, depth, color_type, compression, filter_method, interlace = header
    channels = {6: 4, 2: 3}.get(color_type)
    if depth != 8 or channels is None or (compression, filter_method, interlace) != (0, 0, 0):
        raise AssertionError(f"{path}: expected a non-interlaced 8-bit RGB or RGBA PNG")
    pixels, stride = zlib.decompress(idat), 1 + width * channels
    if len(pixels) != height * stride:
        raise AssertionError(f"{path}: pixel data does not match the image size")
    rows, previous = [], bytearray(stride - 1)
    for row in range(height):
        kind, line = pixels[row * stride], bytearray(pixels[row * stride + 1:(row + 1) * stride])
        if kind > 4:
            raise AssertionError(f"{path}: invalid scanline filter type")
        for i in range(len(line)):
            left = line[i - channels] if i >= channels else 0
            up, upper_left = previous[i], previous[i - channels] if i >= channels else 0
            if kind == 1:
                line[i] = (line[i] + left) & 0xFF
            elif kind == 2:
                line[i] = (line[i] + up) & 0xFF
            elif kind == 3:
                line[i] = (line[i] + ((left + up) >> 1)) & 0xFF
            elif kind == 4:
                guess = left + up - upper_left
                pa, pb, pc = abs(guess - left), abs(guess - up), abs(guess - upper_left)
                line[i] = (line[i] + (left if pa <= pb and pa <= pc else up if pb <= pc else upper_left)) & 0xFF
        rows.append(line)
        previous = line
    return width, height, color_type, rows


def transparent_margin(width, height, rows):
    """Fraction of the image width and height, from each edge, that is fully transparent."""
    opaque = [(x, y) for y, row in enumerate(rows) for x in range(width) if row[x * 4 + 3] != 0]
    if not opaque:
        return 0.0
    xs, ys = [x for x, _ in opaque], [y for _, y in opaque]
    return min(min(xs), width - 1 - max(xs)) / width, min(min(ys), height - 1 - max(ys)) / height


class PluginManifest(unittest.TestCase):
    def setUp(self):
        self.manifest = load_json(ROOT / "plugin.json")

    def test_matches_official_schema(self):
        import jsonschema  # installed from tests/requirements.txt

        jsonschema.validate(self.manifest, load_json(FIXTURES / "plugin.schema.json"))

    def test_has_every_field_the_marketplace_requires(self):
        for field in ("name", "displayName", "description", "version", "logo", "suggestedPrompts", "author"):
            self.assertTrue(self.manifest.get(field), f"plugin.json is missing {field}")

    def test_name_and_display_name(self):
        self.assertRegex(self.manifest["name"], KEBAB)
        display = self.manifest["displayName"]
        self.assertFalse(display.startswith(FORBIDDEN_PREFIXES), display)
        self.assertFalse(re.search(r"\b(Plugin|MCP)$", display), display)

    def test_description_length_is_in_the_recommended_range(self):
        # The spec recommends 120 to 160 characters; this repository holds itself to it for the Marketplace card.
        self.assertTrue(120 <= len(self.manifest["description"]) <= 160, len(self.manifest["description"]))

    def test_at_most_three_suggested_prompts(self):
        prompts = self.manifest["suggestedPrompts"]
        self.assertTrue(1 <= len(prompts) <= 3, prompts)
        self.assertTrue(all(isinstance(p, str) and p.strip() for p in prompts))

    def test_version_is_a_stable_semver_release(self):
        self.assertIsNotNone(STABLE_VERSION.fullmatch(self.manifest["version"]), self.manifest["version"])

    def test_urls_use_https(self):
        author = self.manifest["author"]
        urls = [author.get("url")] if isinstance(author, dict) else []
        urls += [self.manifest.get("homepage"), self.manifest.get("repository")]
        for url in filter(None, urls):
            self.assertTrue(url.startswith("https://"), url)

    def test_logo_is_a_square_png_of_at_least_128px_with_transparent_padding(self):
        logo = ROOT / self.manifest["logo"]
        self.assertTrue(logo.is_file(), logo)
        width, height, color_type, rows = png_info(logo)
        self.assertEqual(width, height, "logo must be 1:1")
        self.assertGreaterEqual(width, 128)
        self.assertEqual(color_type, 6, "logo needs an alpha channel for the transparent padding")
        # The spec asks for about 10% transparent padding; under 5% on any edge is treated as missing.
        horizontal, vertical = transparent_margin(width, height, rows)
        self.assertGreaterEqual(min(horizontal, vertical), 0.05)


class McpConfig(unittest.TestCase):
    def setUp(self):
        self.servers = load_json(ROOT / "mcp_config.json")["mcpServers"]

    def test_bundles_only_the_hosted_octen_server(self):
        self.assertEqual(list(self.servers), ["octen"])
        self.assertEqual(self.servers["octen"].get("url"), SERVER_URL)

    def test_signs_in_with_oauth_and_carries_no_credentials(self):
        # Any header, variable or client secret here would ask users for a key again.
        self.assertEqual(set(self.servers["octen"]), {"url"})


class Skills(unittest.TestCase):
    def setUp(self):
        self.skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))

    def test_there_is_at_least_one_skill(self):
        self.assertTrue(self.skill_files)

    def test_frontmatter_follows_the_spec(self):
        for path in self.skill_files:
            fields = frontmatter(path)
            with self.subTest(skill=path.parent.name):
                self.assertIsInstance(fields.get("name"), str)
                self.assertIsInstance(fields.get("description"), str)
                self.assertEqual(fields["name"], path.parent.name)
                self.assertRegex(fields["name"], KEBAB)
                self.assertTrue(1 <= len(fields["name"]) <= 64)
                self.assertTrue(1 <= len(fields["description"]) <= 1024)

    def test_guide_lists_every_hosted_tool_once(self):
        guide = (ROOT / "skills/octen-search-guide/SKILL.md").read_text(encoding="utf-8")
        listed = table_tools(guide, "The task needs", column=1)
        self.assertCountEqual(listed, hosted_tools())

    def test_guide_names_no_unknown_tool(self):
        guide = (ROOT / "skills/octen-search-guide/SKILL.md").read_text(encoding="utf-8")
        named = set(re.findall(r"`((?:[a-z0-9]+_)*search|extract)`", guide))
        parameters = {"web_search"}  # an option object of design_search and place_search, not a tool
        self.assertLessEqual(named - parameters, set(hosted_tools()))
        # Bullets in the comparison and tool-note sections open with tool names: "- `a` or `b`:" and "- `a`:".
        openers = re.findall(r"^- `([a-z_]+)`(?: or `([a-z_]+)`)?:", guide, re.M)
        self.assertTrue(openers)
        self.assertLessEqual({name for pair in openers for name in pair if name}, set(hosted_tools()))


class Readme(unittest.TestCase):
    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_tool_table_lists_every_hosted_tool_once(self):
        self.assertCountEqual(table_tools(self.readme, "Tool", column=0), hosted_tools())

    def test_relative_links_and_anchors_resolve(self):
        def anchors(markdown):
            prose = re.sub(r"^```.*?^```", "", markdown, flags=re.S | re.M)  # headings only outside code fences
            headings = re.findall(r"^#+ (.+)$", prose, re.M)
            return {re.sub(r"[^a-z0-9 -]", "", h.lower()).strip().replace(" ", "-") for h in headings}

        inline = re.findall(r"\]\(([^)\s]+)\)", self.readme)
        definitions = re.findall(r"^\s*\[[^\]]+\]:\s*(\S+)", self.readme, re.M)  # reference-style links
        for target in inline + definitions:
            if target.startswith(("https://", "http://", "mailto:")):
                continue
            path, _, fragment = target.partition("#")
            with self.subTest(link=target):
                linked = ROOT / path if path else ROOT / "README.md"
                self.assertTrue(linked.exists())
                if fragment:
                    self.assertIn(fragment, anchors(linked.read_text(encoding="utf-8")))

    def test_install_command_points_at_the_repository(self):
        # Assumes the command appears unquoted in a fenced block, as it does today.
        repository = load_json(ROOT / "plugin.json")["repository"]
        targets = re.findall(r"agy plugin install (\S+)", self.readme)
        self.assertTrue(targets)
        self.assertEqual(set(targets), {repository})


class Repository(unittest.TestCase):
    def tracked_text_files(self):
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
        for name in filter(None, out.decode("utf-8").split("\0")):
            path = ROOT / name
            if path.is_file() and b"\0" not in path.read_bytes()[:8192]:  # skip binary files such as the logo
                yield path

    def test_text_has_no_cjk_characters(self):
        ranges = ((0x3040, 0x30FF), (0x3400, 0x9FFF), (0xAC00, 0xD7AF))  # kana, CJK ideographs, hangul
        cjk = re.compile("[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in ranges) + "]")
        for path in self.tracked_text_files():
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertIsNone(cjk.search(str(path.relative_to(ROOT))))
                self.assertIsNone(cjk.search(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
