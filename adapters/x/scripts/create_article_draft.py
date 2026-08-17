#!/usr/bin/env python3
"""Create an X Article draft from HTML and local images.

This script deliberately stops at a saved draft. Publishing remains an explicit
human action in the X editor. It uses the Playwright MCP stdio interface and
has no access to credentials; authentication comes from the browser profile.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_PROFILE = os.environ.get("X_ARTICLE_PROFILE_DIR", "~/.x-article-profile")
DEFAULT_MCP = os.environ.get("PLAYWRIGHT_MCP_BIN", "playwright-mcp")


class MCPClient:
    """Minimal JSON-RPC client for Playwright MCP over stdio."""

    def __init__(self, mcp_bin: str, profile_dir: Path) -> None:
        command = shutil.which(mcp_bin) or mcp_bin
        self.proc = subprocess.Popen(
            [command, "--browser", "chromium", "--user-data-dir", str(profile_dir)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._id = 0
        self.call(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "article-style-system", "version": "1.0"},
            },
        )
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, message: dict[str, Any]) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("Playwright MCP stdin is unavailable")
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._id += 1
        request_id = self._id
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        if self.proc.stdout is None:
            raise RuntimeError("Playwright MCP stdout is unavailable")
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("Playwright MCP closed unexpectedly")
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                continue
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise RuntimeError(str(response["error"]))
            return response.get("result", {})

    def tool(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        result = self.call(
            "tools/call",
            {"name": name, "arguments": arguments or {}},
        )
        return "\n".join(
            item.get("text", "")
            for item in result.get("content", [])
            if item.get("type") == "text"
        )

    def close(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def js_string(value: str) -> str:
    """Return a JSON-quoted JavaScript string literal."""
    return json.dumps(value, ensure_ascii=False)


def copy_html_to_clipboard(html: str) -> None:
    """Copy HTML and a tag-stripped fallback to the macOS pasteboard."""
    if sys.platform != "darwin":
        raise RuntimeError(
            "Rich-text clipboard injection currently supports macOS only; "
            "use the X editor manually on other platforms."
        )
    try:
        import importlib

        appkit = importlib.import_module("AppKit")
        foundation = importlib.import_module("Foundation")
        NSPasteboard = appkit.NSPasteboard
        NSPasteboardTypeHTML = appkit.NSPasteboardTypeHTML
        NSPasteboardTypeString = appkit.NSPasteboardTypeString
        NSData = foundation.NSData
    except ImportError as exc:
        raise RuntimeError(
            "Install pyobjc-framework-Cocoa in the Python environment used to run "
            "this script."
        ) from exc

    pasteboard = NSPasteboard.generalPasteboard()
    pasteboard.clearContents()
    encoded = html.encode("utf-8")
    data = NSData.dataWithBytes_length_(encoded, len(encoded))
    pasteboard.setData_forType_(data, NSPasteboardTypeHTML)
    plain = re.sub(r"<[^>]+>", "\n", html)
    plain = html_lib.unescape(re.sub(r"\n{3,}", "\n\n", plain)).strip()
    pasteboard.setString_forType_(plain, NSPasteboardTypeString)


def parse_image_specs(values: list[str]) -> list[tuple[str, Path]]:
    specs: list[tuple[str, Path]] = []
    for value in values:
        anchor, separator, path = value.partition("=")
        if not separator or not anchor or not path:
            raise ValueError(
                f"Invalid --image value {value!r}; use ANCHOR=/absolute/path/image.png"
            )
        specs.append((anchor, Path(path).expanduser().resolve()))
    return specs


def ensure_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")


def body_stats(client: MCPClient) -> dict[str, int]:
    function = """() => {
      const b = document.querySelector('[data-testid="composer"]');
      if (!b) return JSON.stringify({error: 'composer not found'});
      const blocks = Array.from(b.querySelectorAll('[data-block=true]'));
      return JSON.stringify({
        chars: b.innerText.length,
        blocks: blocks.length,
        headings: blocks.filter(x => x.className.includes('header-two')).length
      });
    }"""
    raw = client.tool("browser_evaluate", {"function": function})
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise RuntimeError(f"Could not parse body stats: {raw[:300]}")
    stats = json.loads(match.group(0))
    if "error" in stats:
        raise RuntimeError(stats["error"])
    return stats


def upload_image(client: MCPClient, anchor: str, image_path: Path) -> bool:
    """Insert one image after a unique text anchor; return False on any positioning failure."""
    clear = """() => {
      document.querySelectorAll('[data-anchor]').forEach(x => x.removeAttribute('data-anchor'));
      return 'CLEARED';
    }"""
    client.tool("browser_evaluate", {"function": clear})

    anchor_literal = js_string(anchor)
    tag = f"""() => {{
      const b = document.querySelector('[data-testid="composer"]');
      if (!b) return 'NO_COMPOSER';
      const blocks = Array.from(b.querySelectorAll('[data-block=true]'));
      const target = blocks.find(x => (x.innerText || '').includes({anchor_literal}));
      if (!target) return 'ANCHOR_NOT_FOUND';
      target.setAttribute('data-anchor', 'yes');
      target.scrollIntoView({{block: 'center'}});
      return 'TAGGED';
    }}"""
    result = client.tool("browser_evaluate", {"function": tag})
    if "TAGGED" not in result:
        print(f"skip image {image_path.name}: {result[:120]}", file=sys.stderr)
        return False

    try:
        client.tool("browser_click", {"target": "[data-anchor='yes']"})
    except Exception as exc:
        print(f"skip image {image_path.name}: anchor click failed: {exc}", file=sys.stderr)
        return False
    time.sleep(0.5)

    open_media = """() => {
      const buttons = Array.from(document.querySelectorAll('button[aria-label="Add Media"]'));
      if (!buttons.length) return 'NO_ADD_MEDIA';
      buttons[0].click();
      return 'OPENED';
    }"""
    if "OPENED" not in client.tool("browser_evaluate", {"function": open_media}):
        return False
    time.sleep(0.8)

    choose_media = """() => {
      const items = Array.from(document.querySelectorAll('[role=menuitem]'));
      const media = items.find(x => x.textContent.trim() === 'Media');
      if (!media) return 'NO_MEDIA_ITEM';
      media.click();
      return 'OPENED';
    }"""
    if "OPENED" not in client.tool("browser_evaluate", {"function": choose_media}):
        return False
    time.sleep(1)

    mark_upload = """() => {
      const dialog = document.querySelector('[role=dialog]');
      if (!dialog) return 'NO_DIALOG';
      const leaves = dialog.querySelectorAll('*');
      let zone = null;
      for (const element of leaves) {
        if (element.children.length === 0 && element.textContent.includes('Choose a file')) {
          zone = element;
          break;
        }
      }
      if (!zone) return 'NO_UPLOAD_ZONE';
      let target = zone;
      while (target && !target.getAttribute('role') && !target.onclick) {
        target = target.parentElement;
      }
      if (!target) return 'NO_UPLOAD_TARGET';
      target.setAttribute('data-upload-zone', 'yes');
      return 'MARKED';
    }"""
    if "MARKED" not in client.tool("browser_evaluate", {"function": mark_upload}):
        return False
    try:
        client.tool("browser_click", {"target": "[data-upload-zone='yes']"})
        time.sleep(0.5)
        client.tool("browser_file_upload", {"paths": [str(image_path)]})
    except Exception as exc:
        print(f"skip image {image_path.name}: upload failed: {exc}", file=sys.stderr)
        return False
    time.sleep(3)
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a true X Article draft from HTML; never publishes automatically."
    )
    parser.add_argument("--title", required=True, help="Article title")
    parser.add_argument("--cover", required=True, type=Path, help="Cover image path")
    parser.add_argument("--body-html", required=True, type=Path, help="HTML body file")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        metavar="ANCHOR=/PATH/IMAGE",
        help="Insert an image after a unique body-text anchor; repeatable",
    )
    parser.add_argument(
        "--profile-dir",
        type=Path,
        default=Path(DEFAULT_PROFILE).expanduser(),
        help="Persistent Playwright browser profile (or X_ARTICLE_PROFILE_DIR)",
    )
    parser.add_argument(
        "--mcp-bin",
        default=DEFAULT_MCP,
        help="playwright-mcp executable (or PLAYWRIGHT_MCP_BIN)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cover = args.cover.expanduser().resolve()
    body_html = args.body_html.expanduser().resolve()
    ensure_file(cover, "Cover image")
    ensure_file(body_html, "HTML body")
    image_specs = parse_image_specs(args.image)
    for _, image_path in image_specs:
        ensure_file(image_path, "Content image")

    html_body = body_html.read_text(encoding="utf-8")
    copy_html_to_clipboard(html_body)
    client = MCPClient(args.mcp_bin, args.profile_dir)
    try:
        client.tool("browser_navigate", {"url": "https://x.com/compose/articles"})
        time.sleep(2)
        write_js = """() => {
          const write = Array.from(document.querySelectorAll('a'))
            .find(a => a.textContent.trim() === 'Write');
          if (!write) return 'NO_WRITE';
          write.click();
          return 'OPENED';
        }"""
        if "OPENED" not in client.tool("browser_evaluate", {"function": write_js}):
            raise RuntimeError("Could not find the X Articles Write action")
        time.sleep(2)
        client.tool("browser_type", {"target": "textarea[name='Article Title']", "text": args.title})
        client.tool("browser_click", {"target": "button[aria-label='Add photos or video']"})
        time.sleep(0.8)
        client.tool("browser_file_upload", {"paths": [str(cover)]})
        time.sleep(2)
        snapshot = client.tool("browser_snapshot", {})
        if "Apply" in snapshot:
            client.tool("browser_click", {"target": "button:has-text('Apply')"})
            time.sleep(0.8)

        client.tool("browser_click", {"target": "[data-testid='composer']"})
        client.tool("browser_press_key", {"key": "Meta+v"})
        time.sleep(3)
        stats = body_stats(client)
        if stats["blocks"] <= 2:
            raise RuntimeError(
                f"Rich-text paste did not populate the composer: {stats}. "
                "Check the browser profile and clipboard dependencies."
            )
        print(f"body: {stats}")

        inserted = 0
        for anchor, image_path in image_specs:
            if upload_image(client, anchor, image_path):
                inserted += 1
        print(f"images inserted: {inserted}/{len(image_specs)}")

        verify_js = """() => {
          const b = document.querySelector('[data-testid="composer"]');
          const blocks = Array.from(b.querySelectorAll('[data-block=true]'));
          const imageBlocks = [];
          blocks.forEach((x, i) => { if (x.querySelector('img')) imageBlocks.push(i); });
          return JSON.stringify({
            blocks: blocks.length,
            images: b.querySelectorAll('img').length,
            imageBlocks
          });
        }"""
        print("verify:", client.tool("browser_evaluate", {"function": verify_js}))
        print("Draft saved by X. Review it in the editor before publishing.")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
