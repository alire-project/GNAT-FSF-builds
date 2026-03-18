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
    jobs: list[Job]

    def to_yaml(self, ctx: Os) -> Yaml:
        res: dict[str, Yaml] = {
            "name": self.name,
            "on": self.on,
        }

        res["jobs"] = dict()
        for os in oses:
            res["jobs"].update(
                {
                    job.key(dispatch(os, job.kind)): job.to_yaml(dispatch(os, job.kind))
                    for job in self.jobs
                }
            )
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
        needs=[jobs["gcc_dependencies"]],
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
        "GNAT Cross",
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
        needs=[jobs["gcc_dependencies"]],
        outputs=[
            Artifact(
                "gnat-release-packages-${{matrix.target}}",
                "sbx/*/release_package*/install/*",
            )
        ],
    )

    jobs["spark"] = Job(
        "SPARK",
        [
            AnodBuild("Build SPARK", "spark2014"),
            ReleasePackage("Package GNATprove", "gnatprove"),
            GhRelease("Release GNATprove", "gnatprove"),
        ],
        needs=[jobs["gprbuild"]],
        outputs=[
            Artifact(
                "gnatprove-release-packages",
                "sbx/*/release_package*/install/*",
                retention_days=5,
            )
        ],
    )

    jobs["gnatformat"] = Job(
        "GNATformat",
        [
            AnodBuild("Build GNATformat", "gnatformat"),
            ReleasePackage("Package GNATformat", "gnatformat"),
            GhRelease("Release GNATformat", "gnatformat"),
        ],
        needs=[jobs["gprbuild"]],
        outputs=[
            Artifact(
                "gnatformat-release-packages",
                "sbx/*/release_package*/install/*",
                retention_days=5,
            )
        ],
    )

    jobs["gnatdoc"] = Job(
        "GNATdoc",
        [
            AnodBuild("Build GNATdoc", "gnatdoc"),
            ReleasePackage("Package GNATdoc", "gnatdoc"),
            GhRelease("Release GNATdoc", "gnatdoc"),
        ],
        needs=[jobs["gprbuild"]],
        outputs=[
            Artifact(
                "gnatdoc-release-packages",
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
        list(jobs.values()),
    )

    dest = "../.github/workflows/"
    match sys.argv:
        case [_, dirname]:
            dest = dirname.rstrip("/\\") + "/"
        case [] | [_]:
            pass
        case _:
            sys.exit("error: too many arguments")

    with open(dest + "main.yml", "w+") as f:
        _ = f.write(workflow.dump("linux"))


if __name__ == "__main__":
    main()
