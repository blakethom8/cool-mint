# Deployment guide

Brief guide on how to deploy the GenAI Launchpad on any virtual machine running a Linux distribution.

## Virtual machine requirements

1. Hardware requirements:
    - minimum 4gb RAM.
2. Software requirements:
    - Docker, docker compose
    - Git
    - Any text editor (vim, vi, nano etc.)
3. SSH user with root access.
3. Custom domain that is pointed to your virtual machine.
4. Make sure that the default ports for http and https are not blocked by your firewall. So ports 80 and 443 should be
   publicly accessible. This is mandatory for setting up a SSL certificate.

## Deployment

### Overview

1. SSH into the virtual machine.
2. Clone repository.
3. Set .env files.
4. Build and run.
5. Apply database migrations.
6. Check.

### Step by step

#### 1. SSH into the virtual machine

```
ssh username@hostname-or-ip
```

#### 2. Clone your Git repository
```
cd /opt
git clone git@github.com:datalumina/genai-launchpad.git
```

#### 3. Create .env files

##### Docker

```
cd /opt/genai-launchpad/docker
cp .env.example .env
```

Make sure to update the following variables:

1. DATABASE_PASSWORD (for obvious security reasons)
2. CADDY_DOMAIN: Your custom domain here

##### Backend

```
cd /opt/genai-launchpad/app
cp .env.example .env
```

Make sure to update the database password for security reasons.

#### 4. Build and run

Go to the docker folder
```
cd /opt/genai-launchpad/docker
```
Make sure the script has execute permission
```
sudo chmod +x start.sh
```
Execute script
```
./start.sh
```
#### 5. Apply database migrations
Go to the backend folder
```
cd /opt/genai-launchpad/app
```
Make sure the script has execute permission
```
sudo chmod +x migrate.sh
```
Execute script
```
./migrate.sh
```

#### 6. Check

Everything should be up and running now. Run the command following command to check if all docker containers are
running:

```
docker ps
```