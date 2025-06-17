from abc import ABC, abstractmethod
from dataclasses import dataclass

import yaml


class CustomDumper(yaml.SafeDumper):
    def represent_str(self, data: str) -> yaml.ScalarNode:
        if "\n" in data:
            return self.represent_scalar("tag:yaml.org,2002:str", data, style="|")  # type: ignore #
        return super().represent_str(data)


CustomDumper.add_representer(str, CustomDumper.represent_str)


type Yaml = bool | int | float | str | list[Yaml] | dict[str, Yaml] | None


class Yamlable[Context](ABC):
    @abstractmethod
    def to_yaml(self, ctx: Context) -> Yaml:
        pass

    def dump(self, ctx: Context) -> str:
        return yaml.dump(
            self.to_yaml(ctx),
            Dumper=CustomDumper,
            width=200,
            sort_keys=False,
            default_flow_style=False,
        )


@dataclass
class RawStep(Yamlable[type["HostOs"]]):
    name: str
    command: list[str] | None

    def to_yaml(self, ctx: type["HostOs"]) -> Yaml:
        return {
            "name": self.name,
            "run": "\n".join(self.command if self.command is not None else []),
        }


class HostOs:
    runner: str
    env: dict[str, str] = {}
    shell: str | None = None

    workdir: str = "GNAT-FSF-builds"
    e3_core_version: str = "22.1.0"
    python_version: str = "3.12"
    ocaml_version: str = "4.14.2"

    @classmethod
    def native_path(cls, path: str) -> str:
        return path

    @classmethod
    def command(cls, cmd: list[str]) -> str:
        return "\n".join(cmd)

    @classmethod
    def setup_python(cls) -> list[RawStep]:
        raise NotImplementedError

    @classmethod
    def setup_ocaml(cls) -> list[RawStep]:
        raise NotImplementedError


type Host = type[HostOs]
