variable "app_name" {
  description = "Name of the deployed Juju application"
  type        = string
  default     = "openssh"
}

variable "base" {
  description = "Ubuntu base for the charm"
  type        = string
  default     = null
}

variable "channel" {
  description = "Charmhub channel to deploy from"
  type        = string
  default     = "latest/edge"
}

variable "config" {
  description = "Charm configuration options"
  type        = map(string)
  default     = {}
}

variable "model_uuid" {
  description = "UUID of the Juju model to deploy into"
  type        = string
  nullable    = false
}

variable "revision" {
  description = "Optional charm revision number"
  type        = number
  nullable    = true
  default     = null
}
