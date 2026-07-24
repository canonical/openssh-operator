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

"""Shared unit test fixtures for the ``openssh`` charm."""

from unittest.mock import Mock

import pytest


class _MockOpenSSH:
    """Mock of ``OpenSSHManager`` for use in unit tests."""

    def __init__(self) -> None:
        self.install = Mock()
        self.is_installed = Mock(return_value=True)
        self.version = Mock(return_value="9.9p1-3ubuntu1")

        self.config = Mock()
        self.config.files = []
        self.config.remove = Mock()
        self.config.write = Mock()
        self.config.validate = Mock()

        self.service = Mock()
        self.service.reload = Mock()
        self.service.stop = Mock()
        self.service.is_active = Mock(return_value=True)

        self._log_level: str = "info"
        self._port: int | None = None

    @property
    def log_level(self) -> str | None:
        return self._log_level

    @log_level.setter
    def log_level(self, value: str) -> None:
        self._log_level = value

    @property
    def port(self) -> int | None:
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        self._port = value

    @port.deleter
    def port(self) -> None:
        self._port = None


@pytest.fixture(scope="function")
def mock_openssh(monkeypatch: pytest.MonkeyPatch) -> _MockOpenSSH:
    """Mock ``OpenSSHManager`` for unit tests.

    Returns:
        An instance of ``_MockOpenSSH`` with mock attributes mirroring
        the public surface of ``OpenSSHManager``.
    """
    mock_instance = _MockOpenSSH()
    monkeypatch.setattr("charm.OpenSSHManager", lambda: mock_instance)
    return mock_instance
