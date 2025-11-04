#!/usr/bin/env python3

import json
import os
import subprocess
import time

basever = "16.0.0"
error = []

for package in ("gnat", "gnatprove"):
    release_name = f"{package}-{basever}-snapshot"

    old_rel = subprocess.run(args=["gh", "release", "view", release_name])
    new_rel = subprocess.run(args=["gh", "release", "view", f"{release_name}-draft"])

    if new_rel.returncode != 0:
        error.append(f"could not find candidate draft release for {package}")
        continue

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
        args=["gh", "release", "view", release_name, "--json", "body,assets"],
        capture_output=True,
        check=True,
    )
    release = json.loads(p.stdout)

    version = release["body"].removeprefix(f"{package}-")
    assets = dict()
    for a in release["assets"]:
        assets[a["name"]] = a

    manifest = None
    alire_crate = None
    match package:
        case "gnat":
            alire_crate = "gnat_native"
            manifest = """name = "gnat_native"
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
        case "gnatprove":
            alire_crate = "gnatprove"
            manifest = """name = "gnatprove"
            version = "%s"
            authors = ["AdaCore"]
            description = "Automatic formal verification of SPARK code"
            maintainers = ["Fabien Chouteau <chouteau@adacore.com>", "César Sagaert <sagaert@adacore.com>"]
            maintainers-logins = ["Fabien-Chouteau", "AldanTanneo"]
            licenses = "GPL-3.0-or-later"
            website = "https://docs.adacore.com/spark2014-docs/html/ug/index.html"

            long-description = \"""
            GNATprove, which provides automatic formal verification of SPARK code, is based on the [open-source](https://github.com/AdaCore/spark2014) [SPARK Pro](https://www.adacore.com/sparkpro) by [AdaCore](https://www.adacore.com).
            The [SPARK Pro User's Guide](https://docs.adacore.com/spark2014-docs/html/ug/index.html) provides extensive documentation on how to use GNATprove.
            Note that because this version of GNATprove is built from an intermediate commit of SPARK Pro, it is not representative of any specific SPARK Pro release, and the SPARK Pro documentation may describe features or capabilities that are not yet available in this version of GNATprove.

            To use GNATprove, simply add it to your Alire project using

                alr with gnatprove

            Then, configure your environment by running:

                eval "$( alr printenv )"

            You will then be able to run GNATprove:

                gnatprove

            For more details on getting started using GNATprove, see [Getting Started with SPARK](https://docs.adacore.com/spark2014-docs/html/ug/en/getting_started.html) from the [SPARK Pro User's Guide](https://docs.adacore.com/spark2014-docs/html/ug/index.html).

            To get started with the SPARK language, see the [Introduction to SPARK](https://learn.adacore.com/courses/intro-to-spark/index.html) course on [learn.adacore.com](https://learn.adacore.com/index.html).
            \"""

            auto-gpr-with = false

            [configuration]
            disabled = true

            [environment]
            PATH.prepend = "${CRATE_ROOT}/bin"
            GPR_PROJECT_PATH.prepend = "${CRATE_ROOT}/lib/gnat"
            """ % version

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
        key = f"{package}-{asset_identifier}-{version}.tar.gz"
        if key not in assets:
            continue
        asset = assets[key]
        t = os_template.replace("{OS}", os_name)
        t = t.replace("{ARCH}", arch)
        t = t.replace("{URL}", asset["url"])
        t = t.replace("{HASH}", asset["digest"])
        manifest += t


    index_path = f"../index/gn/{alire_crate}"
    if lst := os.listdir(index_path):
        # delete previous file (we don't keep artifacts around)
        for f in lst:
            os.remove(f"{index_path}/{f}")
    os.makedirs(index_path, exist_ok=True)

    with open(f"{index_path}/{alire_crate}-{version}.toml", "w+") as f:
        f.write(manifest)

    subprocess.run(args=["git", "add", "../index"], check=True)
    subprocess.run(
        args=[
            "git",
            "-c",
            "user.name=github-actions",
            "-c",
            "user.email=noreply@github.com",
            "commit",
            "-m",
            f"{package} {version} snapshot",
        ],
        check=True,
    )
    subprocess.run(args=["git", "push", "origin"], check=True)

if len(error) != 0:
    raise Exception("\n".join(error))