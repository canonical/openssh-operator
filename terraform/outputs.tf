output "application" {
  description = "The deployed openssh juju_application resource"
  value       = juju_application.openssh
}

output "requires" {
  description = "Map of requires endpoint names"
  value = {
    juju-info  = "juju-info"
    ssh-config = "ssh-config"
  }
}
