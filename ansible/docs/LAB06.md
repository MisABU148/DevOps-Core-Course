## Overview - What you accomplished and technologies used
### Accomplishments:
1. Successfully configured Ansible control node in WSL
- Resolved SSH key permission issues (chmod 600)
- Configured ansible.cfg with correct parameters
- Overcame "world writable directory" warning by explicitly setting ANSIBLE_CONFIG

2. Deployed Docker on remote server (terraform-vm)
- Installed Docker version 29.3.0
- Configured Docker repository and GPG key
- Added user to docker group for password-less Docker commands

3. Implemented tag-based execution strategy
- Selective role execution using --tags
- Role exclusion using --skip-tags
- Change preview using --check (dry-run mode)

4. Achieved idempotent configuration
- Most tasks show ok (no changes) on subsequent runs
- Only logging tasks show changed status

Technologies Used:\
Technology	- Purpose -	Version/Configuration \
Ansible Core -	Configuration management -	2.16.3\
WSL 2	- Ansible execution environment on Windows -	Ubuntu 24.04\
Docker -	Application containerization -	29.3.0\
Ubuntu -	Target OS on server -	22.04/24.04\
Python -	Interpreter for Ansible modules -	3.12.3\
OpenSSH -	Secure connection to servers	-\
Git -	Version control	-


## Blocks & Tags - Block usage in each role, tag strategy, execution examples
### Role Structure

- common Role - Basic server setup \
Place: **ansible/roles/common/tasks/main.yml**


- docker Role - Docker installation and configuration \
Place: **ansible/roles/docker/tasks/main.yml**

Tag Strategy
```text
├── always           # Always executed (apt cache update)
├── packages         # Package installation
├── users           # User management
├── docker_install  # Docker installation
├── docker_service  # Docker service management
├── docker_users    # User permissions setup
├── docker_info     # Docker information tasks
├── docker_deploy   # Container deployment
└── debug           # Debugging tasks
```

### Execution Examples
Example 1: Install only Docker
```bash
ANSIBLE_CONFIG=ansible.cfg ansible-playbook playbooks/provision.yml --tags "docker_install,docker_service,docker_users"
```
Result:

```text
ok=12 changed=1 skipped=0
```
Analysis: Only Docker installation tasks executed, common role skipped

Example 2: Skip common role entirely
```bash
ANSIBLE_CONFIG=ansible.cfg ansible-playbook playbooks/provision.yml --skip-tags "common"
```
Result:

```text
ok=16 changed=0 skipped=12
```
Analysis: All common tasks skipped, only docker tasks executed

Example 3: Only common packages
```bash
ANSIBLE_CONFIG=ansible.cfg ansible-playbook playbooks/provision.yml --tags "packages"
```
Result:

```text
ok=6 changed=1
```
Analysis: Only tasks with 'packages' tag from common role executed

Example 4: Dry-run Docker installation
```bash
ANSIBLE_CONFIG=ansible.cfg ansible-playbook playbooks/provision.yml --tags "docker" --check
```
Result:

```text
ok=16 changed=1 skipped=13
```
Analysis: --check shows what changes would occur without applying them

Example 5: Full installation (all tags)
```bash
ANSIBLE_CONFIG=ansible.cfg ansible-playbook playbooks/provision.yml
```
Result:

```text
ok=18 changed=4 skipped=12
```
Example 6: Specific tag "docker_install" only
```bash
ANSIBLE_CONFIG=ansible.cfg ansible-playbook playbooks/provision.yml --tags "docker_install"
```
Result:

```text
ok=12 changed=1 skipped=0
```

## 
## 2.1 Why Docker Compose?

### Advantages over docker run:

| Feature | docker run | Docker Compose |
|---------|------------|----------------|
| **Declarative configuration** | Command-line flags only | YAML file defines desired state |
| **Multi-container management** | Manual each container | Single command for all services |
| **Networks & Volumes** | Manual creation | Declarative in compose file |
| **Environment variables** | --env flags | .env files, variable substitution |
| **Easy updates** | Stop, remove, run new | Change config and `docker-compose up` |
| **Production consistency** | Manual steps error-prone | Reproducible deployments |
| **Dependencies** | Manual start order | `depends_on` configuration |

