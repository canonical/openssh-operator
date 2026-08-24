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

"""Integration interface implementation for the ``ssh_config`` interface."""

__all__ = [
    "SSHConfigConnectedEvent",
    "SSHConfigData",
    "SSHConfigDisconnectedEvent",
    "SSHConfigProvider",
    "SSHConfigReadyEvent",
    "SSHConfigRequirer",
]

from typing import Any

import ops
from charmed_hpc_libs.interfaces import Interface
from charmed_hpc_libs.ops import leader
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class SSHConfigData:
    """Data provided by the ``ssh-config`` integration provider.

    Attributes:
        ssh_config:
            Custom configuration to place under
            ``/etc/ssh/ssh_config.d`` on the requirer.
    """

    ssh_config: str


class SSHConfigReadyEvent(ops.RelationEvent):
    """Event emitted when an ``ssh-config`` provider is ready."""


class SSHConfigDisconnectedEvent(ops.RelationEvent):
    """Event emitted when an ``ssh-config`` provider is disconnected."""


class SSHConfigConnectedEvent(ops.RelationEvent):
    """Event emitted when an ``ssh-config`` requirer is connected."""


class _SSHConfigProviderEvents(ops.ObjectEvents):
    """``ssh-config`` provider events."""

    ssh_config_connected = ops.EventSource(SSHConfigConnectedEvent)


class _SSHConfigRequirerEvents(ops.ObjectEvents):
    """``ssh-config`` requirer events."""

    ssh_config_ready = ops.EventSource(SSHConfigReadyEvent)
    ssh_config_disconnected = ops.EventSource(SSHConfigDisconnectedEvent)


class SSHConfigProvider(Interface):
    """Integration interface implementation for ``ssh-config`` providers."""

    on = _SSHConfigProviderEvents()  # type: ignore

    def __init__(self, charm: ops.CharmBase, integration_name: str) -> None:
        super().__init__(charm, integration_name)

        self.framework.observe(
            self.charm.on[self._integration_name].relation_created,
            self._on_relation_created,
        )

    @leader
    def _on_relation_created(self, event: ops.RelationCreatedEvent) -> None:
        """Emit an event when the integration is created."""
        self.on.ssh_config_connected.emit(event.relation)

    @leader
    def set_config_data(  # noqa: D417
        self,
        data: SSHConfigData,
        /,
        integration_id: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Set custom SSH configuration data in the application databag.

        Args:
            data: The SSH configuration data to provide.
            integration_id:
                Optional integration ID to target a specific
                relation instance.

        Keyword Args:
            merge:
                Whether to merge ``data`` into the integration databag rather than
                overwriting. When ``True``, only fields whose values differ from their
                dataclass defaults are written; existing values for unset fields are
                preserved. Defaults to ``False``.
            reset:
                Set of dataclass fields to reset to their default value when
                ``merge`` is ``True``. Has precedence over `data`. Defaults to an
                empty set.
        """
        self._save_integration_data(data, self.app, integration_id, **kwargs)


class SSHConfigRequirer(Interface):
    """Integration interface implementation for ``ssh-config`` requirers."""

    on = _SSHConfigRequirerEvents()  # type: ignore

    def __init__(self, charm: ops.CharmBase, integration_name: str) -> None:
        super().__init__(charm, integration_name, required_app_data=["ssh_config"])

        self.framework.observe(
            self.charm.on[self._integration_name].relation_changed,
            self._on_relation_changed,
        )
        self.framework.observe(
            self.charm.on[self._integration_name].relation_broken,
            self._on_relation_broken,
        )

    def _on_relation_changed(self, event: ops.RelationChangedEvent) -> None:
        """Handle when data from the ``ssh-config`` provider is ready."""
        if not self.is_ready(event.relation.id):
            return

        self.on.ssh_config_ready.emit(event.relation)

    def _on_relation_broken(self, event: ops.RelationBrokenEvent) -> None:
        """Handle when the ``ssh-config`` provider application is removed."""
        self.on.ssh_config_disconnected.emit(event.relation)

    def get_config_data(self, integration_id: int | None = None) -> SSHConfigData | None:
        """Get custom SSH configuration data from the provider's app databag.

        Args:
            integration_id:
                Optional integration ID to target a specific
                integration instance.
        """
        results = self._load_integration_data(SSHConfigData, integration_id=integration_id)
        return results[0] if results else None
