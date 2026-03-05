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

## Docker Compose Migration
### 2.1 Why Docker Compose?

Advantages over docker run:

| Feature | docker run | Docker Compose |
|---------|------------|----------------|
| **Declarative configuration** | Command-line flags only | YAML file defines desired state |
| **Multi-container management** | Manual each container | Single command for all services |
| **Networks & Volumes** | Manual creation | Declarative in compose file |
| **Environment variables** | --env flags | .env files, variable substitution |
| **Easy updates** | Stop, remove, run new | Change config and `docker-compose up` |
| **Production consistency** | Manual steps error-prone | Reproducible deployments |
| **Dependencies** | Manual start order | `depends_on` configuration |

Template Structure
```yaml
# roles/web_app/templates/docker-compose.yml.j2
version: '3.8'
services:
  {{ app_name }}:
    image: "{{ docker_image }}:{{ docker_tag }}"
    container_name: "{{ app_name }}"
    restart: unless-stopped
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      {% for key, value in environment_variables.items() %}
      {{ key }}: "{{ value }}"
      {% endfor %}
  ```
Key variables:
- app_name: devops-info-service
- docker_image: mariablood/devops-info-service
- app_port: 5000
- app_internal_port: 8000
- environment_variables: TZ, LOG_LEVEL

Role Dependencies
```yaml
# roles/web_app/meta/main.yml
dependencies:
  - role: docker
  - role: common
```
- Automatic execution: Docker installs when running web_app role
- Order: common → docker → web_app

Before/After Comparison\
Aspect -	Before (docker run)	- After (Docker Compose)\
Configuration - 	Command-line flags -	Declarative YAML\
Management -	Manual commands -	Automated via playbook\
Updates -	Stop + remove + run -	docker-compose up\
Idempotency -	Manual checks	- Built-in\


Before (app_deploy)
```bash
docker run -d --name devops-app -p 5000:8000 -e TZ=UTC mariablood/devops-info-service
```
After (web_app)

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```
#### Generates /opt/devops-info-service/docker-compose.yml
Results
```text
PLAY RECAP **************************************************
terraform-vm : ok=18 changed=4 failed=0
```
Verification:

```bash
$ curl http://46.21.244.23:5000/health
{"status":"healthy"}
```
Benefits achieved:
- Declarative configuration
- Idempotent deployments
- Automatic dependency resolution
- Easy updates and maintenance

## Wipe Logic - Implementation details, variable + tag approach, test results

### Why use both variable AND tag? (Double safety mechanism)

Using both a variable (`web_app_wipe: true`) and a tag (`--tags web_app_wipe`) provides **two-factor protection** against accidental deletions:

| Component | Purpose | Protection Level |
|-----------|---------|------------------|
| **Variable** | Prevents wipe during normal runs | Default `false` |
| **Tag** | Requires explicit intent | Only runs when specified |

**Without both safeguards:**
- If only variable: Could accidentally run wipe during normal deploy
- If only tag: Could accidentally wipe when running with tags

**With double safety:**
```bash
# Wipe only runs when BOTH conditions are met:
# 1. Variable is true (web_app_wipe=true)
# 2. Tag is specified (--tags web_app_wipe)
```
# Safe examples:

ansible-playbook deploy.yml                    #  No wipe (no variable, no tag)\
ansible-playbook deploy.yml --tags web_app_wipe #  No wipe (variable false)\
ansible-playbook deploy.yml -e "web_app_wipe=true" #  Clean reinstall (wipe + deploy)\
ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe #  Wipe only

### What's the difference between never tag and this approach?
Aspect -	never tag -	Variable + Tag approach\
Execution	- Never runs unless explicitly requested -	Runs only when variable AND tag match\
Control	Single - condition (tag only) -	Double condition (variable AND tag)\
Flexibility	- Only on/off -	Multiple combinations (wipe only, clean reinstall)\
Default behavior -	Always skipped -	Configurable via defaults\
Use case -	Dangerous operations -	Conditional cleanup with options

### When would you want clean reinstallation vs. rolling update?
Scenario	- Clean Reinstallation	- Rolling Update\
Configuration changes -  Major config overhaul	- Minor config tweaks\
Version upgrade	- Major version jump (v1 → v2)	- Patch version (v1.0 → v1.1)\
Database schema changes	- Breaking changes	- Compatible changes\
Testing	- Fresh state for testing	- May have issues\
Production	- Causes downtime	- Zero downtime\
Recovery	- Corrupted installation	- May not fix corruption\
Disk space	- Cleanup orphaned resources	- May leave old images

### How would you extend this to wipe Docker images and volumes too?
1. Update defaults/main.yml (add control variables)
```yaml
# Wipe extensions
web_app_wipe_volumes: false   # Remove persistent data volumes
web_app_wipe_images: false     # Remove Docker images
web_app_wipe_prune: false      # Full Docker system prune
```
2. Extend wipe.yml (add new tasks)
```yaml
- name: "Remove Docker volumes"
  community.docker.docker_volume:
    name: "{{ item }}"
    state: absent
  loop:
    - "{{ app_name }}_data"
    - "{{ app_name }}_logs"
  when: web_app_wipe_volumes | bool
  tags: web_app_wipe

- name: "Remove Docker images"
  community.docker.docker_image:
    name: "{{ docker_image }}"
    tag: "{{ docker_tag | default('latest') }}"
    state: absent
    force_remove: yes
  when: web_app_wipe_images | bool
  tags: web_app_wipe

- name: "Prune unused Docker resources"
  community.docker.docker_prune:
    containers: yes
    images: yes
    networks: yes
    volumes: "{{ web_app_wipe_volumes }}"
    builder_cache: yes
  when: web_app_wipe_prune | bool
  tags: web_app_wipe
```
3. Usage Examples

# Basic wipe (containers + files only)
```bash
ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```

# Wipe + remove volumes (complete data cleanup)
```bash
ansible-playbook deploy.yml \
  -e "web_app_wipe=true web_app_wipe_volumes=true" \
  --tags web_app_wipe
```

# Full cleanup (containers + volumes + images)
```bash
ansible-playbook deploy.yml \
  -e "web_app_wipe=true web_app_wipe_volumes=true web_app_wipe_images=true" \
  --tags web_app_wipe
```

# Complete Docker system prune
```bash
ansible-playbook deploy.yml \
  -e "web_app_wipe=true web_app_wipe_prune=true" \
  --tags web_app_wipe
```
4. Benefits
- Complete cleanup - No orphaned resources
- Disk space recovery - Remove unused images
- Fresh start - Clean slate for testing
- Flexible control - Choose what to wipe via variables


## Wipe Logic - Implementation Summary

### Implementation Details

| Component | File | Purpose |
|-----------|------|---------|
| Wipe tasks | `roles/web_app/tasks/wipe.yml` | Remove containers, files, directory |
| Main include | `roles/web_app/tasks/main.yml` | Include wipe at beginning |
| Default variable | `roles/web_app/defaults/main.yml` | `web_app_wipe: false` |
| Tag | `web_app_wipe` | Selective execution |

### Variable + Tag Approach (Double Safety)

```yaml
# In main.yml
- include_tasks: wipe.yml
  when: web_app_wipe | default(false) | bool  # Variable control
  tags: web_app_wipe  # Tag control
```
Why both?
- Variable (web_app_wipe: false) - prevents accidental wipes during normal runs
- Tag (--tags web_app_wipe) - requires explicit intent
- Together - wipe only runs when BOTH conditions are met

Test Results Summary
Scenario	- Command	Result -	Status\
1: Normal deploy -	ansible-playbook deploy.yml	-  Wipe skipped, app running	\
2: Wipe only	- ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe	-  App removed, no deploy\	
3: Clean reinstall -	ansible-playbook deploy.yml -e "web_app_wipe=true"	-  Wipe → Deploy, fresh app	\
4a: Safety check	- ansible-playbook deploy.yml --tags web_app_wipe	-  Wipe blocked (variable false)\	
4b: Safety check	- ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe	 - Only wipe, no deploy	

Key Achievements
- Double safety mechanism - Variable AND tag protection
- No accidental wipes - Verified in all test scenarios
- Clean reinstallation - Wipe → Deploy顺序 correct
- Idempotent operations - Safe to run multiple times
- Selective execution - Run wipe only when needed
- Extensible design - Easy to add volume/image cleanup

## CI/CD Integration - Workflow architecture, setup steps, evidence of automated deployments

## Testing Results - All test scenarios, idempotency verification, application accessibility

## Challenges & Solutions - Difficulties encountered and how you solved them

