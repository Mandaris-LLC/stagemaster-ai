#!/bin/bash
# Replace EB's default nginx config with our custom one
# The .platform/nginx/nginx.conf convention doesn't work with the Docker platform,
# so we copy it manually and reload nginx.

set -e

CUSTOM_CONF="/var/app/current/.platform/nginx/nginx.conf"
NGINX_CONF="/etc/nginx/nginx.conf"

if [ -f "$CUSTOM_CONF" ]; then
    echo "Replacing nginx config with custom configuration..."
    cp "$CUSTOM_CONF" "$NGINX_CONF"
    nginx -t
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
        echo "Nginx config replaced and reloaded."
    else
        systemctl start nginx
        echo "Nginx config replaced and started."
    fi
else
    echo "WARNING: Custom nginx config not found at $CUSTOM_CONF"
    exit 1
fi
