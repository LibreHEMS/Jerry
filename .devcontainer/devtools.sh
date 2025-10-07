#!/bin/bash
set -e

# give default user permission to /usr/local 
chmod -R +007 /usr/local/

# Install Trivy repo
cat > /etc/yum.repos.d/trivy.repo <<'EOF'
[trivy]
name=Trivy repository
baseurl=https://aquasecurity.github.io/trivy-repo/rpm/releases/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://aquasecurity.github.io/trivy-repo/rpm/public.key
EOF

dnf -y update-minimal --security --sec-severity=Important --sec-severity=Critical

# Install trivy, spec-kit and uv (attempt via dnf; if not available, warn and continue)
if ! dnf install -y trivy podman; then
    echo "Warning: one or more packages were not found/installed via dnf. Continuing."
fi

# Clean package cache
dnf clean all