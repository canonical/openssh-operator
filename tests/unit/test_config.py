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

"""Unit tests for the ``config`` module."""

import logging
from typing import Any

import pytest
from pydantic import ValidationError

from config import CharmConfigManager


class TestCharmConfigManager:
    """Tests for ``CharmConfigManager``."""

    def test_valid_defaults(self) -> None:
        """Accept the default ``port`` and ``log_level`` values."""
        config = CharmConfigManager(port=22, log_level="info")
        assert config.port == 22
        assert config.log_level == "info"

    # -- port -----------------------------------------------------------------

    @pytest.mark.parametrize("port", [22, 1024, 65535])
    def test_valid_port_values(self, port: int) -> None:
        """Accept port ``22`` and ports in the range 1024–65535."""
        config = CharmConfigManager(port=port, log_level="info")
        assert config.port == port

    @pytest.mark.parametrize("port", [0, 23, 1023, 65536, 99999, -1])
    def test_invalid_port_values(self, port: int) -> None:
        """Reject port values outside the valid ranges."""
        with pytest.raises(ValidationError, match="port"):
            CharmConfigManager(port=port, log_level="info")

    # -- log_level -------------------------------------------------------------

    @pytest.mark.parametrize("level", ["quiet", "fatal", "error", "info", "verbose"])
    def test_valid_log_level_values(self, level: Any) -> None:
        """Accept the standard log levels."""
        config = CharmConfigManager(port=22, log_level=level)
        assert config.log_level == level

    @pytest.mark.parametrize("level", ["WARN", "trace", "", "none"])
    def test_invalid_log_level_values(self, level: Any) -> None:
        """Reject unrecognised log levels."""
        with pytest.raises(ValidationError, match="log_level"):
            CharmConfigManager(port=22, log_level=level)

    @pytest.mark.parametrize("level", ["debug", "debug1", "debug2", "debug3"])
    def test_debug_log_level_warns(self, level: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Setting a debug log level logs a warning message."""
        caplog.set_level(logging.WARNING)
        CharmConfigManager(port=22, log_level=level)
        assert "should not be used in production" in caplog.text

    def test_non_debug_log_level_does_not_warn(self, caplog: pytest.LogCaptureFixture) -> None:
        """Setting a non-debug log level does not log a warning."""
        caplog.set_level(logging.WARNING)
        CharmConfigManager(port=22, log_level="info")
        assert "should not be used" not in caplog.text
