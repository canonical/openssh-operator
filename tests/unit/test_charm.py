# Copyright 2026 Jason C. Nucciarone
# See LICENSE file for licensing details.
#
# To learn more about testing, see https://documentation.ubuntu.com/ops/latest/explanation/testing/

import ops.testing

from charm import OpenSSHCharm

_CONFIG_SCHEMA = {
    "options": {
        "log-level": {"type": "string", "default": "info"},
        "port": {"type": "int", "default": 22},
    },
}
_META = {
    "requires": {"juju-info": {"interface": "juju-info", "scope": "container"}},
    "provides": {"ssh-config": {"interface": "ssh_config"}},
}


def test_charm_instantiates_with_valid_config(mock_openssh) -> None:
    """The charm does not set ``BlockedStatus`` when config is valid."""
    ctx = ops.testing.Context(OpenSSHCharm, config=_CONFIG_SCHEMA, meta=_META)
    ctx.run(ctx.on.start(), ops.testing.State())


def test_charm_blocked_on_invalid_config(mock_openssh) -> None:
    """The charm sets ``BlockedStatus`` and short-circuits on invalid config."""
    ctx = ops.testing.Context(OpenSSHCharm, config=_CONFIG_SCHEMA, meta=_META)
    # port=23 passes the Juju int schema but fails the pydantic validation
    # (must be exactly 22 or between 1024-65535).
    state_in = ops.testing.State(config={"port": 23, "log-level": "info"})
    state_out = ctx.run(ctx.on.start(), state_in)
    assert state_out.unit_status == ops.BlockedStatus(
        "Configuration option(s) 'port' failed validation. See `juju debug-log` for details"
    )
