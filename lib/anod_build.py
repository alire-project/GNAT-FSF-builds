#!/usr/bin/env python3

"""Anod-based build script."""

from __future__ import annotations

from lib.anod.build import FSFBuildBuilder
from lib.anod.util import create_anod_context, create_anod_sandbox
from lib.anod.paths import REPO_DIR, SPEC_DIR, SBX_DIR

from e3.anod.status import ReturnValue
from e3.env import BaseEnv, Env
from e3.main import Main

import os


# FSFBuild repo root directory
FSFBUILD_ROOT_DIR = os.path.dirname(REPO_DIR)
os.environ["FSFBUILD_ROOT_DIR"] = FSFBUILD_ROOT_DIR

# Define what we mean by a successful build.
BUILD_SUCCESS = [
    ReturnValue.success,
    ReturnValue.force_skip,
    ReturnValue.skip,
    ReturnValue.unchanged,
]


def do_build(m: Main, set_prog: bool = True) -> int:
    """Perform the build."""
    if set_prog:
        m.argument_parser.prog = m.argument_parser.prog + " build"
    m.argument_parser.add_argument(
        "spec_name",
        help="spec to build. This is "
        "the basename of an .anod file (without the extension)",
    )
    m.argument_parser.add_argument("--qualifier", help="optional qualifier")
    m.argument_parser.add_argument(
        "--sandbox-dir",
        help="directory in which build artefacts are stored",
        default=SBX_DIR,
    )
    m.argument_parser.add_argument(
        "--force",
        help="force rebuild of everything",
        action="store_true",
        default=False,
    )

    m.argument_parser.add_argument(
        "--enable-cleanup",
        help="Enable removal of build and source dirs after the build",
        action="store_true",
        default=False,
    )

    m.argument_parser.add_argument(
        "--build",
        default=None,  # to force autodetection
        help="Set the build platform and build os version",
        )
    m.argument_parser.add_argument(
        "--host",
        default=None,  # to force autodetection
        help="Set the host platform, host os version",
        metavar="HOST[,HOST_VERSION]",
        )
    m.argument_parser.add_argument(
        "--target",
        default=None,  # to force autodetection
        help="Set the target platform, target os version, "
        "target machine, and target mode",
        metavar="TARGET[,TARGET_VERSION[,TARGET_MACHINE[,TARGET_MODE]]]",
    )

    m.parse_args()

    ac = create_anod_context(SPEC_DIR)
    sbx = create_anod_sandbox(m.args.sandbox_dir, SPEC_DIR)

    env = BaseEnv.from_env()
    env.set_env(m.args.build, m.args.host, m.args.target)

    sbx.create_dirs()

    ac.add_anod_action(
        name=m.args.spec_name,
        primitive="build",
        qualifier=m.args.qualifier,
        sandbox=sbx,
        upload=False,
        env=env,
    )
    actions = ac.schedule(resolver=ac.always_create_source_resolver)

    walker = FSFBuildBuilder(actions, sandbox=sbx, force=m.args.force)

    # TODO: something with walker.job_status['root'], assuming we can get a
    # useful value there. Right now, it's always 'unknown'
    #
    # In the meantime, python > 3.6 guarantees the order of keys in a dict.
    # The job_status dict has as its penultimate entry the thing we asked to
    # build or the last thing that failed (the last non-root node). It's ugly,
    # but _should_ be safe to use this, until we have resolution for root
    # always reporting unknown.
    result: ReturnValue = list(walker.job_status.values())[-2]

    if result in BUILD_SUCCESS:
        return 0
    else:
        return result.value


def do_install(m: Main, set_prog: bool = True) -> int:
    """Perform the build."""
    if set_prog:
        m.argument_parser.prog = m.argument_parser.prog + " build"
    m.argument_parser.add_argument(
        "spec_name",
        help="spec to build. This is "
        "the basename of an .anod file (without the extension)",
    )
    m.argument_parser.add_argument("--qualifier", help="optional qualifier")
    m.argument_parser.add_argument(
        "--sandbox-dir",
        help="directory in which build artefacts are stored",
        default=SBX_DIR,
    )
    m.argument_parser.add_argument(
        "--force",
        help="force rebuild of everything",
        action="store_true",
        default=False,
    )
    m.parse_args()

    ac = create_anod_context(SPEC_DIR)
    sbx = create_anod_sandbox(m.args.sandbox_dir, SPEC_DIR)

    sbx.create_dirs()

    ac.add_anod_action(
        name=m.args.spec_name,
        primitive="install",
        qualifier=m.args.qualifier,
        sandbox=sbx,
        upload=False,
        env=BaseEnv.from_env(),
    )
    actions = ac.schedule(resolver=ac.always_create_source_resolver)

    walker = FSFBuildBuilder(actions, sandbox=sbx, force=m.args.force)

    # TODO: something with walker.job_status['root'], assuming we can get a
    # useful value there. Right now, it's always 'unknown'
    #
    # In the meantime, python > 3.6 guarantees the order of keys in a dict.
    # The job_status dict has as its penultimate entry the thing we asked to
    # build or the last thing that failed (the last non-root node). It's ugly,
    # but _should_ be safe to use this, until we have resolution for root
    # always reporting unknown.
    result: ReturnValue = list(walker.job_status.values())[-2]

    if result in BUILD_SUCCESS:
        return 0
    else:
        return result.value


if __name__ == "__main__":
    exit(do_build(Main(), set_prog=False))
