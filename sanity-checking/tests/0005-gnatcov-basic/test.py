from drivers.toolchain import gprbuild, startup_gen, run_cmd
from drivers.helpers import check_line_in
import drivers.target
from e3.fs import ls
from e3.os.fs import which
from e3.os.process import Run
from e3.anod.helper import log
from e3.env import Env

import os

gnatcov_bin = which("gnatcov")
gnatcov_path = os.path.dirname(gnatcov_bin)
gnatcov_rts_path = os.path.join(
    gnatcov_path, "..", "share/gnatcoverage/gnatcov_rts/gnatcov_rts_full.gpr"
)

with open("test.gpr", "w") as out:
    out.write(
        """
project Test is

   --  Target Configuration
   {0}

   for Languages use ("Ada") & Target_Languages;

   for Object_Dir use "obj";
   for Main use ("hello.adb");
   for Exec_Dir use "bin";
   for Source_Dirs use ("src");

   package Compiler is
      for Switches ("Ada") use Target_Compiler_Switches;
      for Switches ("Asm_Cpp") use Target_Compiler_Switches;
   end Compiler;
   package Linker is
      for Switches ("Ada") use Target_Linker_Switches;
   end Linker;

end Test;
""".format(
            drivers.target.gpr_insert()
        )
    )

if drivers.target.board():
    startup_gen("-P", "test.gpr", "-l", "src/link.ld", "-s", "src/crt0.S")

# Build the project
gprbuild()

# Add coverage instrumentation
run_cmd(["gnatcov", "instrument", "-Ptest", "--level=stmt", "--dump-trigger=atexit"])

# Build the project with instrumentation
gprbuild(
    "-Ptest", "--src-subdirs=gnatcov-instr", "--implicit-with=%s" % gnatcov_rts_path
)

# Run it
p = drivers.target.run("bin/hello")

# Do coverage analysis
run_cmd(
    [
        "gnatcov",
        "coverage",
        "-Ptest",
        "--level=stmt",
        "--annotate=xcov"] + ls("*.srctrace")
)

check_line_in(
    "obj/hello.adb.xcov", '   5 +:    Ada.Text_IO.Put_Line ("Hello, World!");'
)

print("SUCCESS")
