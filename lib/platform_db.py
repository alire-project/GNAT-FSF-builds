from e3.platform_db import PlatformDBPlugin

class PlatDB(PlatformDBPlugin):
    def update_db(self) -> None:
        self.cpu_info.update(
            {
                "riscv32": {"endian": "little", "bits": 32},
                "riscv64": {"endian": "little", "bits": 64},
            }
        )

        self.os_info.update(
            {
                "none": {
                    "is_bareboard": True,
                    "version": "unknown",
                    "exeext": "",
                    "dllext": "",
                },
            }
        )

        self.host_guess.pop("x86-windows")
        self.host_guess.update(
            {
                "aarch64-darwin": {"os": "Darwin", "cpu": "arm64"},
                "x86_64-windows64": {
                    "os": "Windows",
                    "cpu": "AMD64",
                },
            }
        )

        self.platform_info.update(
            {
                "aarch64-darwin": {"cpu": "aarch64", "os": "darwin", "is_hie": False},
                "riscv32-elf": {"cpu": "riscv32", "os": "none", "is_hie": True},
                "riscv64-elf": {"cpu": "riscv64", "os": "none", "is_hie": True},
                "riscv32-unknown-elf": {"cpu": "riscv32", "os": "none", "is_hie": True},
                "riscv64-unknown-elf": {"cpu": "riscv64", "os": "none", "is_hie": True},
            }
        )

        self.build_targets.update(
            {
                "aarch64-darwin": {"name": "aarch64-apple-darwin%(os_version)s"},
                "riscv32-elf": {"name": "riscv32-elf"},
                "riscv64-elf": {"name": "riscv64-elf"},
                "riscv32-unknown-elf": {"name": "riscv32-unknown-elf"},
                "riscv64-unknown-elf": {"name": "riscv64-unknown-elf"},

            }
        )
