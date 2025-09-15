from __future__ import annotations

from e3.anod.loader import AnodSpecRepository
from e3.anod.context import AnodContext
from e3.anod.sandbox import SandBox
from e3.os.process import Run

from dataclasses import dataclass
import html.parser
import logging
import requests as req
import sys


def check_tool(tool: str) -> str:
    """Check tool version and return its version.

    The function will force exit if the tool is not found.

    :param tool: tool name
    :type tool: str
    :return: the tool version
    :rtype: str
    """
    try:
        p = Run([tool, "--version"])
        version = p.out.splitlines()[0]
        logging.info("%s version: %s", tool, version)
        return version
    except Exception:
        logging.critical("cannot find %s", tool)
        sys.exit(1)


def create_anod_context(spec_dir: str) -> AnodContext:
    return AnodContext(AnodSpecRepository(spec_dir))


def create_anod_sandbox(sbx_dir: str, spec_dir: str) -> SandBox:
    sbx = SandBox(sbx_dir)
    sbx.specs_dir = spec_dir

    return sbx

@dataclass
class Snapshot:
    tarball: str
    url: str

class GCCSnapshotTarballFinder(html.parser.HTMLParser):
    outer = []
    curr = None
    tarball = None
    branch = ""

    # cache the result at the class level to avoid doing unecessary requests
    __snap: Snapshot | None = None

    def __init__(self, branch: str):
        super().__init__()
        self.branch = branch

    def handle_starttag(self, tag, attrs):
        if self.curr:
            self.outer.append(self.curr)
        self.curr = tag
        if tag == "a" and self.outer == ["html", "body", "table", "tr", "td"]:
            for key, val in attrs:
                if key == "href" and (
                    val.endswith(".tar.xz") or val.endswith(".tar.gz")
                ):
                    self.tarball = val.rstrip('/').rsplit('/', 1)[-1]

    def handle_endtag(self, tag):
        if self.curr == tag:
            self.curr = self.outer.pop() if self.outer else None
    
    @classmethod
    def get(cls, branch: str) -> Snapshot:
        if cls.__snap:
            return cls.__snap
        base_url = "https://gcc.gnu.org/pub/gcc/snapshots/LATEST-%s/" % branch
        page = req.get(base_url)
        parser = cls(branch)
        parser.feed(page.text)
        if parser.tarball:
            cls.__snap = Snapshot(parser.tarball, base_url + parser.tarball)
            return cls.__snap
        else:
            raise Exception("could not find tarball in snapshot page")

