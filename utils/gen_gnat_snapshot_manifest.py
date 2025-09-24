#!/usr/bin/env python3

import json
import os
import subprocess
import time

basever = "16.0.0"
release_name = f"gnat-{basever}-snapshot"

old_rel = subprocess.run(args=["gh", "release", "view", release_name])
new_rel = subprocess.run(args=["gh", "release", "view", f"{release_name}-draft"])

if new_rel.returncode != 0:
    raise Exception("could not find candidate draft release to publish")

if old_rel.returncode == 0:
    subprocess.run(
        args=["gh", "release", "delete", release_name, "-y", "--cleanup-tag"]
    )
    time.sleep(3)  # wait for deletion propagation

subprocess.run(
    args=[
        "gh",
        "release",
        "edit",
        f"{release_name}-draft",
        "--draft=false",
        "--target=snapshots",
        f"--title={release_name}",
        f"--tag={release_name}",
        "--prerelease",
    ]
)

p = subprocess.run(
    args=["gh", "release", "view", f"{release_name}", "--json", "body,assets"],
    capture_output=True,
    check=True,
)
release = json.loads(p.stdout)

version = release["body"].removeprefix("gnat-")
assets = dict()
for a in release["assets"]:
    assets[a["name"]] = a

manifest = """
name = "gnat_native"
version = "%s"
provides = ["gnat=%s"]
description = "The GNAT Ada compiler - Native"
maintainers = ["Fabien Chouteau <chouteau@adacore.com>", "César Sagaert <sagaert@adacore.com>"]
maintainers-logins = ["Fabien-Chouteau", "AldanTanneo"]
licenses = "GPL-3.0-or-later AND GPL-3.0-or-later WITH GCC-exception-3.1"
website = "https://github.com/alire-project/GNAT-FSF-builds"

auto-gpr-with = false

[configuration]
disabled = true

[environment."case(os)".linux]
PATH.prepend = "${CRATE_ROOT}/bin"
LIBRARY_PATH.prepend = "${CRATE_ROOT}/lib64"
LD_LIBRARY_PATH.prepend = "${CRATE_ROOT}/lib64"
LD_RUN_PATH.prepend = "${CRATE_ROOT}/lib64"

[environment."case(os)".windows."case(host-arch)".x86-64]
PATH.prepend = "${CRATE_ROOT}/bin"
LIBRARY_PATH.prepend = "${CRATE_ROOT}/lib"
LD_LIBRARY_PATH.prepend = "${CRATE_ROOT}/lib"
LD_RUN_PATH.prepend = "${CRATE_ROOT}/lib"

[environment."case(os)".macos]
PATH.prepend = "${CRATE_ROOT}/bin"
LIBRARY_PATH.prepend = "${CRATE_ROOT}/lib"
LD_LIBRARY_PATH.prepend = "${CRATE_ROOT}/lib"
LD_RUN_PATH.prepend = "${CRATE_ROOT}/lib"
""" % (version, version)

os_template = """

[origin."case(os)".{OS}."case(host-arch)".{ARCH}]
binary = true
url = "{URL}"
hashes = ["{HASH}"]
"""

for os_name, arch, asset_identifier in [
    ("linux", "x86-64", "x86_64-linux"),
    ("linux", "aarch64", "aarch64-linux"),
    ("macos", "x86-64", "x86_64-darwin"),
    ("macos", "aarch64", "aarch64-darwin"),
    ("windows", "x86-64", "x86_64-windows64"),
]:
    key = f"gnat-{asset_identifier}-{version}.tar.gz"
    if key not in assets:
        pass
    asset = assets[key]
    t = os_template.replace("{OS}", os_name)
    t = t.replace("{ARCH}", arch)
    t = t.replace("{URL}", asset["url"])
    t = t.replace("{HASH}", asset["digest"])
    manifest += t


os.makedirs("../index/gn/gnat_native", exist_ok=True)

with open(f"../index/gn/gnat_native/gnat_native-{version}.toml") as f:
    f.write(manifest)

subprocess.run(args=["git", "add", "../index"], check=True)
subprocess.run(
    args=[
        "git",
        "commit",
        "-c",
        "user.name=github-actions",
        "-c",
        "user.email=noreply@github.com",
        "-m",
        f"gnat {version} snapshot",
    ],
    check=True,
)
subprocess.run(args=["git", "push", "origin"], check=True)
