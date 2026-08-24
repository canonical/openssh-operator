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

"""Observe ``ssh-config`` integration events."""

import logging
from typing import TYPE_CHECKING

import ops
from charmed_hpc_libs.ops import Observer, StopCharm
from charmed_openssh_ssh_config_interface import (
    SSHConfigDisconnectedEvent,
    SSHConfigReadyEvent,
    SSHConfigRequirer,
)

from openssh import OpenSSHOpsError
from state import refresh

if TYPE_CHECKING:
    from charm import OpenSSHCharm

_logger = logging.getLogger(__name__)


class SSHConfigObserver(Observer):
    """Observe ``ssh-config`` integration events."""

    def __init__(self, charm: "OpenSSHCharm") -> None:
        super().__init__(charm)

        self._ssh_config = SSHConfigRequirer(self.charm, "ssh-config")
        self.framework.observe(
            self._ssh_config.on.ssh_config_ready,
            self._on_ssh_config_provider_ready,
        )
        self.framework.observe(
            self._ssh_config.on.ssh_config_disconnected,
            self._on_ssh_config_provider_disconnected,
        )

    @refresh
    def _on_ssh_config_provider_ready(self, event: SSHConfigReadyEvent) -> None:
        """Apply custom SSH configuration from the provider."""
        data = self._ssh_config.get_config_data(event.relation.id)
        if data is None:
            return

        filename = self._make_filename(event.relation)
        self.charm.openssh.config.write(filename, f"{data.ssh_config}\n")

        try:
            self.charm.openssh.config.validate()
        except OpenSSHOpsError:
            self.charm.openssh.config.remove(filename)
            raise StopCharm(
                ops.BlockedStatus(
                    "Invalid SSH configuration received from "
                    f"'{event.relation.app}'. "
                    "See `juju debug-log` for details"
                )
            )

        self.charm.openssh.service.reload()

    @refresh
    def _on_ssh_config_provider_disconnected(self, event: SSHConfigDisconnectedEvent) -> None:
        """Remove custom SSH configuration when the provider departs."""
        filename = self._make_filename(event.relation)
        self.charm.openssh.config.remove(filename)
        self.charm.openssh.service.reload()

    @staticmethod
    def _make_filename(integration: ops.Relation) -> str:
        """Generate a configuration filename from relation metadata."""
        return f"{integration.name}-{integration.id}-{integration.app}.conf"
