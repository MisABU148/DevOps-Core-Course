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
Workflow Architecture
The CI/CD pipeline is implemented using GitHub Actions with a two-job workflow that ensures code quality before deployment.

```yaml
name: Ansible Deployment

on:
  push:
    branches: [ main, master, lab06 ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deploy.yml'

jobs:
  lint:
    name: 🔍 Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install ansible ansible-lint
      - name: Run ansible-lint
        run: cd ansible && ansible-lint playbooks/*.yml

  deploy:
    name: 🚀 Deploy Application
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Ansible
        run: pip install ansible
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts
      - name: Deploy with Ansible
        run: |
          cd ansible
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
          ansible-playbook playbooks/deploy.yml \
            -i inventory/hosts.ini \
            --vault-password-file /tmp/vault_pass
      - name: Verify Deployment
        run: |
          sleep 10
          curl -f http://${{ secrets.VM_HOST }}:5000/health
```
Setup Steps
Step	- Description	- Command/Configuration
1. Create workflow file -	.github/workflows/ansible-deploy.yml -	As shown above
2. Configure GitHub - Secrets	- Repository → Settings → Secrets → Actions	
```bash
SSH_PRIVATE_KEY	Private SSH key for VM access	cat ~/.ssh/id_rsa
VM_HOST	VM IP address	46.21.244.23
VM_USER	SSH username	ubuntu
ANSIBLE_VAULT_PASSWORD	Vault decryption password	Your vault password
```
3. Add status badge	In README.md	![Ansible Deployment](https://github.com/MisABU148/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)
Evidence of Automated Deployments
Screenshot 1: Successful Workflow Run
https://screenshots/github-actions-success.png
Complete workflow with lint and deploy jobs passing

Screenshot 2: Lint Job Logs
https://screenshots/ansible-lint.png
Shows successful syntax checking

Screenshot 3: Deploy Job Logs
https://screenshots/ansible-deploy.png
Playbook execution with vault decryption

Screenshot 4: Verification Step
https://screenshots/health-check.png
Curl command confirming application is healthy

Screenshot 5: README Badge
https://screenshots/readme-badge.png
Passing badge in repository README


## Testing Results - All test scenarios, idempotency verification, application accessibility
All Test Scenarios
Scenario 1: Normal Deployment (Wipe NOT Run)
Command:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
Screenshot 1.1: Ansible Output
```
screenshots/Local scenario1.png
Shows skipping: [terraform-vm] for wipe tasks

Screenshot 1.2: VM Verification
screenshots/VM scenario 1.png

```text
$ ssh ubuntu@46.21.244.23 "docker ps && curl -s http://localhost:5000/health"
CONTAINER ID   IMAGE                                   STATUS         PORTS
5865f79138d1   mariablood/devops-info-service:latest   Up 2 minutes   0.0.0.0:5000->5000/tcp
{"status":"healthy","version":"1.0.0"}
```
Result: Application deployed successfully, wipe skipped

Scenario 2: Wipe Only (Remove Existing Deployment)
Command:

```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass
```
Screenshot 2.1: Ansible Output
screenshots/local scenario 2.png

```text
TASK [web_app : Stop and remove containers] ******************
changed: [terraform-vm]
TASK [web_app : Remove application directory] ****************
changed: [terraform-vm]
PLAY RECAP ***************************************************
terraform-vm : ok=6 changed=3 failed=0
```
Screenshot 2.2: VM Verification
screenshots/vm scenario 2.png

```text
$ ssh ubuntu@46.21.244.23 "docker ps && ls -la /opt/ | grep devops"
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
# (empty)
# (no output from grep - directory removed)
```
Result: Application completely removed, no deployment

Scenario 3: Clean Reinstallation (Wipe → Deploy)
Command:

```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass
```
Screenshot 3.1: Ansible Output - Wipe Phase
screenshots/local ansible scenario 3.png
Shows wipe tasks executing first

Screenshot 3.2: Ansible Output - Deploy Phase
screenshots/vm scenario 3.png
Shows deployment tasks after wipe

```text
$ ssh ubuntu@46.21.244.23 "docker ps && curl -s http://localhost:5000/health"
CONTAINER ID   IMAGE                                   STATUS         PORTS
6a081db90d46   mariablood/devops-info-service:latest   Up 1 minute    0.0.0.0:5000->5000/tcp
{"status":"healthy","uptime_seconds":61}
```
Result: Old app wiped, fresh app deployed and running

Scenario 4a: Safety Check (Tag Only, No Variable)
Command:

```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-vault-pass
```
Screenshot 4a: Ansible Output
screenshots/local ansible scenario 4.png

```text
TASK [web_app : Include wipe tasks] **************************
skipping: [terraform-vm]  # Wipe blocked by when condition
```
Result: Wipe tasks correctly skipped (protected by variable)

Scenario 4b: Safety Check (Variable True, Wipe Tag Only)
Command:

```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass
```

```text
TASK [web_app : Stop and remove containers] ******************
changed: [terraform-vm]
PLAY RECAP ***************************************************
terraform-vm : ok=6 changed=3 failed=0  # No deploy tasks!
```
Screenshot 4b.2: VM Verification
screenshots/vm scenario 4.png

```text
$ ssh ubuntu@46.21.244.23 "docker ps && ls -la /opt/ | grep devops"
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
# (empty - container removed)
```
Result: Only wipe executed, deployment correctly skipped

Idempotency Verification
First Run (with changes):

```text
PLAY RECAP ***************************************************
terraform-vm : ok=12 changed=5 failed=0
```
Second Run (no changes):

```text
PLAY RECAP ***************************************************
terraform-vm : ok=12 changed=0 failed=0
```
Screenshot: Idempotency Test
Second run shows changed=0 - no unnecessary changes

Application Accessibility
Health Check Endpoint:

```bash
curl http://46.21.244.23:5000/health
```
Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-03-05T20:03:20.028776Z",
  "uptime_seconds": 61,
  "service": "devops-info-service",
  "version": "1.0.0"
}
```


## Challenges & Solutions - Difficulties encountered and how you solved them

- Challenge 1: SSH Key Permissions
Problem:

text
```Permissions 0644 for '/home/maria/.ssh/id_rsa' are too open.
This private key will be ignored.
```
Solution:

bash
```chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
```
- Challenge 2: Health Check Failing After Deployment
Problem: Application deployed but health check returned connection reset

Solution:

Fixed port mapping (container was listening on 5000, but compose mapped 5000:8000)

Added wait time for application startup

Implemented retry logic

```yaml
- name: "Wait for application to be ready"
  wait_for:
    port: "{{ app_port }}"
    delay: 5
    timeout: 60
    sleep: 5
```

- Challenge 3: YAML Formatting Errors
Problem:

```text
yaml.parser.ParserError: while parsing a block collection
expected <block end>, but found '<block mapping start>'
```
Solution:
- Fixed indentation in Jinja2 template
- Ensured consistent spacing (2 spaces, no tabs)
- Added conditional checks for empty variables

```yaml
# Before (problematic)
    environment:
            TZ: "UTC"  # Wrong indentation

# After (correct)
    environment:
      TZ: "UTC"
      {% if environment_variables is defined %}
      {% for key, value in environment_variables.items() %}
      {{ key }}: "{{ value }}"
      {% endfor %}
      {% endif %}
```

### Research Questions
1. What are the security implications of storing SSH keys in GitHub Secrets?
Storing SSH keys in GitHub Secrets protects them from being exposed in the repository because they are encrypted and only accessible during workflow execution. However, there are still risks: if a workflow is compromised (e.g., through malicious code in a pull request), the key could potentially be used during the run. It is recommended to use least-privilege keys, restrict repository access, and rotate the keys regularly.

2. How would you implement a staging → production deployment pipeline?
I would create a CI/CD pipeline with separate stages. First, the application is built and tested. Then it is deployed automatically to the staging environment where integration or acceptance tests are executed. If everything passes, a manual approval step (or protected environment in GitHub) triggers deployment to production. This ensures that production deployments only happen after validation in staging.

3. What would you add to make rollbacks possible?
To enable rollbacks, I would deploy versioned artifacts (e.g., tagged Docker images or release builds) and keep previous versions available. The deployment process should allow selecting a previous version and redeploying it quickly. Additionally, infrastructure tools like Ansible or Kubernetes can support rollbacks by redeploying the last known stable version.

4. How does a self-hosted runner improve security compared to a GitHub-hosted runner?
A self-hosted runner runs inside your own infrastructure, giving you full control over the environment, network access, and security policies. This allows restricting access to internal systems, limiting outbound connections, and applying organization-specific security controls. In contrast, GitHub-hosted runners run in GitHub’s shared infrastructure and cannot directly access private internal resources.