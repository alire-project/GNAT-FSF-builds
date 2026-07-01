# GNAT-FSF-builds

Builds of the GNAT Ada compiler from FSF GCC releases.

We aim to provide builds for various platforms on every major GCC release. There are also weekly unstable "snapshots" builds of GCC's next version, to be found in the `snapshots-index` branch.


# How to build

To start the builds you will need `python3` and the `e3-core` package.
Starting from python 3.13, `e3-core` also needs the `stevedore` package to be installed.
This can be done in a virtual env, e.g.:

```console
$ python3 -m venv my-virtual-env
$ source my-virtual-env/bin/activate
$ pip install e3-core==22.10.0 stevedore
```

There is also a `pyproject.toml` file to easily setup a virtual environment with [`uv`](https://docs.astral.sh/uv/).

To build a spec, for example `mpc`, run the `anod` script:
```console
$ ./anod build mpc -v --loglevel=DEBUG
```

Or with `uv`:

```console
$ uv run ./anod mpc -v --loglevel=DEBUG
```

`-v --loglevel DEBUG` will output more information logs about the build.

For a cross compiler:

```console
$ ./anod build gcc --target=avr-elf -v --loglevel DEBUG
```

Building release packages can be done using the `release_package` spec:

```console
$ ./anod build release_package --qualifier=package=<package name>
```

Currently supported package names are `gnat`, `gprbuild`, `gnatprove`, `gnatdoc`, `gnatcov`, `gnattest` and `gnatformat`.

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
