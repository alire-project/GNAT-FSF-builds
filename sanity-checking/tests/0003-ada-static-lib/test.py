from drivers.toolchain import gprbuild, gprinstall, startup_gen
from drivers.asserts import assert_eq
from drivers.helpers import contents
import drivers.target
import sys
import os


with open("test.gpr", "w") as out:
    out.write(
        """

with "install/share/gpr/static_lib.gpr";

project Test is

   --  Target Configuration
   {0}

   for Languages use ("Ada") & Target_Languages;

   for Object_Dir use "obj";
   for Main use ("main.adb");
   for Exec_Dir use "bin";
   for Source_Dirs use ("src");

   package Compiler is
      for Switches ("C") use Target_Compiler_Switches;
      for Switches ("Asm_Cpp") use Target_Compiler_Switches;
   end Compiler;

   package Builder is
      for Switches ("C") use ("-s");
   end Builder;

   package Linker is
      for Switches ("C") use Target_Linker_Switches;
   end Linker;

end Test;
""".format(
            drivers.target.gpr_insert()
        )
    )

# Build the library
gprbuild("-Pstatic_lib")

# Install the library
p = gprinstall("-Pstatic_lib", "--prefix=install")

# Check if the .a archive is here
if "install/lib/static_lib/libstaticlib.a" not in contents("install"):
    assert False, "static library not found"

if drivers.target.board():
    startup_gen("-P", "test.gpr", "-l", "src/link.ld", "-s", "src/crt0.S")

# Build the project
gprbuild("-Ptest")

p = drivers.target.run("bin/main")

assert_eq(
    """=== Main start ===
From library
=== Main end ===
""",
    p.out,
)

print("SUCCESS")
