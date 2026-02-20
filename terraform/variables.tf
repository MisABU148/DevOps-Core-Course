variable "cloud_id" {
  description = "ID of Yandex Cloud"
  type        = string
}

variable "folder_id" {
  description = "ID of the folder for resources"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "service_account_key_file" {
  description = "Path to the service account key file"
  type        = string
  default     = "key.json"
}

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "dev-ops-course"
}

variable "username" {
  description = "SSH username"
  type        = string
  default     = "ubuntu"
}

variable "public_key_path" {
  description = "Path to the public SSH key"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}