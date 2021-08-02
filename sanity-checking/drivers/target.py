"""
Helpers to run executables on the target platform (sometimes).
"""

import os.path

from shutil import copytree
from e3.os.process import Run, quote_arg
from e3.fs import mkdir
from e3.testsuite.driver.classic import ProcessResult

import re


TESTSUITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CalledProcessError(Exception):
    pass


def board_command(board, argv):
    """
    Return the command to run an executable on the target board.
    """

    assert len(argv) == 1, "Cannot pass argument when running on QEMU"

    if board == "qemu-microbit":
        return [
            "qemu-system-arm",
            "-nographic",
            "-no-reboot",
            "-M",
            "microbit",
            "-semihosting-config",
            "enable=on,chardev=serial0,target=native",
            "-kernel",
            argv[0],
        ]

    elif board == "qemu-stm32f4":
        return [
            "qemu-system-arm",
            "-nographic",
            "-no-reboot",
            "-M",
            "stm32",
            "-cpu",
            "cortex-m4f",
            "-semihosting-config",
            "enable=on,chardev=serial0,target=native",
            "-kernel",
            argv[0],
        ]
    elif board == "qemu-hifive1":
        return [
            "qemu-system-riscv32",
            "-nographic",
            "-no-reboot",
            "-accel",
            "tcg,forbid-mmio-exec=on",
            "-M",
            "sifive_e",
            "-kernel",
            argv[0],
        ]
    else:
        raise ValueError("Unknown board:" + board)


def run(*args, **kwargs):
    """
    Run an executable on target.

    :param bool complain_on_error: If true and the subprocess exits with a
        non-zero status code, print information on the standard output (for
        debugging) and raise a CalledProcessError (to abort the test).
    :rtype: ProcessResult
    """

    complain_on_error = kwargs.pop("complain_on_error", True)
    quiet = kwargs.pop("quiet", True)
    if kwargs:
        first_unknown_kwarg = sorted(kwargs)[0]
        raise ValueError("Invalid argument: {}".format(first_unknown_kwarg))

    argv = []
    argv.extend(args)

    if board() is not None:
        argv = board_command(board(), argv)

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


def name():
    return os.environ.get("TEST_TARGET")


def runtime():
    return os.environ.get("TEST_RUNTIME")


def board():
    return os.environ.get("TEST_BOARD")


def gpr_insert():
    """
    A piece of GPR file with target specific options and compilation flags.
    """

    if board() == "qemu-hifive1":
        return """
   Target_Languages := ("ASM_CPP");

   Target_Compiler_Switches := ("-march=rv32imac",
                         "-mabi=ilp32",
                         "-DTEST_BOARD_HIFIVE1");

   Target_Linker_Switches :=
     ("-Wl,-T," & Project'Project_Dir & "src/link.ld",
      "-L" & Project'Project_Dir & "lib",
      "-nostartfiles",
      "-lc", "-lgcc", "-lc"
     ) &
     Target_Compiler_Switches;

   package Device_Configuration is
      for CPU_Name use "RISC-V32";

      for Memories use ("flash", "ram");
      for Boot_Memory use "flash";

      for Mem_Kind ("flash") use "ROM";
      for Address ("flash")  use "0x20400000";
      for Size ("flash")     use "512M";

      for Mem_Kind ("ram") use "RAM";
      for Address ("ram")  use "0x80000000";
      for Size ("ram")     use "16K";
   end Device_Configuration;
   """

    else:
        return """
   Target_Languages := ();
   Target_Compiler_Switches := ("-DTEST_BOARD_NATIVE");
   Target_Linker_Switches := ();
   """
