## Overview

This project is the `openssh` charm, a subordinate Juju machine charm that
automates the full lifecycle of the `openssh`/`sshd` service on Charmed HPC
login and compute nodes. The charm is specified in UHPC014 and implements the
observer design pattern from UHPC010 using `charmed-hpc-libs`. Source lives in
`src/`; unit tests in `tests/unit/`; BDD integration tests in
`tests/integration/`; a CC008-compliant Terraform module in `terraform/`; and
the publishable `ssh-config` integration interface package in `pkg/ssh-config/`.

The target source layout is:

```text
.
├── src
│   ├── charm.py            # Entrypoint; defines OpenSSHCharm
│   ├── config.py           # Application config (pydantic v2 dataclass)
│   ├── constants.py        # Integration names, paths, fixed values
│   ├── openssh.py          # Workload manager (OpenSSHManager, OpenSSHConfigManager)
│   ├── integrations/       # Integration observers (UHPC010)
│   │   ├── __init__.py
│   │   └── ssh_config.py   # ssh-config interface observer
│   └── operations/         # Operations observers (UHPC010)
│       ├── __init__.py
│       └── lifecycle.py    # install/start/stop/config-changed observer
├── pkg
│   └── ssh-config          # uv workspace; published as charmed-openssh-ssh-config-interface
├── terraform               # CC008-compliant Terraform module
├── tests
│   ├── unit
│   └── integration
│       ├── features        # Auto-generated gherkin feature files
│       └── plans           # gherkinator YAML test plans
│
└── lib                     # Vendored charm libraries (if any)
```

The project uses:

- `uv` for dependency management and packaging.
- `just` as the task runner (see `justfile`).
- `ruff` for formatting and linting, `codespell` for spell checking.
- `pyright` for static type checking.
- `ops` (latest) and `charmed-hpc-libs` for charm primitives.
- `pydantic` v2 for config and interface data models.
- `ops.testing` for unit tests; `coverage.py` with branch coverage on
  `src/**/*.py` and `pkg/**/*.py`.
- `jubilant` + `gherkinator` + `pytest-jubilant-bdd` for BDD integration
  tests.
- `charmcraft` (with the `uv` plugin) to build the charm.

### Supported versions

- **Base:** Ubuntu 26.04.
- **Runtime:** Python 3.14.
- **`ops`:** latest stable. Do not pin to an older series.
- **`pydantic`:** v2 only. Do not introduce `pydantic` v1 patterns
  (`pydantic.BaseModel` `class Config:` inner classes, `v1` validator
  decorators, etc.).
- **Juju:** the charm `assumes` `juju >= 3.6`; integration tests run on
  `3.6/stable`.

## Architecture conventions

The charm follows the observer design pattern from specification UHPC010 and
the structure laid out in UHPC014:

1. **`charm.py` is an entrypoint, not a handler dump.** All integration and
   charm-lifecycle event handlers live in observer classes under
   `src/integrations/` and `src/operations/`. `OpenSSHCharm.__init__` wires up
   the `OpenSSHManager`, loads the application config via `load_config`, and
   instantiates the observers — nothing else.
2. **Workload logic is standalone.** `OpenSSHManager` (in `openssh.py`) owns
   all `openssh`/`sshd` service operations (install, reload, port, log level,
   config file management). It must be usable outside the context of a charm.
3. **Application config is validated with `pydantic` v2.** A frozen
   `pydantic.dataclasses.dataclass` in `config.py` validates config options;
   validation failures set a `BlockedStatus` and short-circuit `__init__`.
   Defaults live in `charmcraft.yaml`, not in the dataclass.
4. **Integrations are observers.** Each relation (`ssh-config`, `juju-info`,
   …) has an observer under `src/integrations/` that wraps the corresponding
   `Interface` from `charmed-hpc-libs` (or a vendored `lib/` library) and
   emits domain-specific custom events.
5. **Use `charmed-hpc-libs` primitives.** Prefer `AptLifecycleManager`,
   `SystemctlServiceManager`, `Interface`, `leader`, `StopCharm`, and the
   `refresh` decorator over hand-rolled equivalents.
6. **Interface packages are publishable uv workspaces.** The `ssh-config`
   interface implementation lives under `pkg/ssh-config/` (its own
   `pyproject.toml`) and is published to PyPI as
   `charmed-openssh-ssh-config-interface` (spec UHPC009).

> **CRITICAL — do not stop or uninstall the `openssh`/`sshd` service.**
> The machine the charm is deployed on almost always has a running
> `sshd` provisioned by Juju, which is required for `juju ssh ...` to
> function. Stopping or uninstalling `sshd` will sever Juju's ability to
> reach the unit and can lock operators out of the machine entirely. On
> `juju remove-application`, the charm must **only** remove the custom
> configuration files it created under `/etc/ssh/ssh_config.d/` and reload
> the `sshd` service — never stop or purge `openssh-server`. Installation
> must be idempotent: only install `openssh-server` if it is not already
> present.

## Code style

Follow PEP 8 and PEP 257, plus:

### Imports

Three groups, alphabetized (`ruff format` handles ordering): standard
library, third-party, first-party (`ops`, `charmed_hpc_libs`, `pydantic`,
charm modules such as `config`, `constants`, `openssh`, `integrations`,
`operations`).

### Module naming

Flat module names — `charm.py`, `config.py`, `constants.py`, `openssh.py`.
Observer packages use `integrations/` and `operations/` with `__init__.py`
re-exporting the public observer classes. Do **not** use the `_`-prefix
convention; the public API of each module is its top-level surface.

### Docstrings

Every public module, class, and function must have a PEP 257 docstring.
Document `Args`, `Returns`, and `Raises` sections for non-trivial functions
in the house style of `sssd-operator`'s `openssh.py` module.

### Type annotations

All function signatures must have explicit type annotations. `just typecheck`
(pyright) validates them.

If a typing issue is found in production code (`src/`, `pkg/`), STOP and
propose a resolution to the human-in-the-loop before editing production code:

1. Describe the issue, its location, and the impact.
2. Propose a concrete fix.
3. Ask whether to proceed with the proposed fix or to research alternative
   resolutions.

Do not edit production code until the user explicitly approves the fix.

### Avoid inline error handling

Use explicit `raise` statements and intermediate variables for error
handling rather than burying logic in one-liners or ternary expressions.
Define a charm-specific exception class (for example,
`OpenSSHOpsError`, `InvalidConfigError`) and raise it with a descriptive
message — do not allow `subprocess.CalledProcessError` or
`apt.PackageError` to leak out of `openssh.py`.

### Comments

Do __not__ add generic one-off comments throughout the main codebase. Do add
comments in test files to provide justifications for assertions, mocks, and
workarounds.

### License headers

Every new source file must carry the Apache 2.0 license header at the top.
Set the copyright owner to the organization you are contributing on behalf
of and the year to the current year. When editing an existing file whose
copyright year is stale, extend the range (for example, `2023` →
`2023-2026`). See `CONTRIBUTING.md` for the exact header text.

## Build commands

```bash
just setup               # Create the uv dev environment (uv sync --all-groups).
just build               # Pack the charm with charmcraft -v pack.
just clean               # Remove coverage data, caches, build artifacts, *.charm.
just lock                # Regenerate uv.lock.
just upgrade             # Upgrade uv.lock with the latest dependencies.
just generate-charmhub-token  # Export a Charmhub release token to .charmhub.secret.
```

## Testing

```bash
just check           # Run all static checks (fmt, lint, typecheck).
just unit            # Run unit tests with a coverage report.
just integration     # Validate + generate Gherkin features, then run integration tests.
just test            # Run all test suites (unit + integration).
just test <target>   # Run a specific test target.
just fmt             # Format with ruff and apply auto-fixes.
just lint            # codespell + ruff check + ruff format --check --diff.
just typecheck       # Static type checking with pyright.
```

### Unit tests

Use `ops.testing.Context` (the `Harness` is deprecated) to drive the charm
and its observers. Mock the workload module (`openssh`) via `monkeypatch`
fixtures in `tests/unit/conftest.py` — never call real `subprocess`,
`systemctl`, or `apt` code from unit tests. Each observer and each
`OpenSSHManager` method must have dedicated unit tests.

The `ssh-config` interface implementation under `pkg/ssh-config/` is a uv
workspace member; its tests are picked up by the `just unit` recipe, so no
separate command is needed.

### Integration tests

Integration tests are Behavior-Driven. Author YAML test plans under
`tests/integration/plans/`; `gherkinator validate` and `gherkinator generate`
produce the Gherkin `.feature` files consumed by `pytest-jubilant-bdd`. The
`just integration` recipe runs both steps automatically. Integration tests
require Juju 3.6+ and LXD.

### Coverage

The target is **85% branch coverage** on `src/**/*.py` and `pkg/**/*.py`.
Do __not__ write unit tests for code paths that are impossible to reach in production.

## Terraform

The `terraform/` directory contains a CC008-compliant Terraform module that
allows the `openssh` charm to be deployed via Terraform in addition to the
Juju CLI. When creating, reviewing, or restructuring this module, follow
the
[create-charm-terraform-module SKILL.md](https://github.com/canonical/hpc-team/blob/main/.agents/skills/create-charm-terraform-module/SKILL.md)
— it codifies the required file structure (`README.md`, `providers.tf`,
`terraform.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `locals.tf`),
mandatory/optional inputs and outputs, the README structure, versioning
conventions (`tf-X.Y.Z` for a co-located module), and validation
(`terraform fmt` + `terraform validate`).

Because `openssh` is a subordinate charm, the `units` and `constraints`
variables **must not** be defined. The `requires` (`juju-info`) and `provides`
(`ssh-config`) outputs **must** be present in `outputs.tf`.

## Development workflow

1. Implement charm logic in `src/` following the architecture conventions
   above — new event handlers go in observers, new workload operations go in
   `openssh.py`.
2. Write matching unit tests in `tests/unit/`.
3. Run `just unit` — ensure all tests pass and coverage meets the 85%
   branch coverage threshold.
4. Format: `just fmt`.
5. Lint: `just lint` (codespell + ruff). Fix all linter errors.
6. Typecheck: `just typecheck` (pyright). Fix all typing errors. If a
   typing issue is in production code, follow the human-in-the-loop protocol
   in the Code style section above.
7. If adding or changing BDD scenarios, edit the YAML plans under
   `tests/integration/plans/` and run `just integration` locally (requires
   Juju + LXD). You may be editing on a machine that does not have Juju or LXD available.
   1. Ask for explicit approval to run `just integration` if previous instructions
      do not explicitly state whether to run the integration tests or not.
   2. If in plan mode, explicitly ask the human-in-the-loop if they want to
      skip running the integration tests with `just integration`.
8. Repeat for each new or modified file.

Pipe the output of shell commands to either `head` or `tail` to capture
`stdout` and/or `stderr`.

Ask questions to the human-in-the-loop if you require additional context
or further information before beginning work on non-trivial tasks.

## Commit conventions

Use Conventional Commits prefixes for commit messages:

- `feat:` — New user-facing feature.
- `fix:` — Bug fix.
- `test:` — Add or modify tests only.
- `chore:` — Maintenance tasks (formatting, dependency updates, etc.).
- `docs:` — Documentation only.
- `refactor:` — Code change that neither fixes a bug nor adds a feature.
- `ci:` — CI/CD pipeline changes.

Scopes are allowed (for example, `chore(deps):`, `chore(fmt):`,
`feat(ssh-config):`).

### Commit trailers

- Commits must be signed off (`Signed-off-by:` trailer) **by the human**.
  Agents must never add a `Signed-off-by:` trailer on the human's behalf.
- Agents must include an `Assisted-by:` trailer identifying the agent and
  model.
- Order trailers as: `Assisted-by:` first, then the human's
  `Signed-off-by:` last (added by the human).

Format:

    Assisted-by: AGENT_NAME:MODEL_VERSION[:MODEL_VARIANT]

- `AGENT_NAME`: The AI tool (for example, `opencode`).
- `MODEL_VERSION`: The specific model version used.
- `MODEL_VARIANT`: The variant of the model version used (for example,
  `low`, `medium`, or `high`). Optional.

Other rules:

- Commit messages must be ASCII only.
- Keep PRs small and focused.
- Maintain a linear git history.
- All pre-commit checks must pass.

### Constraints

- Do __not__ add new dependencies beyond what is already in
  `pyproject.toml` (and the `pkg/ssh-config/pyproject.toml` workspace)
  without approval.
- Do __not__ pin `ops` below the latest stable series, and do __not__
  introduce `pydantic` v1.
- Do __not__ install anything with `apt` or `snap` on the development
  machine. The charm may install `openssh-server` via `charmlibs-apt` at
  runtime on the Juju unit — that is unrelated.
- Do __not__ run commands that require `sudo`.
- Do __not__ edit production code (`src/`, `pkg/`) without explicit user
  approval when the change originates from a typing issue — propose the fix
  first and wait for approval (see the human-in-the-loop protocol above).
- Do __not__ stop or uninstall the `openssh`/`sshd` service from
  `juju remove-application`; only remove custom config files under
  `/etc/ssh/ssh_config.d/` and reload. See the CRITICAL callout in the
  Architecture conventions section.
- All errors must be handled explicitly in Python code — no bare
  `subprocess.run(..., check=True)` outside a `try/except` that raises a
  charm-specific error class.

## Further information

- [Specification UHPC014 — OpenSSH operator](https://github.com/canonical/hpc-specs/pull/21)
- [Specification UHPC010 — Observer design pattern in HPC charms](https://github.com/canonical/hpc-specs/blob/main/specs/UHPC%20010%20-%20Observer%20design%20pattern%20in%20HPC%20charms/uhpc010.md)
- [Specification UHPC009 — Distributing Slurm interfaces as Python packages](https://github.com/canonical/hpc-specs/blob/main/specs/UHPC%20009%20-%20Distributing%20Slurm%20interfaces%20as%20Python%20packages/uhpc009.md)
- [Specification CC008 — Charm Terraform Standards](https://github.com/canonical/hpc-team/blob/main/.agents/skills/create-charm-terraform-module/SKILL.md)
- [`charmed-hpc-libs`](https://github.com/canonical/charmed-hpc-libs) — shared charm primitives (`AptLifecycleManager`, `SystemctlServiceManager`, `Interface`, `leader`, `StopCharm`, `refresh`).
