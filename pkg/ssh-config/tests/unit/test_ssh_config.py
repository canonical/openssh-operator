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

"""Unit tests for the ``charmed-openssh-ssh-config-interface`` package."""

import ops
import pytest
from charmed_openssh_ssh_config_interface import (
    SSHConfigData,
    SSHConfigProvider,
    SSHConfigRequirer,
)
from ops import testing

SSH_CONFIG_INTEGRATION_NAME = "ssh-config"
EXAMPLE_SSH_CONFIG = SSHConfigData(ssh_config="AuthorizedKeysCommand /usr/bin/sss_ssh_authorizedkeys\n")


class _MockProviderCharm(ops.CharmBase):
    """Mock charm used to test ``SSHConfigProvider``."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        self._ssh_config = SSHConfigProvider(self, SSH_CONFIG_INTEGRATION_NAME)
        framework.observe(
            self.on[SSH_CONFIG_INTEGRATION_NAME].relation_created,
            self._on_relation_created,
        )

    def _on_relation_created(self, event: ops.RelationCreatedEvent) -> None:
        self._ssh_config.set_config_data(
            EXAMPLE_SSH_CONFIG, integration_id=event.relation.id
        )


@pytest.fixture(scope="function")
def provider_ctx() -> testing.Context[_MockProviderCharm]:
    """Return a test context for the provider side."""
    return testing.Context(
        _MockProviderCharm,
        meta={
            "name": "ssh-config-provider",
            "provides": {SSH_CONFIG_INTEGRATION_NAME: {"interface": "ssh_config"}},
        },
    )


class TestSSHConfigProvider:
    """Tests for ``SSHConfigProvider``."""

    @pytest.mark.parametrize("leader", [pytest.param(True, id="leader"), pytest.param(False, id="not-leader")])
    def test_set_config_data(self, provider_ctx: testing.Context, leader: bool) -> None:
        """Data is written to the app databag only when the unit is leader."""
        relation = testing.Relation(
            endpoint=SSH_CONFIG_INTEGRATION_NAME,
            interface="ssh_config",
            remote_app_name="requirer",
        )
        state_in = testing.State(leader=leader, relations={relation})
        state_out = provider_ctx.run(
            provider_ctx.on.relation_created(relation), state_in
        )

        rel = state_out.get_relation(relation.id)
        if leader:
            assert "ssh_config" in rel.local_app_data


class TestSSHConfigRequirer:
    """Tests for ``SSHConfigRequirer``."""

    def test_event_source_is_registered(self) -> None:
        """The custom event sources are registered on the requirer."""
        assert hasattr(SSHConfigRequirer.on, "ssh_config_ready")
        assert hasattr(SSHConfigRequirer.on, "ssh_config_disconnected")
