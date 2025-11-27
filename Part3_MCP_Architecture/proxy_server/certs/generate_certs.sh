#!/bin/bash
# Generate self-signed TLS certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=localhost/O=Demo/C=KR" \
  -addext "subjectAltName=DNS:localhost,DNS:proxy-server,IP:127.0.0.1"
echo "Certificates generated: cert.pem, key.pem"
