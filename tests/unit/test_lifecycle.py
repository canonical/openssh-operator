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

"""Unit tests for the lifecycle observer."""

import ops.testing
import pytest

from charm import OpenSSHCharm

_CONFIG_SCHEMA = {
    "options": {
        "log-level": {"type": "string", "default": "info"},
        "port": {"type": "int", "default": 22},
    },
}


@pytest.fixture(scope="function")
def ctx(mock_openssh) -> ops.testing.Context[OpenSSHCharm]:
    """Return a test context with a mocked ``OpenSSHManager``."""
    return ops.testing.Context(
        OpenSSHCharm,
        config=_CONFIG_SCHEMA,
        meta={
            "requires": {"juju-info": {"interface": "juju-info", "scope": "container"}},
            "provides": {"ssh-config": {"interface": "ssh_config"}},
        },
    )


class TestLifecycleObserver:
    """Tests for ``LifecycleObserver``."""

    def test_install(self, ctx: ops.testing.Context, mock_openssh) -> None:
        """Install ``openssh-server`` when it is not already present."""
        mock_openssh.is_installed.return_value = False

        state_out = ctx.run(ctx.on.install(), ops.testing.State())

        mock_openssh.install.assert_called_once_with(update=True)
        assert state_out.workload_version == mock_openssh.version()
        assert state_out.unit_status == ops.ActiveStatus()

    def test_install_idempotent(self, ctx: ops.testing.Context, mock_openssh) -> None:
        """Do not reinstall when ``openssh-server`` is already present."""
        mock_openssh.is_installed.return_value = True

        state_out = ctx.run(ctx.on.install(), ops.testing.State())

        mock_openssh.install.assert_not_called()
        assert state_out.workload_version == mock_openssh.version()
        assert state_out.unit_status == ops.ActiveStatus()

    def test_config_changed_default_port(self, ctx: ops.testing.Context, mock_openssh) -> None:
        """Remove the port override when the default port is configured."""
        mock_openssh.service.is_active.return_value = True

        state_out = ctx.run(ctx.on.config_changed(), ops.testing.State())

        assert mock_openssh.port is None
        assert mock_openssh.log_level == "info"
        mock_openssh.service.reload.assert_called_once()
        assert state_out.unit_status == ops.ActiveStatus()

    def test_config_changed_custom_port(self, ctx: ops.testing.Context, mock_openssh) -> None:
        """Set a port override and reload the service."""
        mock_openssh.service.is_active.return_value = True

        state_in = ops.testing.State(config={"port": 2222, "log-level": "info"})
        state_out = ctx.run(ctx.on.config_changed(), state_in)

        assert mock_openssh.port == 2222
        mock_openssh.service.reload.assert_called_once()
        assert state_out.unit_status == ops.ActiveStatus()
        assert any(p.port == 2222 for p in state_out.opened_ports)

    def test_config_changed_debug_log_level(self, ctx: ops.testing.Context, mock_openssh) -> None:
        """Custom log levels are applied to the workload."""
        mock_openssh.service.is_active.return_value = True

        state_in = ops.testing.State(config={"port": 22, "log-level": "debug"})
        state_out = ctx.run(ctx.on.config_changed(), state_in)

        assert mock_openssh.log_level == "debug"
        mock_openssh.service.reload.assert_called_once()
        assert state_out.unit_status == ops.ActiveStatus()

    def test_remove(self, ctx: ops.testing.Context, mock_openssh) -> None:
        """Remove custom config files and reload, but never stop."""
        mock_openssh.config.files = [
            type("FakePath", (), {"name": "foo.conf"})(),
            type("FakePath", (), {"name": "bar.conf"})(),
        ]
        mock_openssh.service.is_active.return_value = True

        ctx.run(ctx.on.remove(), ops.testing.State())

        mock_openssh.config.remove.assert_any_call("foo.conf")
        mock_openssh.config.remove.assert_any_call("bar.conf")
        mock_openssh.service.reload.assert_called_once()
        mock_openssh.service.stop.assert_not_called()
