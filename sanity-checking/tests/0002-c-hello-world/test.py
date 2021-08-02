from drivers.toolchain import gprbuild, startup_gen
from drivers.asserts import assert_eq
import drivers.target
import sys
import os


with open("test.gpr", "w") as out:
    out.write(
        """
project Test is

   --  Target Configuration
   {0}

   for Languages use ("C") & Target_Languages;

   for Object_Dir use "obj";
   for Main use ("main.c");
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

if drivers.target.board():
    startup_gen("-P", "test.gpr", "-l", "src/link.ld", "-s", "src/crt0.S")

print(os.getcwd())

# Build the project
gprbuild()

# Run it
if not drivers.target.board():
    # Add bin/ to path to have argv[0] = "main"
    os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

    # Run it
    p = drivers.target.run("main")
else:
    p = drivers.target.run("bin/main")

assert_eq(
    """Constructor says "Hi!"
Hello, there!
argv[0]: 'main'
modified argv[0]: 'test'
Destructor says "Hi!"
""",
    p.out,
)


print("SUCCESS")
