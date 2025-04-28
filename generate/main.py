from dataclasses import dataclass
from typing import Literal
import sys

from build import (
    AnodBuild,
    Artifact,
    Conditional,
    GhRelease,
    Job,
    JobKind,
    ReleasePackage,
    Repository,
    Step,
    Targets,
)
from interfaces import Host, Yaml, Yamlable
import host

type Os = Literal["linux", "linux_arm", "macos", "macos_arm", "windows"]
oses: list[Os] = list(Os.__value__.__args__)


def pretty_name(os: Os) -> str:
    match os:
        case "linux":
            return "Linux"
        case "linux_arm":
            return "Linux Arm"
        case "macos":
            return "macOS"
        case "macos_arm":
            return "macOS Arm"
        case "windows":
            return "Windows"


def dispatch(os: Os, job: JobKind) -> Host:
    match os:
        case "linux":
            return host.Linux
        case "linux_arm":
            return host.Linux_Arm
        case "macos":
            return host.macOS
        case "macos_arm":
            return host.macOS_Arm
        case "windows":
            match job:
                case "python":
                    return host.WindowsMsys2
                case "ocaml":
                    return host.Windows


@dataclass
class Workflow(Yamlable[Os]):
    name: str
    on: Yaml
    jobs: dict[str, Job]

    def to_yaml(self, ctx: Os) -> Yaml:
        res: dict[str, Yaml] = {
            "name": self.name + " " + pretty_name(ctx),
            "on": self.on,
        }

        res["jobs"] = {
            name: job.to_yaml(dispatch(ctx, job.kind))
            for name, job in self.jobs.items()
        }
        return res


def main():
    jobs: dict[str, Job] = {}

    jobs["gcc_dependencies"] = Job(
        "GCC Dependencies",
        [
            AnodBuild("Build GMP", "gmp"),
            AnodBuild("Build MPFR", "mpfr"),
            AnodBuild("Build MPC", "mpc"),
            Conditional(
                AnodBuild("Build ISL", "isl"), lambda os: not issubclass(os, host.macOS)
            ),
        ],
        outputs=[
            Artifact("gcc-dependencies-artifacts", "out_artifacts/*", retention_days=1)
        ],
    )

    jobs["gnat"] = Job(
        "GNAT",
        [
            AnodBuild("Build GNAT native", "gcc"),
            AnodBuild("Build GDB", "gdb"),
            ReleasePackage("Package GNAT", "gnat"),
            GhRelease("Release GNAT", "gnat"),
        ],
        needs=["gcc_dependencies"],
        inputs=[
            Artifact("gcc-dependencies-artifacts", "in_artifacts/"),
        ],
        outputs=[
            Artifact(
                "gnat-release-packages",
                "sbx/*/release_package*/install/*",
                retention_days=5,
            ),
        ],
    )

    jobs["gprbuild"] = Job(
        "GPRbuild",
        [
            AnodBuild("Build GPRbuild", "gprbuild"),
            ReleasePackage("Package GPRbuild", "gprbuild"),
            GhRelease("Release GPRbuild", "gprbuild"),
        ],
        outputs=[
            Artifact(
                "gprbuild-release-packages",
                "sbx/*/release_package*/install/*",
                retention_days=5,
            ),
        ],
    )

    jobs["gnat_cross"] = Job(
        "GNAT ${{ matrix.target }}",
        [
            AnodBuild(
                "Build GNAT ${{ matrix.target }}",
                "gcc",
                ["--target=${{ matrix.target }}"],
            ),
            AnodBuild(
                "Build GDB ${{ matrix.target }}",
                "gdb",
                ["--target=${{ matrix.target}}"],
            ),
            ReleasePackage(
                "Package GNAT ${{ matrix.target }}",
                "gnat",
                ["--target=${{ matrix.target }}"],
            ),
            GhRelease(
                "Release GNAT ${{ matrix.target }}",
                "gnat",
                ["--target=${{ matrix.target }}"],
            ),
        ],
        targets=Targets(),
        needs=["gcc_dependencies"],
        inputs=[
            Artifact("gcc-dependencies-artifacts", "in_artifacts/"),
        ],
        outputs=[
            Artifact(
                "gnat-release-packages-${{matrix.target}}",
                "sbx/*/release_package*/install/*",
            )
        ],
    )

    jobs["why3"] = Job(
        "Why3",
        [
            Step(
                "Setup packages",
                [
                    "opam install zarith re seq why3 --depext-only",
                    "opam install dune dune-configurator menhir num ocamlgraph re "
                    "seq yojson zarith sexplib ppx_sexp_conv ppx_deriving",
                ],
            ),
            Step(
                "Configure why3",
                [
                    "opam exec -- ./configure --prefix=${{ github.workspace }}/why3install "
                    "--enable-relocation --disable-emacs-compilation --disable-hypothesis-selection "
                    "--disable-js-of-ocaml --disable-zip"
                ],
            ),
            Step("Make", ["opam exec -- make"]),
            Step("Install", ["opam exec -- make install_spark2014"]),
            Step(
                "Update version",
                [
                    "git log --format='%H' -n 1 > ${{ github.workspace }}/why3install/why3-version.txt"
                ],
            ),
        ],
        kind="ocaml",
        repo=Repository("adacore/why3", "fsf-14"),
        outputs=[
            Artifact("why3", "${{ github.workspace }}/why3install"),
        ],
    )

    jobs["alt_ergo"] = Job(
        "Alt-Ergo",
        [
            Step(
                "Install",
                [
                    "opam install alt-ergo --destdir=${{ github.workspace }}/alt-ergo-install"
                ],
            ),
            Step(
                "Update version",
                [
                    "git log --format='%H' -n 1 > ${{ github.workspace }}/alt-ergo-install/alt-ergo-version.txt"
                ],
            ),
        ],
        kind="ocaml",
        repo=Repository("adacore/alt-ergo", "fsf-14"),
        outputs=[Artifact("alt-ergo", "${{ github.workspace }}/alt-ergo-install")],
    )

    jobs["spark"] = Job(
        "SPARK",
        [
            AnodBuild("Build SPARK", "spark2014"),
            ReleasePackage("Package GNATprove", "gnatprove"),
            GhRelease("Release GNATprove", "gnatprove"),
        ],
        needs=["why3", "alt_ergo"],
        inputs=[
            Artifact("alt-ergo", "alt-ergo_artifact/"),
            Artifact("why3", "why3_artifact/"),
        ],
        outputs=[
            Artifact(
                "gnatprove-release-packages",
                "sbx/*/release_package*/install/*",
                retention_days=5,
            )
        ],
    )

    workflow = Workflow(
        "GNAT",
        {
            "pull_request": {
                "paths-ignore": [
                    "generate/**",
                    "utils/**",
                    "LICENSE",
                    "README.md",
                    ".gitignore",
                ],
            },
            "workflow_dispatch": {
                "inputs": {
                    "do_gh_release": {
                        "description": "Set to true to publish results in a GitHub release",
                        "type": "boolean",
                        "required": False,
                        "default": False,
                    },
                },
            },
        },
        jobs,
    )

    dest = "../.github/workflows/"
    match sys.argv:
        case [_, dirname]:
            dest = dirname.rstrip("/\\") + "/"
        case [] | [_]:
            pass
        case _:
            sys.exit("error: too many arguments")

    for os in oses:
        with open(dest + os + ".yml", "w+") as f:
            f.write(workflow.dump(os))


if __name__ == "__main__":
    main()
