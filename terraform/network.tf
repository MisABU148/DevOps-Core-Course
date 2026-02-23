# VPC Network
resource "yandex_vpc_network" "network" {
  name = "lab4-network"
}

# Subnet
resource "yandex_vpc_subnet" "subnet" {
  name           = "lab4-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}

# Security Group
resource "yandex_vpc_security_group" "sg" {
  name       = "lab4-security-group"
  network_id = yandex_vpc_network.network.id

  # Allow SSH (port 22) from anywhere
  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "SSH"
  }

  # Allow HTTP (port 80) from anywhere
  ingress {
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "HTTP"
  }

  # Allow port 5000 (for future app) from anywhere
  ingress {
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "Custom App Port"
  }

  # Allow all outbound traffic
  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "All outbound"
  }
}