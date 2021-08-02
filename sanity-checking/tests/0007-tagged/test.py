from drivers.toolchain import gprbuild, startup_gen
from drivers.asserts import assert_eq
import drivers.target

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

# Run it
p = drivers.target.run("bin/hello")
assert_eq("B\nC\n", p.out)


print("SUCCESS")
