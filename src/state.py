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

"""Manage the state of the ``openssh`` charmed operator."""

import ops
from charmed_hpc_libs.ops import Observer, refresh


def check_openssh(observer: Observer) -> ops.StatusBase:
    """Determine the state of the ``openssh`` application/unit.

    Args:
        observer: An ``openssh`` charm observer instance.
    """
    charm = observer.charm

    if not charm.openssh.service.is_active():
        return ops.WaitingStatus("Waiting for `ssh` server to start")

    return ops.ActiveStatus()


refresh = refresh(check_openssh)
