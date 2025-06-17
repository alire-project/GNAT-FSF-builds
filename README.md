# GNAT-FSF-builds
Builds of the GNAT Ada compiler from FSF GCC releases

# How to build

To start the builds you will need `python3` (up to version 3.12) and the `e3-core` package.
This can be done in a virtual env, e.g.:

```console
$ python3 -m venv my-virtual-env
$ source my-virtual-env/bin/activate
$ pip install e3-core==22.1.0
```

A Python 3.12 specific environment can be created with [`uv`](https://docs.astral.sh/uv/) instead:

```console
$ uv venv --python=3.12
```

To build a spec, for example `mpc`, run the `anod` script:
```console
$ ./anod build mpc -v --loglevel DEBUG
```

`-v --loglevel DEBUG` will produce many information log about the build.

For a cross compiler:

```console
$ ./anod build gcc --target=avr-elf -v --loglevel DEBUG
```

To build the full aarch64-elf cross-compiler package:

```console
./anod build release_package --qualifier=package=gnat --target=aarch64-elf -v
```

Then the binary files will be at:

```console
sbx/aarch64-elf-linux64/release_package-gnat-aarch64-elf-linux64/install/gnat-aarch64-elf-linux64-x86_64-<vserion>.tar.gz
```

Building release packages can be done using the `release_package` spec:

```console
$ ./anod build release_package --qualifier=package=<package name>
```

Currently supported package names are `gnat`, `gprbuild` and `gnatprove`.

## On Windows
Only builds in the msys2 mingw64 environement are supported.
You will need:

 - `mingw-w64-x86_64-python-psutil` package for `e3-core` installation to work.

 - The Unix and Windows PATH of the repo checkout must match:
   `C:\dir1\dir2\GNAT-FSF-builds` <-> `\dir1\dir2\GNAT-FSF-builds`. This can be
   done by "mounting" Windows directories in msys2, e.g.: `mount C:/Users
   /Users`.

# Writing specs
Until the `e3-core`/`anod` documentation is available online, the best way to
write a spec is to start from an existing one. A good starting point would be
[`gnatcoll.anod`](https://github.com/alire-project/GNAT-FSF-builds/blob/main/specs/gnatcoll.anod).

 - First, change the `version`, `tarball` and, `source_pkg_build` url
 - Modify the list of `build_deps`, you probably need at least `gcc`.
 - Change the configure/make options

# Publishing to the Alire index

A [little script](utils/gen_gnat_manifests.py) is available to speedup the
process of publising GNAT FSF package to the Alire index.

Edit the PKG_VERSION and CRATE_VERSION constant and then run the script to
generate all the GNAT manifests. The script also checks the correctness of
sha256 hashes.
