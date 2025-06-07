#!/bin/bash
set -e

# give default user permission to /usr/local 
chmod -R +007 /usr/local/

# Install Trivy repo
<<EOF cat >> /etc/yum.repos.d/trivy.repo
[trivy]
name=Trivy repository
baseurl=https://aquasecurity.github.io/trivy-repo/rpm/releases/\$basearch/
gpgcheck=1
enabled=1
gpgkey=https://aquasecurity.github.io/trivy-repo/rpm/public.key
EOF

dnf -y update-minimal --security --sec-severity=Important --sec-severity=Critical && \
# Install trivy package
dnf install trivy -y; \
# Clean package cache
dnf clean all