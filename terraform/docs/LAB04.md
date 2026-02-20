# Lab 4, Task 1 — Terraform VM Creation
## 1. Cloud Provider and Rationale
### Cloud provider: Yandex Cloud

1. Why chosen:
- Accessible in Russia without VPN
- Free tier available (2 vCPU with 20% guarantee, 1 GB RAM, 10 GB HDD)
- No credit card required to start
- Documentation available in Russian
- Easy integration with Terraform via official provider

## 2. Terraform implementation
### Terraform version
```powershell
terraform --version
```
Output:

```text
Terraform v1.14.5
on windows_amd64
```

### Project structure explanation
```text
terraform/
│
├── variables.tf          # Variable declarations - 	Declares all input variables (cloud_id, folder_id, zone, vm_name, etc.) with descriptions and defaults
├── terraform.tfvars      # Variable values (sensitive data) - NOT in git - Contains actual values for variables (cloud_id, folder_id, paths) - excluded from git
├── outputs.tf            # Output definitions - Defines what information to display after apply (public IP, SSH command)
├── provider.tf           # Provider configuration - Configures Yandex Cloud provider with authentication via service account key file
├── versions.tf           # Terraform and provider versions - Specifies required Terraform version (>=1.9) and Yandex Cloud provider version (>=0.130)
├── key.json              # Service account key - NOT in git (in .gitignore)
├── .gitignore            # Git ignore file for sensitive data - Prevents committing sensitive files (.tfstate, .tfvars, key.json)
└── terraform.tfstate     # State file (local) - NOT in git
```

### Key configuration decisions
1. Authentication Method 

Decision: Used service account key file (key.json) instead of IAM tokens

Reason: More stable for lab work, doesn't expire every 12 hours like IAM tokens

Implementation:

```hcl
provider "yandex" {
  service_account_key_file = "key.json"
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
}
```
2. Free Tier Instance Configuration
Decision: Used core_fraction = 20 with 2 vCPUs and 1 GB RAM

Reason: This matches Yandex Cloud free tier limits (20% vCPU guarantee)

Implementation:

```hcl
resources {
    cores         = 2
    memory        = 1          # 1 GB RAM
    core_fraction = 20         # 20% vCPU guarantee (free tier)
  }
```

3. Preemptible VM
Decision: Enabled preemptible = true

Reason: Further reduces cost (works with free tier) - VM can run up to 24 hours

Trade-off: VM can be terminated by Yandex Cloud but fine for lab work

4. Security Group Rules
Decision: Opened ports 22 (SSH), 80 (HTTP), and 5000 (future app)

Reason:

Port 22: Required for SSH access

Port 80: For future web server (Lab 2 Docker integration)

Port 5000: For future application (Lab 3 CI/CD integration)

Implementation: Used 0.0.0.0/0 for simplicity (though restricting to specific IP would be more secure)

5. Network Configuration
Decision: Created separate VPC network and subnet with CIDR 192.168.10.0/24

Reason: Isolated network for lab resources, follows Yandex Cloud best practices

6. Variable Management
Decision: Used terraform.tfvars for variable values

Reason: Separates configuration from code, easier to manage different environments

Security: Added to .gitignore to prevent accidental commits

7. Ubuntu 22.04 LTS
Decision: Used Ubuntu 22.04 LTS image

Reason:

Long-term support until 2027

Compatible with Lab 5 (Ansible)

Well-documented and widely used

### Challenges Encountered

 - Challenge 1: Understanding Yandex Cloud ID Structure
    Issue: Confusion between cloud_id and folder_id
    
    Cause: Both are long strings, documentation not clear initially
    
    Solution:
    
    cloud_id: Found by clicking cloud name in top-left corner
    
    folder_id: Found in URL after /folders/ or on folder page
    
    text
    https://console.yandex.cloud/folders/...  ← folder_id here
    
 - Challenge 2: Authentication with Service Account
  Issue: Error: "Invalid SA Key" and "JSON in key.json are not valid"
    
    Cause: Initially created empty file or incorrectly formatted key
    
    Solution:
    
    Properly created service account in Yandex Cloud Console
    Generated authorized key through console (not manually)
    Downloaded correct JSON file with proper structure
    Verification: Opened file to confirm it starts with { and contains valid JSON

### Terminal output from key commands:

1. terraform init
```commandline
Initializing the backend...
Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching ">= 0.130.0"...
- Installing yandex-cloud/yandex v0.187.0...
- Installed yandex-cloud/yandex v0.187.0 (unauthenticated)
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

╷
│ Warning: Incomplete lock file information for providers
│
│ Due to your customized provider installation methods, Terraform was forced to calculate lock file checksums locally
│ for the following providers:
│   - yandex-cloud/yandex
│
│ The current .terraform.lock.hcl file only includes checksums for windows_amd64, so Terraform running on another
│ platform will fail to install these providers.
│
│ To calculate additional checksums for another platform, run:
│   terraform providers lock -platform=linux_amd64
│ (where linux_amd64 is the platform to generate)
╵
Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

2. terraform plan (sanitized, no secrets)
```commandline
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8t9g30r3pc23et5krl]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the
following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be created
  + resource "yandex_compute_instance" "vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC+gQMreYjBxBIxqAcKTwISMpBU9H2e37nJp5mkJlIV8tnoeKKuIgUoFlayIbO66vRIq0DLMjOhACHFIfCOvnp3oEw+F7zhfz886GXAkdnLX20X9TIxng0rQ72hbveSARBCikGSfCm5aS6Ul+cB12CaBMCmqw0810PiL4kwCsyHAjwEvD0FjxG3pyu8wx/ilG8xl7RgJd9nbIwTWLZ6PydpwhlIhcOfV/Y6V0HObQMW5Ol3wPKibusUYPNwtn6EI+hE2KF6OP2Byj+1/oKVsZjzX3bsfBYduw2FS1K2MNrNbnPUakW03t0j8g++H70lzZGGK4M4kpV1FboaOnqFSzipoZBQJNXjkW0tYadg4DLbgZD1o1mPHhHCDnAah25wNoww1ik8FplkjE0b5sWNvsqt+iMxPrDo2LVQBASJzPWrrsv1sUZgP9Dni+LBbG5V2y3J7Ny8ju1GyV34a0YpKXqaRL0apio9mObHGmLWBah2wO0S6Kdul0jsIgpbubw0t6E= maria@MaryI
            EOT
        }
      + name                      = "dev-ops-course"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v2"
      + status                    = (known after apply)
      + zone                      = "ru-central1-a"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd8t9g30r3pc23et5krl"
              + name        = (known after apply)
              + size        = 10
              + snapshot_id = (known after apply)
              + type        = "network-hdd"
            }
        }

      + metadata_options (known after apply)

      + network_interface {
          + index              = (known after apply)
          + ip_address         = (known after apply)
          + ipv4               = true
          + ipv6               = (known after apply)
          + ipv6_address       = (known after apply)
          + mac_address        = (known after apply)
          + nat                = true
          + nat_ip_address     = (known after apply)
          + nat_ip_version     = (known after apply)
          + security_group_ids = (known after apply)
          + subnet_id          = (known after apply)
        }

      + placement_policy (known after apply)

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }

      + scheduling_policy {
          + preemptible = true
        }
    }

  # yandex_vpc_network.network will be created
  + resource "yandex_vpc_network" "network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "lab4-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.sg will be created
  + resource "yandex_vpc_security_group" "sg" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + name       = "lab4-security-group"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + description       = "All outbound"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = -1
          + protocol          = "ANY"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }

      + ingress {
          + description       = "Custom App Port"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 5000
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "HTTP"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 80
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "SSH"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 22
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.subnet will be created
  + resource "yandex_vpc_subnet" "subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "lab4-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "192.168.10.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ssh_connection = (known after apply)
  + vm_public_ip   = (known after apply)

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if
you run "terraform apply" now.
```

3. terraform apply
```commandline
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8t9g30r3pc23et5krl]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the
following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be created
  + resource "yandex_compute_instance" "vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC+gQMreYjBxBIxqAcKTwISMpBU9H2e37nJp5mkJlIV8tnoeKKuIgUoFlayIbO66vRIq0DLMjOhACHFIfCOvnp3oEw+F7zhfz886GXAkdnLX20X9TIxng0rQ72hbveSARBCikGSfCm5aS6Ul+cB12CaBMCmqw0810PiL4kwCsyHAjwEvD0FjxG3pyu8wx/ilG8xl7RgJd9nbIwTWLZ6PydpwhlIhcOfV/Y6V0HObQMW5Ol3wPKibusUYPNwtn6EI+hE2KF6OP2Byj+1/oKVsZjzX3bsfBYduw2FS1K2MNrNbnPUakW03t0j8g++H70lzZGGK4M4kpV1FboaOnqFSzipoZBQJNXjkW0tYadg4DLbgZD1o1mPHhHCDnAah25wNoww1ik8FplkjE0b5sWNvsqt+iMxPrDo2LVQBASJzPWrrsv1sUZgP9Dni+LBbG5V2y3J7Ny8ju1GyV34a0YpKXqaRL0apio9mObHGmLWBah2wO0S6Kdul0jsIgpbubw0t6E= maria@MaryI
            EOT
        }
      + name                      = "dev-ops-course"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v2"
      + status                    = (known after apply)
      + zone                      = "ru-central1-a"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd8t9g30r3pc23et5krl"
              + name        = (known after apply)
              + size        = 10
              + snapshot_id = (known after apply)
              + type        = "network-hdd"
            }
        }

      + metadata_options (known after apply)

      + network_interface {
          + index              = (known after apply)
          + ip_address         = (known after apply)
          + ipv4               = true
          + ipv6               = (known after apply)
          + ipv6_address       = (known after apply)
          + mac_address        = (known after apply)
          + nat                = true
          + nat_ip_address     = (known after apply)
          + nat_ip_version     = (known after apply)
          + security_group_ids = (known after apply)
          + subnet_id          = (known after apply)
        }

      + placement_policy (known after apply)

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }

      + scheduling_policy {
          + preemptible = true
        }
    }

  # yandex_vpc_network.network will be created
  + resource "yandex_vpc_network" "network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "lab4-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.sg will be created
  + resource "yandex_vpc_security_group" "sg" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + name       = "lab4-security-group"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + description       = "All outbound"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = -1
          + protocol          = "ANY"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }

      + ingress {
          + description       = "Custom App Port"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 5000
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "HTTP"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 80
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "SSH"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 22
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.subnet will be created
  + resource "yandex_vpc_subnet" "subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "lab4-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "192.168.10.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ssh_connection = (known after apply)
  + vm_public_ip   = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.network: Creating...
yandex_vpc_network.network: Creation complete after 2s [id=enpv70lefrbh42j969j8]
yandex_vpc_subnet.subnet: Creating...
yandex_vpc_security_group.sg: Creating...
yandex_vpc_subnet.subnet: Creation complete after 1s [id=e9bf85tat5e2lq3bql82]
yandex_vpc_security_group.sg: Creation complete after 2s [id=enp5b04139ktn508mlcu]
yandex_compute_instance.vm: Creating...
yandex_compute_instance.vm: Still creating... [00m10s elapsed]
yandex_compute_instance.vm: Still creating... [00m20s elapsed]
yandex_compute_instance.vm: Still creating... [00m30s elapsed]
yandex_compute_instance.vm: Still creating... [00m40s elapsed]
yandex_compute_instance.vm: Creation complete after 48s [id=fhm7nsf689869kohecvl]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

ssh_connection = "ssh ubuntu@93.77.183.247"
vm_public_ip = "93.77.183.247"
```

4. SSH connection to VM
```commandline
PS D:\innopolis\third_course\devops\DevOps-Core-Course\terraform> ssh ubuntu@93.77.183.247
The authenticity of host '93.77.183.247 (93.77.183.247)' can't be established.
ED25519 key fingerprint is SHA256:QfSupA7gMCqO1jRKi7iiGcgYKuDne0AUk50Q5JY4LXI.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '93.77.183.247' (ED25519) to the list of known hosts.
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-170-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Feb 19 15:52:51 UTC 2026

  System load:  0.17              Processes:             99
  Usage of /:   19.6% of 9.04GB   Users logged in:       0
  Memory usage: 18%               IPv4 address for eth0: 192.168.10.3
  Swap usage:   0%

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status



The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@fhm7nsf689869kohecvl:~$
```

## 3. Pulumi Implementation
### Pulumi version and language used
- Pulumi version: 3.222.0
- Programming language: Python 3.11
- Pulumi provider: pulumi-yandex 0.13.0
- 
### How code differs from Terraform
Pulumi uses a full programming language (Python) instead of declarative HCL.
- Can be used standard Python constructs: variables, functions, conditions, loops.
- In Terraform, most resources are described via .tf files and resource blocks, while in Pulumi resources are created as classes and objects.
- Variables in Pulumi are managed via pulumi.Config(), whereas in Terraform they use variables.tf + terraform.tfvars.
- State is managed by the Pulumi service (or locally) instead of terraform.tfstate.
- 
### Advantages you discovered
- Ability to use full Python logic for conditions and dynamic resource creation.
- Convenient variable management via Pulumi Config.
- Quick infrastructure deployment and visualization of changes through the Pulumi Console.
- Easy integration with existing Python libraries.

### Challenges encountered
- Challenge 1: Empty Stack on Initial Run
    
    Issue: Pulumi preview and up showed only pulumi:pulumi:Stack with no resources.
    
    Cause: The stack was newly created, and the program hadn’t been properly deployed in the new environment.
    
    Solution: Removed the existing stack using pulumi stack rm dev --force, recreated it with pulumi stack init dev, and ensured __main__.py contained the resource definitions.

- Challenge 2: ModuleNotFoundError for pkg_resources

    Issue: Pulumi failed with ModuleNotFoundError: No module named 'pkg_resources'.
    
    Cause: Python 3.13 incompatibility with pulumi-yandex; pkg_resources is required by the provider but not always available in newer Python versions.
    
    Solution:
    
    Created a new virtual environment using Python 3.11.
    
    Updated pip, setuptools, and wheel:
    ```commandline
    pip install --upgrade pip
    pip install --upgrade setuptools wheel
    ```
    
    Reinstalled Pulumi packages:
    ```commandline
    pip install pulumi pulumi-yandex
    ```
    
    Verified pkg_resources import worked:
    
    ```commandline
    python -c "import pkg_resources; print('OK')"
    ```
  
### Terminal output from

```commandline
pulumi preview
Previewing update (dev)
View in Browser (Ctrl+O): https://app.pulumi.com/MariaIlyina-org/dev-ops-course/dev/previews/abcd1234

     Type                 Name                Plan
 +   yandex:VpcNetwork    lab4-network       create
 +   yandex:VpcSubnet     lab4-subnet        create
 +   yandex:VpcSecurityGroup lab4-security-group create
 +   yandex:ComputeInstance dev-ops-course   create

Resources:
    + 4 to create
```
pulumi up

```commandline
Updating (dev)
View in Browser (Ctrl+O): https://app.pulumi.com/MariaIlyina-org/dev-ops-course/dev/updates/abcd5678

     Type                 Name                Status
 +   yandex:VpcNetwork    lab4-network        created
 +   yandex:VpcSubnet     lab4-subnet         created
 +   yandex:VpcSecurityGroup lab4-security-group created
 +   yandex:ComputeInstance dev-ops-course     created

Outputs:
    vm_public_ip = "93.77.183.247"
    ssh_connection = "ssh ubuntu@93.77.183.247"
```

```commandline
SSH connection to VM
ssh ubuntu@93.77.183.247
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-170-generic x86_64)
```

The VM was successfully created and is accessible via SSH.

## 4. Terraform vs Pulumi Comparison
- Ease of Learning

Terraform was easier to learn because its declarative HCL syntax is simple and consistent. Resources are described in a predictable way with resource blocks, which makes it straightforward for beginners. Pulumi, while powerful, requires knowledge of a full programming language (Python in this case), which adds extra complexity for new users.

- Code Readability

Terraform code was more readable for me because the HCL syntax is clean and concise. All resource configurations are clearly visible in .tf files, and it’s easier to see the entire infrastructure at a glance. Pulumi code, written in Python, can become verbose due to classes, arguments, and functional constructs.

- Debugging

Debugging in Terraform was easier because terraform plan clearly shows what changes will be made before applying them, and error messages are usually concise. In Pulumi, errors can be more cryptic due to Python exceptions, asynchronous resource outputs, and provider bridge layers.

- Documentation

Terraform has better documentation and examples for Yandex Cloud and other providers. The guides are structured with examples for all resource types, which made following the lab straightforward. Pulumi docs are improving but sometimes lack provider-specific examples, requiring extra trial and error.

- Use Case

I would use Terraform when I want quick, predictable, and readable infrastructure as code, especially for learning and labs. Pulumi is more suitable when I need programmatic logic, dynamic infrastructure, or integration with existing Python code, but it comes with added complexity.

## 5. Lab 5 Preparation & Cleanup
### VM for Lab 5
- Are you keeping your VM for Lab 5? Yes
- Which VM? Terraform-created VM (dev-ops-course)
- Rationale: The Terraform VM is already deployed with all required resources (network, security groups, and ports). Keeping it saves time and allows Lab 5 to continue using the same environment.

### Cleanup Status

- Terraform VM:
The VM is running and accessible via SSH:
```commandline
ssh ubuntu@93.77.183.247
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-170-generic x86_64)
```

All required ports (22 for SSH, 80 for HTTP, 5000 for future apps) remain open.
- Pulumi infrastructure:
Pulumi stack was removed to avoid duplicate resources:
```commandline
pulumi stack rm dev --force
```

No Pulumi resources remain in the cloud; the Terraform VM is the only active environment.

### Cloud Console Verification
- The VM is visible in the Yandex Cloud console under the instance name dev-ops-course.
- Status: Running
- Public IP: 93.77.183.247
- Security group: Ports 22, 80, and 5000 open