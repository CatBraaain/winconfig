import re

import pytest
from pexpect.popen_spawn import PopenSpawn


class PowershellProcess:
    process: PopenSpawn
    left_prompt: re.Pattern = re.compile(rb"PS .*> ")

    def __init__(self) -> None:
        self.process = PopenSpawn(
            "powershell -NoExit -Command 'chcp 65001'", encoding="utf-8"
        )
        self.process.expect(self.left_prompt, timeout=3)

    def send(self, cmd: str, timeout: int = 10) -> str:
        self.process.sendline(cmd.replace("\n", ""))
        self.process.expect(self.left_prompt, timeout=timeout)

        output = self.process.before or ""
        return "\n".join(output.splitlines()[1:]).strip()


@pytest.fixture(scope="session")
def powershell() -> PowershellProcess:
    return PowershellProcess()
