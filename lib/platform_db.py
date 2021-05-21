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

        self.platform_info.update(
            {
                "riscv32-elf": {"cpu": "riscv32", "os": "none", "is_hie": True},
                "riscv64-elf": {"cpu": "riscv64", "os": "none", "is_hie": True},
                "riscv32-unknown-elf": {"cpu": "riscv32", "os": "none", "is_hie": True},
                "riscv64-unknown-elf": {"cpu": "riscv64", "os": "none", "is_hie": True},
            }
        )

        self.build_targets.update(
            {
                "riscv32-elf": {"name": "riscv32-elf"},
                "riscv64-elf": {"name": "riscv64-elf"},
                "riscv32-unknown-elf": {"name": "riscv32-unknown-elf"},
                "riscv64-unknown-elf": {"name": "riscv64-unknown-elf"},

            }
        )
