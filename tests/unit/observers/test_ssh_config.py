#!/usr/bin/env python3
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

"""Unit tests for the ``SSHConfigObserver`` integration observer."""

import json

import ops
import pytest
from charmed_openssh_ssh_config_interface import SSHConfigRequirer
from ops import testing

from charm import OpenSSHCharm
from constants import SSH_CONFIG_INTEGRATION_NAME
from openssh import OpenSSHOpsError

_SSH_CONFIG = "AuthorizedKeysCommand /usr/bin/sss_ssh_authorizedkeys"


class TestSSHConfigObserver:
    """Test the ``ssh-config`` integration event observer."""

    def test_ssh_config_provider_ready(
        self,
        mock_charm: testing.Context[OpenSSHCharm],
        mock_openssh,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test the ``_on_ssh_config_provider_ready`` event handler."""
        integration = testing.Relation(
            endpoint=SSH_CONFIG_INTEGRATION_NAME,
            interface="ssh_config",
            id=51,
            remote_app_name="sssd",
            remote_app_data={"ssh_config": json.dumps(_SSH_CONFIG)},
        )

        # Test `ssh_config_ready` hook when the provider publishes SSH configuration data.
        mock_openssh.service.is_active.return_value = True
        with mock_charm(
            mock_charm.on.relation_changed(integration),
            testing.State(relations={integration}),
        ) as manager:
            state = manager.run()
            assert state.unit_status == ops.ActiveStatus()
            mock_openssh.config.write.assert_called_once_with(
                f"{SSH_CONFIG_INTEGRATION_NAME}-51-sssd", f"{_SSH_CONFIG}\n"
            )
            mock_openssh.config.validate.assert_called_once()
            mock_openssh.service.reload.assert_called_once()

        # Test `ssh_config_ready` hook when the configuration received from the
        # provider is invalid.
        mock_openssh.config.write.reset_mock()
        mock_openssh.config.validate.reset_mock()
        mock_openssh.service.reload.reset_mock()
        mock_openssh.config.validate.side_effect = OpenSSHOpsError(
            "invalid ssh server configuration"
        )

        with mock_charm(
            mock_charm.on.relation_changed(integration),
            testing.State(relations={integration}),
        ) as manager:
            state = manager.run()
            assert state.unit_status == ops.BlockedStatus(
                "Invalid SSH configuration received from 'sssd'. See `juju debug-log` for details"
            )
            mock_openssh.config.delete.assert_called_once_with(
                f"{SSH_CONFIG_INTEGRATION_NAME}-51-sssd"
            )
            mock_openssh.service.reload.assert_not_called()

        # Test `ssh_config_ready` hook when the provider has not published data yet.
        integration = testing.Relation(
            endpoint=SSH_CONFIG_INTEGRATION_NAME,
            interface="ssh_config",
            id=51,
            remote_app_name="sssd",
        )
        mock_openssh.config.write.reset_mock()
        mock_openssh.config.delete.reset_mock()

        with mock_charm(
            mock_charm.on.relation_changed(integration),
            testing.State(relations={integration}),
        ) as manager:
            manager.run()
            mock_openssh.config.write.assert_not_called()
            mock_openssh.service.reload.assert_not_called()

        # Test `ssh_config_ready` hook when configuration data cannot be loaded.
        # This is a defensive path: the event only fires when the provider databag
        # is populated, so the loader is patched to simulate the data becoming
        # unavailable.
        monkeypatch.setattr(
            SSHConfigRequirer, "get_config_data", lambda self, integration_id=None: None
        )

        with mock_charm(
            mock_charm.on.relation_changed(integration),
            testing.State(relations={integration}),
        ) as manager:
            manager.run()
            mock_openssh.config.write.assert_not_called()
            mock_openssh.service.reload.assert_not_called()

    def test_ssh_config_provider_disconnected(
        self, mock_charm: testing.Context[OpenSSHCharm], mock_openssh
    ) -> None:
        """Test the ``_on_ssh_config_provider_disconnected`` event handler."""
        ssh_config_relation = testing.Relation(
            endpoint=SSH_CONFIG_INTEGRATION_NAME,
            interface="ssh_config",
            id=51,
            remote_app_name="sssd",
            remote_app_data={"ssh_config": json.dumps(_SSH_CONFIG)},
        )

        # Test `ssh_config_disconnected` hook when the provider departs. The
        # configuration file received from the provider is deleted and the `ssh`
        # service is reloaded.
        mock_openssh.service.is_active.return_value = True
        with mock_charm(
            mock_charm.on.relation_broken(ssh_config_relation),
            testing.State(relations={ssh_config_relation}),
        ) as manager:
            state = manager.run()
            assert state.unit_status == ops.ActiveStatus()
            mock_openssh.config.delete.assert_called_once_with(
                f"{SSH_CONFIG_INTEGRATION_NAME}-51-sssd"
            )
            mock_openssh.service.reload.assert_called_once()
