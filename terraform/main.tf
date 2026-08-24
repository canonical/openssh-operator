resource "juju_application" "openssh" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "openssh"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }

  config = var.config
}
