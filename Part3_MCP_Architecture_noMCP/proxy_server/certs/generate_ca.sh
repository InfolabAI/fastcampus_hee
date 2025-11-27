#!/bin/bash
# Generate self-signed CA and server certificate for certificate pinning
set -e
cd "$(dirname "$0")"

echo "=== Generating CA and Server Certificate ==="

# 1. Generate CA private key and certificate
openssl genrsa -out ca-key.pem 4096
openssl req -new -x509 -days 365 -key ca-key.pem -out ca.pem \
    -subj "/CN=MCP-Demo-CA/O=FastCampus/C=KR"

# 2. Generate server private key and CSR
openssl genrsa -out key.pem 2048
openssl req -new -key key.pem -out server.csr \
    -subj "/CN=localhost/O=MCP-Proxy/C=KR"

# 3. Create extension file for SAN
cat > server.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = proxy-server
IP.1 = 127.0.0.1
EOF

# 4. Sign server certificate with CA
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca-key.pem \
    -CAcreateserial -out cert.pem -days 365 -extfile server.ext

# 5. Cleanup
rm -f server.csr server.ext ca.srl

echo ""
echo "=== Certificate Generation Complete ==="
echo "CA Certificate:     ca.pem      (use for certificate pinning)"
echo "Server Certificate: cert.pem"
echo "Server Key:         key.pem"
echo ""
echo "For certificate pinning, clients should verify against ca.pem"
