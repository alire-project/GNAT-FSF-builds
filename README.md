# GNAT FSF weekly snapshots

This branch is an Alire index containing weekly builds of unstable [GCC snapshots](https://gcc.gnu.org/pub/gcc/snapshots/LATEST-16/). You can add this index to your Alire setup with the command

```sh
alr index --add="git+https://github.com/alire-project/GNAT-FSF-builds#snapshots-index" --name=snapshots
```

The snapshots are built from the `snapshots` branch of this repository, every Tuesday. The
artifacts are not kept week to week, so every week the previous snapshot is removed from the index.

There are NO guarantees on the produced compiler. It is not guaranteed to be stable, and build
failures are minimally investigated.
