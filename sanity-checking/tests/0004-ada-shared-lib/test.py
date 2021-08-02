from e3.env import Env
from e3.os.fs import unixpath

from drivers.toolchain import gprbuild, gprinstall, startup_gen, run_cmd
from drivers.asserts import assert_eq
from drivers.helpers import contents
import drivers.target
import sys
import os


with open("test.gpr", "w") as out:
    out.write(
        """

with "install/share/gpr/shared_lib.gpr";

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
gprbuild("-Pshared_lib")

# Install the library
p = gprinstall("-Pshared_lib", "--prefix=install")

shared_lib_dir = os.path.join("install", "lib", "shared_lib")
shared_lib_filename = "libsharedlib" + Env().target.os.dllext
shared_lib_path = os.path.join(shared_lib_dir, shared_lib_filename)
# Check if the .a archive is here

dir_list = contents("install")
assert unixpath(shared_lib_path) in dir_list, "shared library '%s' not found in %s" % (
    unixpath(shared_lib_path),
    str(dir_list),
)

if drivers.target.board():
    startup_gen("-P", "test.gpr", "-l", "src/link.ld", "-s", "src/crt0.S")

# Build the project
gprbuild("-Ptest")

Env().add_dll_path(os.path.abspath(shared_lib_dir))
p = drivers.target.run("bin/main")

assert_eq(
    """=== Main start ===
From library
=== Main end ===
""",
    p.out,
)

if Env().host.os.name == "darwin":
    p = run_cmd(["otool", "-L", "bin/main"])
else:
    p = run_cmd(["ldd", "bin/main"])

assert shared_lib_filename in p.out, "%s not found in list of deps ('%s')" % (
    shared_lib_filename,
    p.out,
)

print("SUCCESS")
