#!/bin/bash
# Test script for Tenant B - requires Infisical setup
# Run with: infisical run -- bash test_tenant_b.sh
set -e
cd "$(dirname "$0")"

echo "=== Test Tenant B ==="
PROXY_URL="${PROXY_URL:-https://localhost:8443}"
CA_CERT="proxy_server/certs/ca.pem"

# Check JWT_SECRET from Infisical
if [ -z "$JWT_SECRET" ]; then
    echo "[ERROR] JWT_SECRET not set. Run with: infisical run -- bash test_tenant_b.sh"
    exit 1
fi
echo "[OK] JWT_SECRET loaded from Infisical"

# Check CA certificate
if [ ! -f "$CA_CERT" ]; then
    echo "[ERROR] CA certificate not found. Run: bash proxy_server/certs/generate_ca.sh"
    exit 1
fi
echo "[OK] CA certificate found: $CA_CERT"

# Generate JWT for tenant_b
TOKEN=$(python3 -c "
from authlib.jose import jwt
from datetime import datetime, timedelta
import os
header = {'alg': 'HS256'}
payload = {'tenant': 'tenant_b', 'exp': datetime.utcnow() + timedelta(minutes=5), 'iat': datetime.utcnow()}
print(jwt.encode(header, payload, os.environ['JWT_SECRET']).decode())
")

# Test 1: Insert to Backend B (should succeed)
echo "[Test 1] Tenant B insert to Backend B..."
RESP=$(curl -s --cacert "$CA_CERT" -X POST "$PROXY_URL/mcp/b" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"method": "insert", "params": {"name": "test_b", "value": "value_b"}}')
echo "Response: $RESP"
if echo "$RESP" | grep -q '"status"'; then
    echo "[PASS] Insert succeeded"
else
    echo "[FAIL] Insert failed"; exit 1
fi

# Test 2: Update on Backend B (should succeed)
echo "[Test 2] Tenant B update on Backend B..."
RESP=$(curl -s --cacert "$CA_CERT" -X POST "$PROXY_URL/mcp/b" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"method": "update", "params": {"id": 1, "value": "updated_value_b"}}')
echo "Response: $RESP"
if echo "$RESP" | grep -q '"status"'; then
    echo "[PASS] Update succeeded"
else
    echo "[FAIL] Update failed"; exit 1
fi

# Test 3: Try to access Backend A (should be denied)
echo "[Test 3] Tenant B trying to access Backend A (should be denied)..."
HTTP_CODE=$(curl -s --cacert "$CA_CERT" -o /tmp/resp_b.json -w "%{http_code}" -X POST "$PROXY_URL/mcp/a" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"method": "select", "params": {}}')
echo "Response: $(cat /tmp/resp_b.json) (HTTP $HTTP_CODE)"
if [ "$HTTP_CODE" = "403" ]; then
    echo "[PASS] Access correctly denied by Casbin"
else
    echo "[FAIL] Access should have been denied"; exit 1
fi

# Test 4: Check debug.log
echo "[Test 4] Checking debug.log..."
sleep 1
if [ -f "proxy_server/debug.log" ]; then
    echo "Last 5 log entries:"
    tail -5 proxy_server/debug.log
    if grep -q '"tenant": "tenant_b"' proxy_server/debug.log; then
        echo "[PASS] Debug log contains tenant_b entries"
    fi
fi

echo ""
echo "=== All Tenant B tests passed! ==="
exit 0
