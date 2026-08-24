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

"""Manage the ``openssh`` charm's application configuration."""

import logging
from typing import Annotated, Literal, get_args

from pydantic import Field, field_validator
from pydantic.dataclasses import dataclass

type LogLevel = Literal[
    "quiet", "fatal", "error", "info", "verbose", "debug", "debug1", "debug2", "debug3"
]

_DEBUG_LOG_LEVELS = frozenset(filter(lambda v: "debug" in v, get_args(LogLevel.__value__)))
_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfigData:
    """Charm configuration data.

    Attributes:
        port: Port number the ``ssh`` service listens on.
        log_level: Logging level for the ``ssh`` service.
    """

    port: Literal[22] | Annotated[int, Field(ge=1024, le=65535)]
    log_level: LogLevel

    @field_validator("log_level", mode="after")
    @classmethod
    def _warn_debug_log_level(cls, value: str) -> str:
        """Log a warning when a debug-level logging mode is selected."""
        if value in _DEBUG_LOG_LEVELS:
            _logger.warning(
                "log level '%s' should not be used in production; it may emit sensitive user data",
                value,
            )

        return value
