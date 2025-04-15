---
id: deploying-on-vps
title: Deploying on a server
sidebar_position: 1
---

# Deploying the GenAI Launchpad on a Server

This tutorial provides a step-by-step process for deploying the GenAI Launchpad on a production-ready Linux server.

## Prerequisites

Before proceeding, ensure you have the following:

- A remote server running a Linux distribution (Ubuntu recommended).
- SSH access to the server.
- (Optional) custom domain with access to DNS settings

## Step 1: Connect to the Server

Log in to your remote server via SSH:

```bash
ssh username@remote-ip-address
```

## Step 2: Install Docker

Docker is required to run the Launchpad. Follow the official installation instructions for your Linux
distribution: [Docker Installation Guide](https://docs.docker.com/engine/install/).

For Ubuntu, execute the following commands:

### Set up Docker’s APT Repository

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

### Install Docker

```bash
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Verify Installation

Ensure Docker is installed correctly by running:

```bash
sudo docker run hello-world
```

## Step 3: Clone the Repository

To deploy the Launchpad, clone the repository onto your server. First, add an SSH key to your GitHub repository.

### Generate an SSH Key

Generate a new SSH key pair:

```bash
ssh-keygen
```

Follow the prompts. If you do not wish to set a passphrase, press `Enter` to skip.

Print the public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the output, as it will be needed in the next step.

### Add the SSH Key to GitHub

1. Navigate to your GitHub repository.
2. Open **Settings**.
3. In the left menu, go to **Security > Deploy keys**.
4. Click **Add deploy key** and provide:
    - **Title:** `genai-launchpad-prod`
    - **Key:** Paste the copied public key.
5. Click **Add key**.

### Clone the Repository

Run the following command to clone the repository to the server:

```bash
cd /opt && git clone git@github.com:jorisebbelaar/genai-launchpad.git
```

## Step 4: Configure Environment Variables

Ensure all necessary `.env` files are correctly set up within the `app/` and `docker/` directories. It is crucial to
replace default credentials with secure values.

## Step 5: Enable HTTPS (Optional)

If you intend to use HTTPS, you must have a domain and configure the appropriate DNS settings.

### Configure Domain

1. Create an **A record** in your domain's DNS settings, pointing to your server's IP address.
2. Modify the `.env` file in the `docker/` directory to include:

```dotenv
CADDY_DOMAIN=https://yourdomain.com
```

## Step 6: Start the Application

Navigate to the `docker/` directory:

```bash
cd /opt/genai-launchpad/docker
```

Run the startup script:

```bash
./start.sh
```

## Conclusion

Your GenAI Launchpad instance is now successfully deployed on your server!

