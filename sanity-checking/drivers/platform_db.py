from e3.platform_db import PlatformDBPlugin

class PlatDB(PlatformDBPlugin):
    def update_db(self) -> None:
        self.cpu_info.update(
            {
                "xtensa": {"endian": "little", "bits": 32},
                "aarch64": {"endian": "little", "bits": 64},
                "riscv32": {"endian": "little", "bits": 32},
                "riscv64": {"endian": "little", "bits": 64},
                "x86_64": {"endian": "little", "bits": 64},
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
                "xtensa-esp32-elf": {"cpu": "xtensa", "os": "none", "is_hie": True},
                "aarch64-elf": {"cpu": "aarch64", "os": "none", "is_hie": True},
                "aarch64-unknown-elf": {"cpu": "aarch64", "os": "none", "is_hie": True},
                "riscv32-elf": {"cpu": "riscv32", "os": "none", "is_hie": True},
                "riscv64-elf": {"cpu": "riscv64", "os": "none", "is_hie": True},
                "riscv32-unknown-elf": {"cpu": "riscv32", "os": "none", "is_hie": True},
                "riscv64-unknown-elf": {"cpu": "riscv64", "os": "none", "is_hie": True},
                "x86_64-elf": {"cpu": "x86_64", "os": "none", "is_hie": True},
                "x86_64-unknown-elf": {"cpu": "x86_64", "os": "none", "is_hie": True},
            }
        )

        self.build_targets.update(
            {
                "aarch64-darwin": {"name": "aarch64-apple-darwin%(os_version)s"},
                "xtensa-esp32-elf": {"name": "xtensa-esp32-elf"},
                "aarch64-elf": {"name": "aarch64-elf"},
                "aarch64-unknown-elf": {"name": "aarch64-unknown-elf"},
                "riscv32-elf": {"name": "riscv32-elf"},
                "riscv64-elf": {"name": "riscv64-elf"},
                "riscv32-unknown-elf": {"name": "riscv32-unknown-elf"},
                "riscv64-unknown-elf": {"name": "riscv64-unknown-elf"},
                "x86_64-elf": {"name": "x86_64-elf"},
                "x86_64-unknown-elf": {"name": "x86_64-unknown-elf"},

            }
        )
