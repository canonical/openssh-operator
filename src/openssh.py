# Copyright 2026 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Manage and operate the ``ssh`` service."""

import logging
import subprocess
from functools import cached_property
from pathlib import Path

from charmed_hpc_libs.errors import Error
from charmed_hpc_libs.ops import AptLifecycleManager, SystemctlServiceManager

logger = logging.getLogger(__name__)


class OpenSSHOpsError(Error):
    """Exception raised when an ``ssh`` server operation has failed."""


class OpenSSHConfigManager:
    """Manage configuration files in the ``ssh`` server configuration directory."""

    @property
    def path(self):
        """Path to the ``ssh`` server configuration directory."""
        return Path("/etc/ssh/ssh_config.d")

    @property
    def files(self) -> list[Path]:
        """List of files in the ``ssh`` server configuration directory."""
        try:
            return [p for p in self.path.iterdir() if p.is_file()]
        except OSError:
            return []

    def write(self, name: str, content: str) -> None:
        """Write a configuration file under ``/etc/ssh/ssh_config.d``.

        Args:
            name: Name of the configuration file to write.
            content: Content to write into the file.

        Raises:
            OpenSSHOpsError: Raised if the configuration file cannot be written.
        """
        file = self.path / name
        self.path.mkdir(parents=True, exist_ok=True)
        try:
            file.write_text(content)
        except OSError as e:
            raise OpenSSHOpsError(f"failed to write '{file}'. reason: {e}") from e

    def validate(self) -> None:
        """Validate the ``ssh`` server configuration.

        Runs ``sshd -t`` to test the configuration.

        Raises:
            OpenSSHOpsError:
                Raised if the ``sshd`` binary is not found on PATH or
                if the server configuration is invalid.
        """
        try:
            result = subprocess.run(["sshd", "-t"], capture_output=True, text=True, check=False)
        except FileNotFoundError as e:
            raise OpenSSHOpsError(f"failed to run 'sshd -t'. reason: {e}") from e

        if result.returncode != 0:
            raise OpenSSHOpsError(f"invalid ssh server configuration:\n{result.stderr.strip()}")

    def remove(self, name: str) -> None:
        """Remove a configuration file from ``/etc/ssh/ssh_config.d``.

        Args:
            name: Name of the configuration file to remove.

        Raises:
            OpenSSHOpsError: Raised if the configuration file cannot be removed.
        """
        file = self.path / name
        try:
            file.unlink(missing_ok=True)
        except OSError as e:
            raise OpenSSHOpsError(f"failed to remove '{file}'. reason: {e}") from e


class OpenSSHManager(AptLifecycleManager):
    """Manage the ``ssh`` service of a machine."""

    def __init__(self) -> None:
        super().__init__("openssh-server")

    @cached_property
    def config(self) -> OpenSSHConfigManager:
        """Get the configuration manager for the ``ssh`` service."""
        return OpenSSHConfigManager()

    @cached_property
    def service(self) -> SystemctlServiceManager:
        """Get the service manager for ``ssh`` service."""
        return self._ops_manager.service_manager_for("ssh")

    @property
    def log_level(self) -> str | None:
        """Get the log level of the ``ssh`` service."""
        log_level_file = self.config.path / "log-level.conf"
        if not log_level_file.is_file():
            return None

        content = log_level_file.read_text().strip()
        parts = content.split()
        if len(parts) >= 2 and parts[0] == "LogLevel":
            return parts[1]

        return None

    @log_level.setter
    def log_level(self, value: str) -> None:
        """Set the log level of the ``ssh`` service.

        Args:
            value: The log level to set.
        """
        self.config.write("log-level.conf", f"LogLevel {value}\n")

    @property
    def port(self) -> int | None:
        """Get the port number the ``ssh`` service communicates on."""
        port_file = self.config.path / "port-override.conf"
        if not port_file.is_file():
            return None

        content = port_file.read_text().strip()
        parts = content.split()
        if len(parts) >= 2 and parts[0] == "Port":
            return int(parts[1])

        return None

    @port.setter
    def port(self, value: int) -> None:
        """Set the port number the ``ssh`` service communicates on.

        Args:
            value: The port number to set.
        """
        self.config.write("port-override.conf", f"Port {value}\n")

    @port.deleter
    def port(self) -> None:
        """Unset the port number, restoring the default.

        Removes the ``port-override.conf`` configuration file.
        """
        self.config.remove("port-override.conf")
