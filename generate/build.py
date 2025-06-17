from dataclasses import dataclass, field
from typing import Callable, Literal


from interfaces import RawStep, Yaml, Yamlable, Host


@dataclass
class Step(RawStep):
    name: str
    command: list[str] | None
    uses: str | None = None
    with_args: Yamlable[Host] | None = None
    secrets: list[str] = field(default_factory=list)

    def to_yaml(self, ctx: Host) -> Yaml:
        res: Yaml = {
            "name": self.name,
        }
        if self.uses is not None:
            res["uses"] = self.uses
            if self.with_args is not None:
                res["with"] = self.with_args.to_yaml(ctx)
        if self.command is not None:
            res["run"] = ctx.command(self.command)
        if len(self.secrets) != 0:
            res["env"] = {s: "${{ secrets." + s + " }}" for s in self.secrets}

        return res


class Action(Step):
    command: list[str] | None = None

    def __init__(
        self,
        name: str,
        action: str,
        with_args: Yamlable[Host] | None = None,
        secrets: list[str] | None = None,
    ):
        if secrets is None:
            secrets = []
        self.name = name
        self.uses = action
        self.with_args = with_args
        self.secrets = secrets


class AnodBuild(Step):
    def __init__(
        self,
        name: str,
        package: str,
        args: list[str] | None = None,
        secrets: list[str] | None = None,
        verbose: bool = True,
        loglevel: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG",
    ):
        if secrets is None:
            secrets = []
        if args is None:
            args = []
        self.name = name
        self.secrets = secrets
        if verbose:
            args.append("-v")
        args.append("--loglevel")
        args.append(loglevel)
        if package not in ["release_package", "gh-release"]:
            args.append("--enable-cleanup")
        self.command = ["python3 ./anod build " + package + " " + " ".join(args)]


class ReleasePackage(AnodBuild):
    def __init__(self, name: str, package: str, args: list[str] = []):
        super().__init__(
            name,
            "release_package",
            [f"--qualifier=package={package}", *args],
        )


class GhRelease(AnodBuild):
    def __init__(self, name: str, package: str, args: list[str] = []):
        super().__init__(
            name,
            "release_github",
            [f"--qualifier=package={package}", *args],
            secrets=["GITHUB_TOKEN"],
        )

    def to_yaml(self, ctx: Host) -> Yaml:
        spr = super().to_yaml(ctx)
        assert isinstance(spr, dict)
        return {"if": "inputs.do_gh_release", **spr}


@dataclass
class Artifact(Yamlable[Host]):
    name: str
    path: str
    retention_days: int = 0

    def to_yaml(self, ctx: Host) -> Yaml:
        res: Yaml = {"name": self.name, "path": ctx.native_path(self.path)}
        if self.retention_days > 0:
            res["retention-days"] = self.retention_days
        return res


class UploadArtifact(Action):
    def __init__(self, art: Artifact):
        super().__init__(
            f"Upload artifact '{art.name}'",
            "actions/upload-artifact@v4",
            with_args=art,
        )


class DownloadArtifact(Action):
    def __init__(self, art: Artifact):
        super().__init__(
            f"Download artifact '{art.name}'",
            "actions/download-artifact@v4",
            with_args=art,
        )


@dataclass
class Repository(Yamlable[Host]):
    repository: str
    ref: str

    def to_yaml(self, ctx: Host) -> Yaml:
        return {"repository": self.repository, "ref": self.ref}


class Checkout(Action):
    def __init__(
        self,
        repo: Repository | None = None,
    ):
        super().__init__("Checkout Project", "actions/checkout@v4", with_args=repo)


@dataclass
class PythonVersion(Yamlable[Host]):
    version: str

    def to_yaml(self, ctx: Host) -> Yaml:
        return {"python-version": self.version}


class SetupPython(Action):
    def __init__(self, python_version: str):
        super().__init__(
            f"Set up Python {python_version}",
            "actions/setup-python@v5",
            with_args=PythonVersion(python_version),
        )


@dataclass
class OcamlVersion(Yamlable[Host]):
    version: str

    def to_yaml(self, ctx: Host) -> Yaml:
        return {"ocaml-compiler": self.version}


class SetupOcaml(Action):
    def __init__(self, ocaml_version: str):
        super().__init__(
            f"Setup OCaml {ocaml_version}",
            "ocaml/setup-ocaml@v3",
            with_args=OcamlVersion(ocaml_version),
        )


class InstallPythonDeps(RawStep):
    def __init__(self, deps: dict[str, str]):
        super().__init__(
            "Install Python dependencies",
            [
                "python3 -m pip install --upgrade pip",
                "pip install --break-system-packages "
                + " ".join([d if v == "*" else f"{d}=={v}" for d, v in deps.items()]),
            ],
        )


class Targets(Yamlable[Host]):
    def to_yaml(self, ctx: Host) -> Yaml:
        return ["arm-elf", "riscv64-elf", "avr-elf", "xtensa-esp32-elf"]


class Conditional(RawStep):
    cond: Callable[[Host], bool]

    def __init__(self, step: RawStep, cond: Callable[[Host], bool]):
        self.step = step
        self.cond = cond

    def to_yaml(self, ctx: Host) -> Yaml:
        if self.cond(ctx):
            return self.step.to_yaml(ctx)
        else:
            return None


type JobKind = Literal["python", "ocaml"]


@dataclass
class Job(Yamlable[Host]):
    name: str
    steps: list[RawStep]

    kind: JobKind = "python"
    repo: Repository | None = None
    needs: list[str] = field(default_factory=list)
    matrix: dict[str, list[str]] = field(default_factory=dict)
    targets: Targets | None = None

    inputs: list[Artifact] = field(default_factory=list)
    outputs: list[Artifact] = field(default_factory=list)

    def to_yaml(self, ctx: Host) -> Yaml:
        res: Yaml = {}

        if len(self.matrix) != 0 or self.targets is not None:
            res["strategy"] = {"fail-fast": False}
            res["strategy"]["matrix"] = {}
            for name, values in self.matrix.items():
                res["strategy"]["matrix"][name] = list(values)
            if self.targets is not None:
                res["strategy"]["matrix"]["target"] = self.targets.to_yaml(ctx)

        if len(self.needs) != 0:
            res["needs"] = list(self.needs)

        res["name"] = self.name + " " + ctx.__name__
        res["runs-on"] = ctx.runner

        if len(ctx.env) != 0:
            res["env"] = dict(ctx.env)

        if ctx.shell is not None:
            res["defaults"] = {"run": {"shell": ctx.shell}}

        res["steps"] = [Checkout(self.repo).to_yaml(ctx)]

        match self.kind:
            case "python":
                res["steps"].extend(step.to_yaml(ctx) for step in ctx.setup_python())
            case "ocaml":
                res["steps"].extend(step.to_yaml(ctx) for step in ctx.setup_ocaml())

        for i in self.inputs:
            res["steps"].append(DownloadArtifact(i).to_yaml(ctx))

        res["steps"].extend(
            (st for st in (s.to_yaml(ctx) for s in self.steps) if st is not None)
        )

        for o in self.outputs:
            res["steps"].append(UploadArtifact(o).to_yaml(ctx))

        return res
