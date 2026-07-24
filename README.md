# OpenSSH operator

![GitHub License](https://img.shields.io/github/license/canonical/openssh-operator)
[![Matrix](https://img.shields.io/matrix/ubuntu-hpc%3Amatrix.org?logo=matrix&label=ubuntu-hpc)](https://matrix.to/#/#hpc:ubuntu.com)

A [Juju](https://juju.is) charm for automating the full lifecycle operations of
[OpenSSH](https://www.openssh.com), the premier connectivity tool for remote login
with the SSH protocol.

## ✨ Getting Started

To deploy the OpenSSH operator, you'll need to integrate it with a principal charm:

```shell
juju deploy ubuntu --base ubuntu@26.04
juju deploy openssh-operator
juju integrate openssh-operator ubuntu
```

The OpenSSH operator provides the `ssh-config` integration for charms that need to
configure custom SSH server settings (for example, enabling LDAP-based key lookup for SSSD).

## 🤔 What's next?

If you want to learn more about all the things you can do with the OpenSSH operator,
or have any further questions on what you can do with the operator, here are some
further resources for you to explore:

* [Charmed HPC documentation](https://documentation.ubuntu.com/charmed-hpc)
* [Open an issue](https://github.com/canonical/openssh-operator/issues/new?title=ISSUE+TITLE&body=*Please+describe+your+issue*)
* [Ask a question](https://discourse.ubuntu.com/c/project/hpc/151)

## 🛠️ Development

This project uses [uv](https://docs.astral.sh/uv/) and [just](https://just.systems) for development. You can install them with:

```shell
sudo snap install astral-uv --classic
sudo snap install just --classic
```

The project provides several useful commands that will help you while hacking on the OpenSSH operator:

```shell
just fmt           # Apply formatting standards to code.
just lint          # Check code against coding style standards.
just typecheck     # Run static type checks.
just unit          # Run unit tests.
```

To run the OpenSSH operator integration tests, you'll need to have both
[Juju](https://juju.is) and [LXD](https://ubuntu.com/lxd) installed
on your machine:

```shell
just integration   # Run integration tests.
```

If you're interested in contributing, take a look at our [contributing guidelines](./CONTRIBUTING.md).

## 🤝 Project and Community

The OpenSSH operator is a project of the [Ubuntu High-Performance Computing community](https://ubuntu.com/community/governance/teams/hpc).
Interested in contributing bug fixes, patches, documentation, or feedback? Want to join the
Ubuntu HPC community? You've come to the right place.

Here's some links to help you get started with joining the community:

* [Ubuntu Code of Conduct](https://ubuntu.com/community/ethos/code-of-conduct)
* [Contributing guidelines](./CONTRIBUTING.md)
* [Join the conversation on Matrix](https://matrix.to/#/#hpc:ubuntu.com)
* [Get the latest news or ask and answer questions on the Ubuntu Discourse](https://discourse.ubuntu.com/c/project/hpc/151)

## 📋 License

The OpenSSH operator is free software, distributed under the Apache Software License, version 2.0.
See the [Apache-2.0 LICENSE](./LICENSE) file for further details.

OpenSSH is licensed under the BSD license.
See the upstream OpenSSH [LICENSE](https://github.com/openssh/openssh-portable/blob/master/LICENCE) file
for further licensing information about OpenSSH.
