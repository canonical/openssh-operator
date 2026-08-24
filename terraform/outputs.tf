output "application" {
  description = "The deployed openssh juju_application resource"
  value       = juju_application.openssh
}

output "provides" {
  description = "Map of provides endpoint names"
  value = {
    ssh-config = "ssh-config"
  }
}

output "requires" {
  description = "Map of requires endpoint names"
  value = {
    juju-info = "juju-info"
  }
}
