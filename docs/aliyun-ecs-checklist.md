# Aliyun ECS checklist for Lumia ScriptorRAG

Use this checklist after logging in to Aliyun Console.

## Console path

Open:

```text
https://ecs.console.aliyun.com/
```

Go to:

```text
Elastic Compute Service -> Instances
```

## Information to collect

Copy these fields from the ECS instance page:

- Region
- Instance ID
- Public IPv4 address
- Private IPv4 address
- Operating system
- CPU / memory
- Disk size
- Security group name

## Required security group rules

Make sure these inbound ports are allowed:

- `22/tcp` for SSH
- `80/tcp` for HTTP
- `443/tcp` for HTTPS
- `8080/tcp` only if you want to test the app directly without Nginx

For production, expose `80` and `443` publicly, and keep `8080` internal if possible.

## Recommended architecture

If `zclum.com` is already hosted by Vercel, use:

```text
zclum.com        -> existing website or lightweight entry
api.zclum.com    -> Aliyun ECS running Lumia ScriptorRAG
```

If you want this app to own the whole domain:

```text
zclum.com        -> Aliyun ECS Nginx -> Lumia ScriptorRAG
```

## DNS records

For full-domain deployment:

```text
A     zclum.com        <ECS_PUBLIC_IP>
A     www.zclum.com    <ECS_PUBLIC_IP>
```

For API subdomain deployment:

```text
A     api.zclum.com    <ECS_PUBLIC_IP>
```

## SSH command template

```bash
ssh root@<ECS_PUBLIC_IP>
```

If the server uses Ubuntu user:

```bash
ssh ubuntu@<ECS_PUBLIC_IP>
```

## First deployment command

After SSH login:

```bash
curl -fsSL https://raw.githubusercontent.com/clementzhang29/lumia-scriptor-rag/main/deploy/server/deploy_ubuntu.sh -o deploy_ubuntu.sh
chmod +x deploy_ubuntu.sh
DOMAIN=zclum.com ENABLE_HTTPS=0 ./deploy_ubuntu.sh
```

Enable HTTPS after DNS points to the ECS public IP:

```bash
DOMAIN=zclum.com ENABLE_HTTPS=1 EMAIL=you@example.com ./deploy_ubuntu.sh
```

