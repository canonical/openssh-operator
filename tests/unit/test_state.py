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

"""Unit tests for the ``state`` module."""

from unittest.mock import Mock

import ops

from state import check_openssh


class TestCheckOpenSSH:
    """Tests for ``check_openssh``."""

    def test_active_when_service_is_running(self) -> None:
        """Return ``ActiveStatus`` when the ``ssh`` service is active."""
        obj = Mock()
        obj.charm.openssh.service.is_active.return_value = True
        status = check_openssh(obj)
        assert status == ops.ActiveStatus()

    def test_waiting_when_service_is_not_running(self) -> None:
        """Return ``WaitingStatus`` when the ``ssh`` service is not active."""
        obj = Mock()
        obj.charm.openssh.service.is_active.return_value = False
        status = check_openssh(obj)
        assert status == ops.WaitingStatus("Waiting for `ssh` server to start")
