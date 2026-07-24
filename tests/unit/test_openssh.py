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

"""Unit tests for the ``openssh`` workload manager module."""

import subprocess
from unittest.mock import Mock

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pyfakefs.helpers import set_gid, set_uid
from pytest_mock import MockerFixture

from openssh import (
    OpenSSHConfigManager,
    OpenSSHManager,
    OpenSSHOpsError,
)


@pytest.fixture(autouse=True)
def _set_root(fs: FakeFilesystem) -> None:
    """Set the fake filesystem uid/gid to 0 (root) for config operations."""
    set_uid(0)
    set_gid(0)


@pytest.fixture(scope="function")
def mock_run(mocker: MockerFixture) -> Mock:
    """Mock ``subprocess.run`` to return a successful completed process."""
    completed = subprocess.CompletedProcess([], returncode=0, stdout="", stderr="")
    return mocker.patch("subprocess.run", return_value=completed)


class TestOpenSSHConfigManager:
    """Tests for ``OpenSSHConfigManager``."""

    def test_write_and_files(self, fs: FakeFilesystem) -> None:
        """Writing a config file makes it appear in ``files``."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        manager.write("test.conf", "SomeDirective value\n")

        assert "test.conf" in [f.name for f in manager.files]
        file_path = config_dir / "test.conf"
        assert file_path.read_text() == "SomeDirective value\n"

    def test_write_creates_directory(self, fs: FakeFilesystem) -> None:
        """Writing a config file creates the directory tree if needed."""
        manager = OpenSSHConfigManager()
        manager.write("extra.conf", "# comment\n")

        file_path = manager.path / "extra.conf"
        assert file_path.exists()
        assert file_path.read_text() == "# comment\n"

    def test_validate_success(self, mock_run: Mock) -> None:
        """``validate`` passes when ``sshd -t`` exits with code 0."""
        manager = OpenSSHConfigManager()
        manager.validate()

        mock_run.assert_called_once_with(
            ["sshd", "-t"], capture_output=True, text=True, check=False
        )

    def test_validate_failure(self, mock_run: Mock) -> None:
        """``validate`` raises ``OpenSSHOpsError`` when ``sshd -t`` fails."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=1, stdout="", stderr="bad config\n"
        )

        manager = OpenSSHConfigManager()
        with pytest.raises(OpenSSHOpsError, match="invalid ssh server configuration"):
            manager.validate()

    def test_remove(self, fs: FakeFilesystem) -> None:
        """Removing a config file makes it disappear from ``files``."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        manager.write("removable.conf", "data\n")
        assert "removable.conf" in [f.name for f in manager.files]

        manager.remove("removable.conf")
        assert "removable.conf" not in [f.name for f in manager.files]

    def test_remove_idempotent(self, fs: FakeFilesystem) -> None:
        """Removing a non-existent file does not raise."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        manager.remove("nonexistent.conf")

    def test_files_empty_directory(self, fs: FakeFilesystem) -> None:
        """``files`` returns an empty list when directory is empty."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        assert manager.files == []

    def test_files_directory_does_not_exist(self) -> None:
        """``files`` returns an empty list when directory is absent."""
        manager = OpenSSHConfigManager()
        assert manager.files == []


class TestOpenSSHManager:
    """Tests for ``OpenSSHManager``."""

    def test_log_level_get_none_when_not_set(self) -> None:
        """``log_level`` returns ``None`` when no ``log-level.conf`` exists."""
        manager = OpenSSHManager()
        assert manager.log_level is None

    def test_log_level_set_and_get(self, fs: FakeFilesystem) -> None:
        """Setting ``log_level`` writes a config file and is readable."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHManager()
        manager.log_level = "debug"
        assert manager.log_level == "debug"

        log_file = config_dir / "log-level.conf"
        assert log_file.read_text() == "LogLevel debug\n"

    def test_log_level_is_not_deletable(self) -> None:
        """``log_level`` property does not support deletion."""
        manager = OpenSSHManager()
        prop = type(manager).__dict__["log_level"]
        assert prop.fdel is None

    def test_port_get_none_when_not_set(self) -> None:
        """``port`` returns ``None`` when no ``port-override.conf`` exists."""
        manager = OpenSSHManager()
        assert manager.port is None

    def test_port_set_and_get(self, fs: FakeFilesystem) -> None:
        """Setting ``port`` writes a config file and is readable."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHManager()
        manager.port = 2222
        assert manager.port == 2222

        port_file = config_dir / "port-override.conf"
        assert port_file.read_text() == "Port 2222\n"

    def test_port_delete(self, fs: FakeFilesystem) -> None:
        """Deleting ``port`` removes the override file."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHManager()
        manager.port = 2222
        assert "port-override.conf" in [f.name for f in manager.config.files]

        del manager.port
        assert manager.port is None
        assert "port-override.conf" not in [f.name for f in manager.config.files]

    def test_port_delete_when_not_set(self) -> None:
        """Deleting ``port`` when not set does not raise."""
        manager = OpenSSHManager()
        del manager.port
