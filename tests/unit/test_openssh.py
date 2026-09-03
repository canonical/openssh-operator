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
        manager.write("test", "SomeDirective value\n")

        assert "99-charmed-openssh-test.conf" in [f.name for f in manager.files]
        file_path = config_dir / "99-charmed-openssh-test.conf"
        assert file_path.read_text() == "SomeDirective value\n"

    def test_write_creates_directory(self, fs: FakeFilesystem) -> None:
        """Writing a config file creates the directory tree if needed."""
        manager = OpenSSHConfigManager()
        manager.write("extra", "# comment\n")

        file_path = manager.path / "99-charmed-openssh-extra.conf"
        assert file_path.exists()
        assert file_path.read_text() == "# comment\n"

    def test_make_filename(self) -> None:
        """Slugs are expanded into the charm's managed filename scheme."""
        assert OpenSSHConfigManager._make_filename("test") == "99-charmed-openssh-test.conf"

    def test_read(self, fs: FakeFilesystem) -> None:
        """Reading a config file returns its content."""
        manager = OpenSSHConfigManager()
        manager.write("readable", "SomeDirective value\n")

        assert manager.read("readable") == "SomeDirective value\n"

    def test_read_missing_file_raises(self, fs: FakeFilesystem) -> None:
        """Reading a non-existent config file raises ``OpenSSHOpsError``."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        with pytest.raises(OpenSSHOpsError, match="failed to read"):
            manager.read("nonexistent")

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

    def test_delete(self, fs: FakeFilesystem) -> None:
        """Deleting a config file makes it disappear from ``files``."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        manager.write("deletable", "data\n")
        assert "99-charmed-openssh-deletable.conf" in [f.name for f in manager.files]

        manager.delete("deletable")
        assert "99-charmed-openssh-deletable.conf" not in [f.name for f in manager.files]

    def test_delete_missing_file_raises(self, fs: FakeFilesystem) -> None:
        """Deleting a non-existent config file raises ``OpenSSHOpsError``."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        with pytest.raises(OpenSSHOpsError, match="failed to delete"):
            manager.delete("nonexistent")

    def test_clear(self, fs: FakeFilesystem) -> None:
        """Clearing deletes all managed files but leaves others untouched."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        manager.write("log-level", "LogLevel debug\n")
        manager.write("port", "Port 2222\n")
        # Unmanaged files in the directory must not be touched by ``clear``.
        unmanaged = config_dir / "10-unmanaged.conf"
        unmanaged.write_text("Port 23\n")

        manager.clear()

        assert manager.files == []
        assert unmanaged.read_text() == "Port 23\n"

    def test_files_ignores_unmanaged(self, fs: FakeFilesystem) -> None:
        """``files`` only lists configuration files managed by this charm."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHConfigManager()
        manager.write("managed", "data\n")
        (config_dir / "10-unmanaged.conf").write_text("other\n")

        assert [f.name for f in manager.files] == ["99-charmed-openssh-managed.conf"]

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
        """``log_level`` returns ``None`` when no ``99-charmed-openssh-log-level.conf`` exists."""
        manager = OpenSSHManager()
        assert manager.log_level is None

    def test_log_level_set_and_get(self, fs: FakeFilesystem) -> None:
        """Setting ``log_level`` writes a config file and is readable."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHManager()
        manager.log_level = "debug"
        assert manager.log_level == "debug"

        log_file = config_dir / "99-charmed-openssh-log-level.conf"
        assert log_file.read_text() == "LogLevel debug\n"

    def test_log_level_is_not_deletable(self) -> None:
        """``log_level`` property does not support deletion."""
        manager = OpenSSHManager()
        prop = type(manager).__dict__["log_level"]
        assert prop.fdel is None

    def test_port_get_none_when_not_set(self) -> None:
        """``port`` returns ``None`` when no ``99-charmed-openssh-port.conf`` exists."""
        manager = OpenSSHManager()
        assert manager.port is None

    def test_port_set_and_get(self, fs: FakeFilesystem) -> None:
        """Setting ``port`` writes a config file and is readable."""
        config_dir = OpenSSHConfigManager().path
        fs.create_dir(str(config_dir))

        manager = OpenSSHManager()
        manager.port = 2222
        assert manager.port == 2222

        port_file = config_dir / "99-charmed-openssh-port.conf"
        assert port_file.read_text() == "Port 2222\n"
