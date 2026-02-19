# Get the latest Ubuntu 22.04 image
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

# VM Instance
resource "yandex_compute_instance" "vm" {
  name        = var.vm_name
  platform_id = "standard-v2" # Intel Cascade Lake
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1          # 1 GB RAM
    core_fraction = 20         # 20% vCPU guarantee (free tier)
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10            # 10 GB HDD
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true   # Assign a public IP
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  metadata = {
    ssh-keys = "${var.username}:${file(var.public_key_path)}"
  }

  scheduling_policy {
    preemptible = true   # Preemptible VM (cheaper/free)
  }
}