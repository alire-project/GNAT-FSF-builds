from typing import Literal

from build import (
    AnodBuild,
    Artifact,
    Checkout,
    Conditional,
    Job,
    JobKind,
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


class Workflow(Yamlable[Os]):
    def __init__(self, name: str, on: list[str], jobs: dict[str, Job]):
        self.name = name
        self.on = on
        self.jobs = jobs

    def to_yaml(self, ctx: Os) -> Yaml:
        res: dict[str, Yaml] = {
            "name": self.name + " " + pretty_name(ctx),
            "on": list(self.on),
        }

        res["jobs"] = {
            name: job.to_yaml(dispatch(ctx, job.kind))
            for name, job in self.jobs.items()
        }
        return res


def main():
    jobs: dict[str, Job] = {}

    jobs["gnat"] = Job(
        "GNAT",
        [
            Conditional(
                Step(
                    "Install Ada dependencies",
                    [
                        "sudo apt-get update",
                        "DEBIAN_FRONTEND=noninteractive sudo apt-get install -y texinfo",
                    ],
                ),
                lambda os: issubclass(os, host.Linux),
            ),
            AnodBuild("Build GNAT native", "gcc"),
            AnodBuild("Build GDB", "gdb"),
            AnodBuild(
                "Package GNAT",
                "release_package",
                ["--qualifier=package=gnat,do_gh_release"],
                secrets=["GITHUB_TOKEN"],
            ),
        ],
        outputs=[
            Artifact(
                "gnat-anod-artifacts",
                "out_artifacts/*",
                retention_days=1,
            ),
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
            AnodBuild(
                "Package GPRbuild",
                "release_package",
                ["--qualifier=package=gprbuild,do_gh_release"],
                secrets=["GITHUB_TOKEN"],
            ),
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
            AnodBuild(
                "Package GNAT ${{ matrix.target }}",
                "release_package",
                [
                    "--qualifier=package=gnat,do_gh_release",
                    "--target=${{ matrix.target }}",
                ],
            ),
        ],
        needs=["gnat"],
        targets=Targets(),
        inputs=[Artifact("gnat-anod-artifacts", "in_artifacts/")],
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
            Checkout(Repository("adacore/why3", "fsf-14")),
            Step(
                "Setup packages",
                [
                    "opam depext zarith re seq why3",
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
        outputs=[
            Artifact("why3", "${{ github.workspace }}/why3install"),
        ],
    )

    jobs["alt_ergo"] = Job(
        "Alt-Ergo",
        [
            Checkout(Repository("adacore/alt-ergo", "fsf-14")),
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
        outputs=[Artifact("alt-ergo", "${{ github.workspace }}/alt-ergo-install")],
    )

    jobs["spark"] = Job(
        "SPARK",
        [
            AnodBuild("Build SPARK", "spark2014"),
            AnodBuild(
                "Package GNATprove",
                "release_package",
                ["--qualifier=package=gnatprove,do_gh_release"],
                secrets=["GITHUB_TOKEN"],
            ),
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
        ["pull_request"],
        jobs,
    )

    for os in oses:
        with open("../.github/workflows/" + os + ".yml", "w+") as f:
            f.write(workflow.dump(os))


if __name__ == "__main__":
    main()
