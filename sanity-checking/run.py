#! /usr/bin/env python

from __future__ import absolute_import, print_function

### Hack to get the platform DB in e3.platform plug-ing ###
import importlib
from stevedore import ExtensionManager
dummy_ep = importlib.metadata.EntryPoint('my_db', 'drivers.platform_db:PlatDB', 'e3.platform_db')
ExtensionManager.ENTRY_POINT_CACHE = {'e3.platform_db': [dummy_ep]}
### END OF HACK ###

import os.path
import sys

from pathlib import Path

import e3.testsuite
import e3.testsuite.driver
from e3.testsuite.result import TestStatus
from e3.archive import unpack_archive
from e3.anod.helper import log
from e3.fs import mkdir, rm

from drivers.python_script import PythonScriptDriver


class Testsuite(e3.testsuite.Testsuite):
    tests_subdir = "tests"
    test_driver_map = {"python-script": PythonScriptDriver}

    def enable_cross_support(self):
        return True

    def add_options(self, parser):
        parser.add_argument(
            "--install-deps-from",
            help="Directory where depency packages are stored (GNAT, GPRBUILD, etc.)",
        )
        parser.add_argument(
            "--pkgs-install-dir",
            required=True,
            help="Directory where depency packages are/will be installed",
        )
        parser.add_argument("--runtime", help="Ada run-time name or absolute path")
        parser.add_argument("--board", help="Name of the board to run test on, if any")

    def install_pkg(self, pkg, dest):
        log.info("Installing %s." % pkg)
        pkgs_dir = os.path.abspath(self.env.options.install_deps_from)
        log.info("Using package dir '%s'." % str(pkgs_dir))

        # The package may be located in sub-dirs so use rglob to find it
        paths = list(Path(pkgs_dir).rglob(pkg + "*.tar.gz"))

        if len(paths) == 0:
            log.error("Package for '%s' not found." % pkg)
            sys.exit(1)
        if len(paths) > 1:
            log.error("More than one package for '%s': %s." % (pkg, str(paths)))
            sys.exit(1)

        tarball = paths[0]
        print(tarball)
        log.info("Unpacking '%s' into '%s'" % (tarball, dest))
        unpack_archive(filename=tarball, dest=dest, remove_root_dir=True)

    def install_all_deps(self, install_dir):
        required_pkgs = [
            "gnat-" + self.env.platform,
            "gprbuild-" + self.env.host.platform,
            "gnatcov-" + self.env.host.platform,
        ]

        rm(install_dir, recursive=True)
        mkdir(install_dir)

        for pkg in required_pkgs:
            self.install_pkg(pkg, install_dir)

    def set_up(self):
        super().set_up()

        install_dir = os.path.abspath(self.env.options.pkgs_install_dir)

        if self.env.options.install_deps_from is not None:
            self.install_all_deps(install_dir)

        self.env.add_path(os.path.join(install_dir, "bin"))
        self.env.add_dll_path(os.path.join(install_dir, "lib"))

        # Some tests rely on an initially empty GPR_PROJECT_PATH variable
        os.environ.pop("GPR_PROJECT_PATH", None)


if __name__ == "__main__":
    suite = Testsuite()
    sys.exit(suite.testsuite_main())
