output "vm_public_ip" {
  description = "Public IP address of VM"
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh ${var.username}@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}