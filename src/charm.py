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

"""Charmed operator for ``openssh``."""

import logging

import ops
from pydantic import ValidationError

from config import CharmConfigManager
from integrations import SSHConfigObserver
from openssh import OpenSSHManager
from operations import LifecycleObserver

_logger = logging.getLogger(__name__)


class OpenSSHCharm(ops.CharmBase):
    """Charmed operator for ``openssh``."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)

        self.openssh = OpenSSHManager()
        try:
            self.app_config = self.load_config(CharmConfigManager)
        except ValidationError as e:
            _logger.error(e)
            failed_options = sorted({error["loc"][0] for error in e.errors() if error.get("loc")})
            self.unit.status = ops.BlockedStatus(
                "Configuration option(s) "
                + ", ".join(f"'{str(o).replace('_', '-')}'" for o in failed_options)
                + " failed validation. See `juju debug-log` for details"
            )
            return

        self.lifecycle = LifecycleObserver(self)
        self.ssh_config = SSHConfigObserver(self)


if __name__ == "__main__":  # pragma: nocover
    ops.main(OpenSSHCharm)
