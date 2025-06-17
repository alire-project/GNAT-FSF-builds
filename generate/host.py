from dataclasses import dataclass, field

from build import Action, InstallPythonDeps, SetupOcaml, SetupPython, Step
from interfaces import Host, HostOs, RawStep, Yaml, Yamlable


class Unix(HostOs):
    @classmethod
    def setup_python(cls) -> list[RawStep]:
        return [
            SetupPython(cls.python_version),
            InstallPythonDeps({"e3-core": cls.e3_core_version}),
        ]

    @classmethod
    def setup_ocaml(cls) -> list[RawStep]:
        return [SetupOcaml(cls.ocaml_version)]


class Linux(Unix):
    runner: str = "ubuntu-22.04"


class Linux_Arm(Unix):
    runner: str = "ubuntu-22.04-arm"


class macOS(Unix):
    runner = "macos-13"

    @classmethod
    def setup_python(cls) -> list[RawStep]:
        return [
            Step(
                "Install packages with Homebrew",
                [
                    "brew install texinfo",
                    "brew install autoconf",
                    "brew install automake",
                ],
            ),
            *super().setup_python(),
        ]


class macOS_Arm(macOS):
    runner = "macos-14"

    @classmethod
    def setup_python(cls) -> list[RawStep]:
        return [
            Step(
                "Set Xcode 15.3",
                ["sudo xcode-select --switch /Applications/Xcode_15.3.app"],
            ),
            *super().setup_python(),
        ]


class Windows(HostOs):
    runner = "windows-2019"

    @classmethod
    def setup_ocaml(cls) -> list[RawStep]:
        return [SetupOcaml(cls.ocaml_version)]


class WindowsMsys2(Windows):
    env = {"CONFIG_SHELL": "/bin/bash"}
    shell = "msys2 {0}"

    host_dir: str = "C:/aaa"
    mount_point: str = "/aaa"

    @classmethod
    def native_path(cls, path: str) -> str:
        return cls.host_dir + "/" + cls.workdir + "/" + path.lstrip("/")

    @classmethod
    def command(cls, cmd: list[str]) -> str:
        return (
            f"mount {cls.host_dir} {cls.mount_point} && "
            + f"cd {cls.mount_point}/{cls.workdir} && "
            + "\n".join(cmd)
        )

    @classmethod
    def setup_python(cls) -> list[RawStep]:
        @dataclass
        class Msys2Args(Yamlable[Host]):
            msystem: str | None = None
            update: bool = False
            install: list[str] = field(default_factory=list)

            def to_yaml(self, ctx: Host) -> Yaml:
                res = dict()
                if self.msystem is not None:
                    res["msystem"] = self.msystem
                if self.update:
                    res["update"] = True
                res["install"] = "\n".join(self.install)
                return res

        return [
            Action(
                "Install msys2",
                "msys2/setup-msys2@v2",
                with_args=Msys2Args(
                    install=[
                        "base-devel",
                        "git",
                        "rsync",
                        "mingw-w64-x86_64-github-cli",
                        "mingw-w64-x86_64-toolchain",
                        "mingw-w64-x86_64-python",
                        "mingw-w64-x86_64-python-pip",
                        "mingw-w64-x86_64-python-psutil",
                    ],
                ),
            ),
            InstallPythonDeps({"e3-core": cls.e3_core_version}),
            RawStep(
                "Prepare msys2 build setup",
                # we need a path that is compatible between Windows and Unix world
                [
                    "df -h",
                    f"mkdir {cls.host_dir}",
                    f"mount {cls.host_dir} {cls.mount_point}",
                    "cd ..",
                    f"cp -r {cls.workdir} {cls.mount_point}",
                ],
            ),
        ]

    @classmethod
    def setup_ocaml(cls) -> list[RawStep]:
        raise NotImplementedError
