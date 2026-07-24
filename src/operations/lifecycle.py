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

"""Observe charm lifecycle events for the ``openssh`` charm."""

import logging
from typing import TYPE_CHECKING

import ops
from charmed_hpc_libs.ops import StopCharm

from openssh import OpenSSHOpsError
from state import OpenSSHObserver, refresh

if TYPE_CHECKING:
    from charm import OpenSSHCharm

_logger = logging.getLogger(__name__)


class LifecycleObserver(OpenSSHObserver):
    """Observe charm lifecycle events."""

    def __init__(self, charm: "OpenSSHCharm") -> None:
        super().__init__(charm)

        self.framework.observe(self.charm.on.install, self._on_install)
        self.framework.observe(self.charm.on.config_changed, self._on_config_changed)
        self.framework.observe(self.charm.on.remove, self._on_remove)

    @refresh
    def _on_install(self, _: ops.InstallEvent) -> None:
        """Install ``openssh-server`` if it is not already present."""
        self.charm.unit.status = ops.MaintenanceStatus("Installing OpenSSH")
        try:
            if not self.charm.openssh.is_installed():
                self.charm.openssh.install(update=True)
            self.charm.unit.set_workload_version(self.charm.openssh.version())
        except OpenSSHOpsError as e:
            _logger.error(e.message)
            raise StopCharm(
                ops.BlockedStatus("Failed to install OpenSSH. See `juju debug-log` for details")
            )

    @refresh
    def _on_config_changed(self, _: ops.ConfigChangedEvent) -> None:
        """Apply configuration changes to the ``ssh`` service."""
        self.charm.openssh.log_level = self.charm.app_config.log_level

        if self.charm.app_config.port == 22:
            del self.charm.openssh.port
        else:
            self.charm.openssh.port = self.charm.app_config.port

        self.charm.unit.open_port("tcp", self.charm.app_config.port)
        self.charm.openssh.service.reload()

    @refresh
    def _on_remove(self, _: ops.RemoveEvent) -> None:
        """Remove custom configuration files and reload ``ssh``.

        The ``ssh`` service **must not** be stopped or uninstalled,
        as ``juju ssh`` depends on a running ``ssh`` service on the machine.
        """
        for file in self.charm.openssh.config.files:
            self.charm.openssh.config.remove(file.name)

        self.charm.openssh.service.reload()
