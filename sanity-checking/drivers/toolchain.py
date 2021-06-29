"""
Helpers to run toolchain commands in the testsuite.
"""

import os.path

from shutil import copytree
from e3.os.process import Run, quote_arg
from e3.fs import mkdir
from e3.testsuite.driver.classic import ProcessResult

import drivers.target
import re


TESTSUITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CalledProcessError(Exception):
    pass


def run_cmd(argv, complain_on_error=True):
    p = Run(argv)
    if p.status != 0 and complain_on_error:
        print("The following command:")
        print("  {}".format(" ".join(quote_arg(arg) for arg in argv)))
        print("Exitted with status code {}".format(p.status))
        print("Output:")
        print(p.out)
        raise CalledProcessError(argv[0] + " returned non-zero status code")

    # Convert CRLF line endings (Windows-style) to LF (Unix-style). This
    # canonicalization is necessary to make output comparison work on all
    # platforms.
    return ProcessResult(p.status, p.out.replace("\r\n", "\n"))


def gprbuild(*args, **kwargs):
    """
    Run "gprbuild" with the given arguments.

    :param bool complain_on_error: If true and the subprocess exits with a
        non-zero status code, print information on the standard output (for
        debugging) and raise a CalledProcessError (to abort the test).
    :param bool quiet: If true (which is the default), append "-q" to the
        command line.
    :rtype: ProcessResult
    """

    complain_on_error = kwargs.pop("complain_on_error", True)
    quiet = kwargs.pop("quiet", True)
    if kwargs:
        first_unknown_kwarg = sorted(kwargs)[0]
        raise ValueError("Invalid argument: {}".format(first_unknown_kwarg))

    argv = ["gprbuild"]
    if quiet:
        argv.append("-q")

    # Always create missing directories
    argv.append("-p")

    if drivers.target.name():
        argv.append("--target=" + drivers.target.name())

    if drivers.target.runtime():
        argv.append("--RTS=" + drivers.target.runtime())

    argv.extend(args)
    print(str(argv))
    return run_cmd(argv, complain_on_error)


def gprinstall(*args, **kwargs):
    """
    Run "gprinstall" with the given arguments.

    :param bool complain_on_error: If true and the subprocess exits with a
        non-zero status code, print information on the standard output (for
        debugging) and raise a CalledProcessError (to abort the test).
    :param bool quiet: If true (which is the default), append "-q" to the
        command line.
    :rtype: ProcessResult
    """

    complain_on_error = kwargs.pop("complain_on_error", True)
    quiet = kwargs.pop("quiet", True)
    if kwargs:
        first_unknown_kwarg = sorted(kwargs)[0]
        raise ValueError("Invalid argument: {}".format(first_unknown_kwarg))

    argv = ["gprinstall"]
    if quiet:
        argv.append("-q")

    # Always create missing directories
    argv.append("-p")

    if drivers.target.name():
        argv.append("--target=" + drivers.target.name())

    if drivers.target.runtime():
        argv.append("--RTS=" + drivers.target.runtime())

    argv.extend(args)
    return run_cmd(argv, complain_on_error)


def startup_gen(*args, **kwargs):
    """
    Run "startup-gen" with the given arguments.

    :param bool complain_on_error: If true and the subprocess exits with a
        non-zero status code, print information on the standard output (for
        debugging) and raise a CalledProcessError (to abort the test).
    :rtype: ProcessResult
    """

    complain_on_error = kwargs.pop("complain_on_error", True)
    if kwargs:
        first_unknown_kwarg = sorted(kwargs)[0]
        raise ValueError("Invalid argument: {}".format(first_unknown_kwarg))

    argv = ["startup-gen"]
    argv.extend(args)
    return run_cmd(argv, complain_on_error)
