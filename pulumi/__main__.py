import pulumi
import pulumi_yandex as yandex

config = pulumi.Config("yandex")

cloud_id = config.require("cloudId")
folder_id = config.require("folderId")
zone = config.require("zone")

# Network
network = yandex.VpcNetwork("lab4-network",
    name="lab4-network"
)

# Subnet
subnet = yandex.VpcSubnet("lab4-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["192.168.10.0/24"],
)

# Security Group
security_group = yandex.VpcSecurityGroup("lab4-security-group",
    network_id=network.id,
    ingress=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=22,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="SSH"
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="HTTP"
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="App"
        ),
    ],
    egress=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
            description="All outbound"
        )
    ]
)

# Ubuntu image
image = yandex.get_compute_image(family="ubuntu-2204-lts")

# VM
vm = yandex.ComputeInstance("dev-ops-course",
    name="dev-ops-course",
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id,
            size=10,
            type="network-hdd"
        )
    ),
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(
        preemptible=True
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id]
        )
    ],
    metadata={
        "ssh-keys": "ubuntu:ssh-rsa YOUR_PUBLIC_KEY"
    }
)

pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("ssh_connection",
              vm.network_interfaces[0].nat_ip_address.apply(
                  lambda ip: f"ssh ubuntu@{ip}"
              ))
