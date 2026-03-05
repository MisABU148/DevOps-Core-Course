# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

### Ansible Version Used
```bash
$ ansible --version
ansible [core 2.16.3]
  config file = /mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible/ansible.cfg
  configured module search path = ['/home/maria/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python3/dist-packages/ansible
  ansible collection location = /home/maria/.ansible/collections:/usr/share/ansible/collections
  executable location = /usr/bin/ansible
  python version = 3.12.3 (main, Jan 22 2026, 20:57:42) [GCC 13.3.0] (/usr/bin/python3)
  jinja version = 3.1.2
  libyaml = True
```

### Target VM OS and Version
The target virtual machine runs Ubuntu 24.04 LTS (Noble Numbat) with the following specifications:
- OS: Ubuntu 24.04 LTS
- Kernel: Linux 5.15.0-170-generic
- Architecture: x86_64
- Hostname: fhmp20dgqsvot5oaf8ut (temporary cloud instance name)

The VM was provisioned using Terraform (from Lab 4) in a cloud environment and is accessible via SSH using an RSA key pair.

### Role Structure Diagram
```text
ansible/
├── inventory/
│   └── hosts.ini                    # Static inventory file with VM details
├── roles/
│   ├── common/                       # Base system configuration
│   │   ├── tasks/
│   │   │   └── main.yml              # System updates, package installation, timezone
│   │   └── defaults/
│   │       └── main.yml              # Default variables for common role
│   ├── docker/                        # Docker installation and configuration
│   │   ├── tasks/
│   │   │   └── main.yml              # Docker CE, CLI, Compose installation
│   │   ├── handlers/
│   │   │   └── main.yml              # Docker service restart handler
│   │   └── defaults/
│   │       └── main.yml              # Docker version variables
│   └── app_deploy/                    # Application deployment
│       ├── tasks/
│       │   └── main.yml              # Create directories, deploy docker-compose
│       ├── handlers/
│       │   └── main.yml              # Application restart handler
│       └── defaults/
│           └── main.yml              # App name, port, image variables
├── playbooks/
│   ├── site.yml                       # Full deployment (all roles)
│   ├── provision.yml                   # System provisioning only (common + docker)
│   └── deploy.yml                      # App deployment only
├── group_vars/
│   └── all.yml                         # Global variables (encrypted with Ansible Vault)
├── ansible.cfg                         # Ansible configuration file
└── docs/
    └── LAB05.md                         # This documentation
```

### Why Roles Instead of Monolithic Playbooks?
Ansible roles provide several advantages over monolithic (single-file) playbooks:

|Aspect| 	Monolithic Playbook                          | 	Role-Based Structure                                 |
|-------------------------------------------------------------------|------------------------|--------------------------------------------------|
|Reusability	| Code is tied to one project	                  | Roles can be reused across different projects         |
|Maintainability	| Hard to debug and update when playbook grows	 | Each role has single responsibility, easy to maintain |
|Readability	| Complex logic mixed together	                 | Clear separation of concerns                          |
|Collaboration	| Multiple people editing same file	            | Teams can work on different roles simultaneously      |
|Testing	| Difficult to test individual parts	           | Each role can be tested independently                 |
|Version Control	| One large file with many changes	             | Granular commits per role/feature                     |

## Roles Documentation

## 2. Roles Documentation

### 2.1 Common Role

#### Purpose
The `common` role performs basic system initialization and configuration that should be applied to all servers. It ensures a consistent base environment before any application-specific roles are applied.

**Key responsibilities:**
- Updates package cache to ensure latest package information
- Installs essential system utilities and tools
- Configures system timezone
- Sets up basic security (optional)
- Provides foundation for other roles

#### Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `common_packages` | See list below | List of essential packages to install |
| `timezone` | `UTC` | System timezone configuration |
| `upgrade_system` | `false` | Whether to upgrade all packages (use with caution) |

**Default packages list:**
```yaml
common_packages:
  - python3-pip        # Python package manager
  - python3-venv       # Python virtual environment
  - python3-setuptools # Python package utilities
  - curl               # Data transfer tool
  - wget               # File downloader
  - git                # Version control
  - vim                # Text editor
  - htop               # Process viewer
  - net-tools          # Network utilities (ifconfig, netstat)
  - tree               # Directory tree viewer
  - unzip              # Archive extraction
  - software-properties-common # PPA management
  - apt-transport-https        # HTTPS for apt
  - ca-certificates    # SSL certificates
  - gnupg              # GPG key management
  - lsb-release        # Linux distribution info
  - cron               # Job scheduler
  - ufw                # Firewall (optional)
  ```

#### Handlers
|Handler| Name|	Trigger|	Action|
|-|-|-|-|
|restart cron	|Timezone change	|Restarts cron| service to apply new timezone|
Handler definition:

```yaml
- name: restart cron
  systemd:
    name: cron
    state: restarted
    daemon_reload: yes
```
Dependencies
None - This role has no external dependencies and can run on any fresh Ubuntu installation.

### Docker Role
####  Purpose
- The docker role installs and configures Docker container runtime on the target system. It sets up Docker CE (Community Edition) with all necessary components and prepares the system for running containerized applications.
- Key responsibilities:
- Removes old/unofficial Docker packages
- Adds official Docker GPG key and repository
- Installs Docker Engine, CLI, and Containerd
- Installs Docker plugins (BuildX, Compose V2)
- Configures Docker service to start on boot
- Adds users to docker group for non-sudo access
- Installs Python Docker modules for Ansible integration

#### Verifies Docker installation

Variables

|Variable	|Default Value	|Description|
|-|-|-|
|docker_version	latest	|Specific |Docker version to install|
|docker_compose_version	|latest	|Docker Compose plugin version|
|docker_user	|{{ ansible_user }}	|User to add to docker group|
|docker_daemon_options	|See below	|Docker daemon configuration|
Default daemon options:

```yaml
docker_daemon_options:
  log-driver: "json-file"
  log-opts:
    max-size: "10m"
    max-file: "3"
   ```
Handlers

|Handler |Name	|Trigger	Action|
|-|-|-|
|restart docker	|Docker installation or config change	|Restarts Docker service to apply changes|
Handler definition:
```
yaml
- name: restart docker
  systemd:
    name: docker
    state: restarted
    daemon_reload: yes
   ```
Dependencies
Common Role - Requires basic system packages (ca-certificates, curl, gnupg) which are installed by the common role. The Docker role can run independently, but these packages are prerequisites.

### App_Deploy Role
Purpose
    The app_deploy role handles the deployment of containerized applications using Docker Compose. It creates the necessary directory structure, configuration files, and launches the application containers.

Key responsibilities:
- Creates application directory structure
- Generates docker-compose.yml configuration
- Creates sample HTML content (for testing)
- Deploys application using Docker Compose
- Ensures application containers are running
- Provides restart capability for updates

Variables

|Variable	| Default Value           | 	Description |
|-|-------------------------|--------|
|app_name	| myapp	                  | Name of the application/project |
|app_port| 	80                     | Host port to expose           |
|app_image	nginx:alpine| 	Docker image to deploy |
|app_directory	/opt/{{ app_name }}	| Installation directory  |  (derived) |
|app_user	| {{ ansible_user }}	     | Owner of application files |

Example docker-compose.yml template:

```yaml
version: '3.8'

services:
  web:
    image: "{{ app_image }}"
    ports:
      - "{{ app_port }}:80"
    volumes:
      - ./html:/usr/share/nginx/html
    restart: unless-stopped
```
   
Handlers

|Handler| Name|	Trigger	Action|
|-|-|-|
|restart app	|Configuration change	|Restarts application containers|
Handler definition:

```yaml
- name: restart app
  docker_compose:
    project_src: "/opt/{{ app_name }}"
    state: restarted
```
Dependencies
- Docker Role - Requires Docker and Docker Compose to be installed on the target system
- Docker service must be running - Application deployment will fail if Docker is not operational

### Idempotency Demonstration
#### Terminal output from FIRST provision.yml run

```yaml
/mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers with common tools and Docker] **************************************************************

TASK [Gathering Facts] *************************************************************************************************
ok: [terraform-vm]

TASK [Show playbook start] *********************************************************************************************
ok: [terraform-vm] => {
    "msg": "Starting provisioning of terraform-vm"
}

TASK [common : Update apt cache] ***************************************************************************************
changed: [terraform-vm]

TASK [common : Install essential packages] *****************************************************************************
changed: [terraform-vm]

TASK [common : Set timezone to UTC] ************************************************************************************
changed: [terraform-vm]

TASK [common : Upgrade all packages (optional - comment out if not needed)] ********************************************
skipping: [terraform-vm]

TASK [docker : Remove old Docker packages] *****************************************************************************
ok: [terraform-vm]

TASK [docker : Install required system packages] ***********************************************************************
ok: [terraform-vm]

TASK [docker : Add Docker GPG key] *************************************************************************************
changed: [terraform-vm]

TASK [docker : Add Docker repository] **********************************************************************************
changed: [terraform-vm]

TASK [docker : Install Docker packages] ********************************************************************************
changed: [terraform-vm]

TASK [docker : Install Python Docker module] ***************************************************************************
changed: [terraform-vm]

TASK [docker : Ensure Docker service is running and enabled] ***********************************************************
ok: [terraform-vm]

TASK [docker : Add user to docker group] *******************************************************************************
changed: [terraform-vm]

TASK [docker : Check Docker version] ***********************************************************************************
ok: [terraform-vm]

TASK [docker : Display Docker version] *********************************************************************************
ok: [terraform-vm] => {
    "msg": "Installed Docker version 29.2.1, build a5c7197"
}

RUNNING HANDLER [common : restart cron] ********************************************************************************
changed: [terraform-vm]

RUNNING HANDLER [docker : restart docker] ******************************************************************************
changed: [terraform-vm]

TASK [Verify Docker installation] **************************************************************************************
ok: [terraform-vm]

TASK [Display Docker info summary] *************************************************************************************
ok: [terraform-vm] => {
    "msg": [
        "Docker Server Version:  Server Version: 29.2.1",
        "Containers:  Containers: 0"
    ]
}

TASK [Provisioning complete] *******************************************************************************************
ok: [terraform-vm] => {
    "msg": "✅ Provisioning completed successfully on terraform-vm"
}

PLAY RECAP *************************************************************************************************************
terraform-vm               : ok=20   changed=10   unreachable=0    failed=0    skipped=1    rescued=0    ignored=0

```

#### Terminal output from SECOND provision.yml run

```yaml
/mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers with common tools and Docker] **************************************************************

TASK [Gathering Facts] *************************************************************************************************
ok: [terraform-vm]

TASK [Show playbook start] *********************************************************************************************
ok: [terraform-vm] => {
    "msg": "Starting provisioning of terraform-vm"
}

TASK [common : Update apt cache] ***************************************************************************************
ok: [terraform-vm]

TASK [common : Install essential packages] *****************************************************************************
ok: [terraform-vm]

TASK [common : Set timezone to UTC] ************************************************************************************
ok: [terraform-vm]

TASK [common : Upgrade all packages (optional - comment out if not needed)] ********************************************
skipping: [terraform-vm]

TASK [docker : Remove old Docker packages] *****************************************************************************
ok: [terraform-vm]

TASK [docker : Install required system packages] ***********************************************************************
ok: [terraform-vm]

TASK [docker : Add Docker GPG key] *************************************************************************************
ok: [terraform-vm]

TASK [docker : Add Docker repository] **********************************************************************************
ok: [terraform-vm]

TASK [docker : Install Docker packages] ********************************************************************************
ok: [terraform-vm]

TASK [docker : Install Python Docker module] ***************************************************************************
ok: [terraform-vm]

TASK [docker : Ensure Docker service is running and enabled] ***********************************************************
ok: [terraform-vm]

TASK [docker : Add user to docker group] *******************************************************************************
ok: [terraform-vm]

TASK [docker : Check Docker version] ***********************************************************************************
ok: [terraform-vm]

TASK [docker : Display Docker version] *********************************************************************************
ok: [terraform-vm] => {
    "msg": "Installed Docker version 29.2.1, build a5c7197"
}

TASK [Verify Docker installation] **************************************************************************************
ok: [terraform-vm]

TASK [Display Docker info summary] *************************************************************************************
ok: [terraform-vm] => {
    "msg": [
        "Docker Server Version:  Server Version: 29.2.1",
        "Containers:  Containers: 0"
    ]
}

TASK [Provisioning complete] *******************************************************************************************
ok: [terraform-vm] => {
    "msg": "✅ Provisioning completed successfully on terraform-vm"
}

PLAY RECAP *************************************************************************************************************
terraform-vm               : ok=18   changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0

```

#### Analysis: What changed first time? What didn't change second time?
**First Run Analysis (10 changes):**

Based on the terminal output, these tasks reported **"changed"** during the first run:

| Task | Why It Changed |
|------|----------------|
| **common: Update apt cache** | Package cache was outdated (older than 3600 seconds) |
| **common: Install essential packages** | Required packages (curl, git, vim, etc.) were not installed |
| **common: Set timezone to UTC** | Timezone was not set to UTC (probably default) |
| **docker: Add Docker GPG key** | Docker GPG key was missing from system keyring |
| **docker: Add Docker repository** | Docker repository not configured in sources.list |
| **docker: Install Docker packages** | Docker CE, CLI, and containerd were not installed |
| **docker: Install Python Docker module** | Python docker module missing for Ansible integration |
| **docker: Add user to docker group** | User 'ubuntu' was not in docker group |
| **handler: restart cron** | Triggered by timezone change to apply new timezone |
| **handler: restart docker** | Triggered by Docker installation to start the service |

**Tasks that remained "ok" (no change):**
- `docker: Remove old Docker packages` - No old packages found
- `docker: Install required system packages` - Prerequisites already present
- `docker: Ensure Docker service is running` - Service started by handler
- `docker: Check Docker version` - Read-only check with `changed_when: false`

---

**Second Run Analysis (0 changes):**

During the second run, **ALL** tasks reported **"ok" (green)** with **zero changes** because:

| Task | Why It Didn't Change |
|------|---------------------|
| **Update apt cache** | Cache was still fresh (`cache_valid_time: 3600` prevented update) |
| **Install essential packages** | All packages were already present at desired versions |
| **Set timezone** | Timezone already set to UTC from first run |
| **Add Docker GPG key** | Key already exists in keyring |
| **Add Docker repository** | Repository already configured |
| **Install Docker packages** | Docker already installed at correct version |
| **Install Python Docker module** | Python module already installed |
| **Add user to docker group** | User already in docker group |
| **All handlers** | No tasks reported changes, so handlers were not triggered |

**Key Observation:**
- **First run:** `ok=20 changed=10` - System was configured from scratch
- **Second run:** `ok=18 changed=0` - System already in desired state
- **Skipped tasks:** 1 (the optional upgrade task) in both runs

#### Explanation: What makes your roles idempotent?
Ansible roles achieve idempotency through **declarative state management** - each module checks the current state before making changes:

### Key Mechanisms:

1. **State-based modules** (apt, user, systemd, etc.)
   ```yaml
   - name: Install package
     apt:
       name: git
       state: present  # Checks if installed first
2. **Conditional execution**

- Modules verify current state vs. desired state
- Changes only made if mismatch exists

3. **Smart cache handling**

```yaml
- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600  # Only updates if cache is stale
```
4. **Handlers triggered only on actual changes**

```yaml
notify: restart docker  # Only runs if installation CHANGED something
```
5. **Read-only tasks with changed_when: false**

```yaml
- name: Check version
  command: docker --version
  changed_when: false  # Never reports as changed
```
**Result:**
- First run: 10 changes (system configured)
- Second run: 0 changes (system already in desired state)
- Running the playbook 100 times produces identical results with no unnecessary changes.

### Ansible Vault Usage

#### How you store credentials securely
I use **Ansible Vault** to encrypt sensitive data like Docker Hub credentials. The vault file `group_vars/all.yml` contains all secrets in encrypted form.

1. Vault Password Management Strategy
- The vault password is **not stored in the code repository**
- For local development, I enter the password manually using `--ask-vault-pass`
- For automation, a password file could be used (but not committed to git)
- The password is memorized and stored securely offline

2. Example of Encrypted File
```bash
$ head -n 2 group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
66386439653236336...  # encrypted content - not human readable
```

#### Vault password management strategy
My strategy for managing the Ansible Vault password:

1. Password Creation: I created a strong, unique password for the vault during initialization with ansible-vault create group_vars/all.yml

2. Storage: The vault password is never stored in the code repository. It is:
- Memorized personally
- Stored in a secure password manager (not in plain text files)
- Not committed to git (added to .gitignore if accidentally created)

3. Usage Methods:
- Interactive mode: --ask-vault-pass flag when running playbooks (used in this lab)

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```
- Password file (for automation): Can use --vault-password-file but the file is never committed to git
- Environment variable: Can set ANSIBLE_VAULT_PASSWORD_FILE for CI/CD pipelines

4.Security Practices:
- Password is shared only with team members who need access
- Different vault passwords for different environments (dev/staging/production)
- Regular password rotation following security policies

#### Example of encrypted file (show it's encrypted!)
Here's what my encrypted vault file looks like:

```bash
/mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible$ cat group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
35326163633362356331306535336133346235313034616165353333313938393338313738653066
3965613231333138663831303265363736663335613335310a616134356663643838343737616439
35396336626339393161363333336661313165326139316661336539626638643064613461623237
3464303930323737610a356466656366326235333730386130623666393535663538636462363931
35316161303939346664303032336165653134653865646239343031383936343536653163363639
32386266393366373333303262393936373365313332353734396666363536663538343931623833
64633131333266303635626633353331393163656638626239366163306562393666316266363365
32656536656235666362316539643133393063313762306238396361636463613262613331316465
36326530366363323064323233663762663565393833623030396637333965326338623966316430
37353730326132326238336563646263626535353661343766643862336235313230633961306532
63303232643730383466633032333035316561653061666631303764396261323136663130346636
63616631386161336539376337316336343133393530643532666130363762386233626231656534
61353861343838343062636464303662336132316632396234343966313935316430386363373730
63613962373039666132663739393232306365383236323631633065363832376336366665343464
31313835623063623566336138633166393635656165633161373433323938373137383066323062
32343932633033383334376438303839356537383861303139613138396166653661333465303637
33633335343635363831633762363135306666316131303830643266616132333165
```

#### Why Ansible Vault is important

Ansible Vault is critically important for several reasons:

Reason -	Explanation
1. **Security**	- Prevents exposure of sensitive data (passwords, API keys, tokens) in code repositories. Without Vault, credentials would be in plain text for anyone with repository access.
2. **Compliance** -	Meets security requirements and standards (PCI DSS, HIPAA, GDPR) that mandate encryption of sensitive data.
3. **Separation** of Concerns -	Keeps configuration logic separate from sensitive data. The same playbook can use different vault passwords for different environments.
4. **Version Control Safety** -	Allows storing all configuration in git without fear of credential leaks. Even if repository becomes public, secrets remain encrypted.
5. **Access Control** -	Vault password acts as a simple but effective gatekeeper - only team members with the password can decrypt and view secrets.
6. **Audit Trail**	- Changes to encrypted files are tracked in version control, but contents remain hidden. You can see that a credential changed, but not what it changed to.

Real-world importance demonstrated in this lab:
- Docker Hub credentials (dockerhub_username and dockerhub_password) are stored encrypted
- Even though the entire ansible directory is in version control, these secrets are protected
- The playbook runs successfully using --ask-vault-pass without exposing credentials in logs
- If I accidentally push code to a public repository, my Docker Hub account remains secure

### Deployment Verification

##### Terminal output from deploy.yml run
```bash
/mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml --ask-vault-pass
Vault password:

PLAY [Deploy application] **************************************************************************************

TASK [Gathering Facts] *****************************************************************************************
ok: [terraform-vm]

TASK [app_deploy : Create application directory] ***************************************************************
changed: [terraform-vm]

TASK [app_deploy : Log in to Docker Hub] ***********************************************************************
changed: [terraform-vm]

TASK [app_deploy : Pull Docker image] **************************************************************************
changed: [terraform-vm]

TASK [app_deploy : Check if container is running] **************************************************************
ok: [terraform-vm]

TASK [app_deploy : Stop existing container] ********************************************************************
skipping: [terraform-vm]

TASK [app_deploy : Remove old container] ***********************************************************************
skipping: [terraform-vm]

TASK [app_deploy : Run new container] **************************************************************************
changed: [terraform-vm]

TASK [app_deploy : Wait for application to be ready] ***********************************************************
ok: [terraform-vm]

TASK [app_deploy : Verify health endpoint] *********************************************************************
ok: [terraform-vm]

TASK [app_deploy : Display health check result] ****************************************************************
ok: [terraform-vm] => {
    "msg": [
        "Health check: ✅ PASSED",
        "Application is running on port 5000"
    ]
}

TASK [app_deploy : Log out from Docker Hub] ********************************************************************
changed: [terraform-vm]

PLAY RECAP *****************************************************************************************************
terraform-vm               : ok=10   changed=5    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0

```

#### Container status: docker ps output
```bash
/mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible$ ansible webservers -m shell -a "docker ps" --ask-vault-pass
Vault password:
terraform-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                   COMMAND           CREATED          STATUS          PORTS                                         NAMES
b2595990efe0   mariablood/devops-info-service:latest   "python app.py"   12 minutes ago   Up 12 minutes   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   devops-info-service
```
#### Health check verification: curl outputs
```bash
/mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible$ curl http://89.169.133.138:5000/health
{"status":"healthy","timestamp":"2026-02-24T22:47:25.431336Z","uptime_seconds":831,"service":"devops-info-service","version":"1.0.0"}maria@MaryI:/mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible$  curl http://8 curl http://89.169.133.138:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"b2595990efe0","platform":"Linux","platform_version":"5.15.0-170-generic","architecture":"x86_64","cpu_count":2,"python_version":"3.12.12"},"runtime":{"uptime_seconds":841,"uptime_human":"0 hours, 14 minutes","current_time":"2026-02-24T22:47:35.137114Z","timezone":"UTC"},"request":{"client_ip":"188.130.155.169","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/docs","method":"GET","description":"Swagger documentation"},{"path":"/redoc","method":"GET","description":"ReDoc documentamaria@MaryI:/mnt/d/innopolis/third_course/devops/DevOps-Core-Course/ansible$ curl -v http://89.169.133.138:5000/health 2>&1 | head -n 10ad -n 10
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0*   Trying 89.169.133.138:5000...
* Connected to 89.169.133.138 (89.169.133.138) port 5000
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0> GET /health HTTP/1.1
> Host: 89.169.133.138:5000
> User-Agent: curl/8.5.0
> Accept: */*
>
< HTTP/1.1 200 OK
```

#### Handler execution (if any)
```bash
RUNNING HANDLER [app_deploy : restart app] *********************************************************************
changed: [terraform-vm]
```
- Handler was triggered - the notify: restart app in tasks worked
- Handler executed successfully - status changed means the container was restarted
- Docker CLI works - using shell command instead of Python module solved the API error

### Key Decisions

1. **Why use roles instead of plain playbooks?**
Roles provide modular organization by separating configuration into reusable components. This makes playbooks cleaner, easier to debug, and simpler to maintain compared to monolithic playbooks with hundreds of lines of code.

2. **How do roles improve reusability?**
Roles can be shared across different projects without modification. For example, my `common` and `docker` roles can be used in any future project that needs Ubuntu server setup or Docker installation.

3. **What makes a task idempotent?**
A task is idempotent when it checks the current state before making changes. Ansible modules like `apt`, `user`, and `file` verify if a package, user, or directory already exists before creating it, ensuring the same result no matter how many times the playbook runs.

4. **How do handlers improve efficiency?**
Handlers run only when notified by tasks that actually made changes, and execute only once at the end of the play even if notified multiple times. This prevents unnecessary service restarts and speeds up deployment.

5. **Why is Ansible Vault necessary?**
Ansible Vault encrypts sensitive data like passwords and API keys so they can be safely stored in version control. Without it, credentials would be exposed in plain text, creating serious security risks.

### Challenges and Solutions

| Challenge | Solution |
|-----------|----------|
| **SSH connection issues** | Fixed by copying correct SSH key to WSL and setting proper permissions (`chmod 600`) |
| **Docker Hub login errors** | Replaced `docker_login` module with shell command `echo "{{ password }}" \| docker login -u {{ username }} --password-stdin` |
| **YAML syntax errors** | Fixed indentation and removed problematic Jinja2 templating in `env` section |
| **Docker Python API errors** | Switched from `docker_container` module to native shell commands throughout the role |
| **Vault file permission issues on Windows** | Worked around by editing vault files in `/tmp` or `~` and copying back to project |
| **Handler not triggering** | Changed handlers from `docker_container` to `shell` commands and verified `notify` statements |
| **Idempotency verification** | Successfully achieved with second run showing `changed=0` |

