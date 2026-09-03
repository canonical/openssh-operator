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

import subprocess
from functools import cached_property
from pathlib import Path

from charmed_hpc_libs.errors import Error
from charmed_hpc_libs.ops import AptLifecycleManager, SystemctlServiceManager

from constants import CONFIG_FILE_PREFIX, CONFIG_FILE_SUFFIX


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
        """Get the list of custom SSH configurations managed by this charm."""
        try:
            return [
                p
                for p in self.path.iterdir()
                if p.is_file() and p.stem.startswith(CONFIG_FILE_PREFIX)
            ]
        except OSError:
            return []

    def read(self, slug: str) -> str:
        """Read the content of a configuration file under ``/etc/ssh/ssh_config.d``.

        Args:
            slug: Slug of the file to read.

        Raises:
            OpenSSSOpsError: Raised if the configuration file cannot be read.
        """
        file = self.path / self._make_filename(slug)
        try:
            return file.read_text()
        except OSError as e:
            raise OpenSSHOpsError(f"failed to read '{file}'") from e

    def write(self, slug: str, content: str) -> None:
        """Write a configuration file under ``/etc/ssh/ssh_config.d``.

        Args:
            slug: Slug of file to write into.
            content: Content to write into the file.

        Raises:
            OpenSSHOpsError: Raised if the configuration file cannot be written.
        """
        file = self.path / self._make_filename(slug)
        self.path.mkdir(parents=True, exist_ok=True)
        try:
            file.write_text(content)
        except OSError as e:
            raise OpenSSHOpsError(f"failed to write '{file}'") from e

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

    def delete(self, slug: str) -> None:
        """Delete a configuration file from ``/etc/ssh/ssh_config.d``.

        Args:
            slug: Slug of the configuration file to remove.

        Raises:
            OpenSSHOpsError: Raised if the configuration file cannot be removed.
        """
        file = self.path / self._make_filename(slug)
        try:
            file.unlink()
        except OSError as e:
            raise OpenSSHOpsError(f"failed to delete '{file}'") from e

    def clear(self) -> None:
        """Delete all custom SSH configuration files managed by this charm.

        Raises:
            OpenSSHOpsError: Raised if a configuration file cannot be removed.
        """
        for file in self.files:
            try:
                file.unlink()
            except OSError as e:
                raise OpenSSHOpsError(f"failed to delete '{file}'") from e

    @staticmethod
    def _make_filename(slug: str) -> str:
        """Make a filename for configuration overrides managed by the OpenSSH charm.

        Args:
            slug: Slug to insert before the ``.conf`` suffix.
        """
        return f"{CONFIG_FILE_PREFIX}{slug}{CONFIG_FILE_SUFFIX}"


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
        try:
            content = self.config.read("log-level")
        except OpenSSHOpsError:
            return None

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
        self.config.write("log-level", f"LogLevel {value}\n")

    @property
    def port(self) -> int | None:
        """Get the port number the ``ssh`` service communicates on."""
        try:
            content = self.config.read("port")
        except OpenSSHOpsError:
            return None

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
        self.config.write("port", f"Port {value}\n")
