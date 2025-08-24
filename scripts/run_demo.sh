#!/usr/bin/env bash
set -euo pipefail

# Helpers: parse JSON with python
parse_json() { python -c "import sys,json; print(json.load(sys.stdin)['$1'])"; }

echo "--- Admin: register + login ---"
curl -s http://localhost/auth/register -H "Content-Type: application/json" \  -d '{"email":"admin@example.com","password":"P@ssw0rd!","role":"admin"}' >/dev/null || true
ATOKENS=$(curl -s http://localhost/auth/login -H "Content-Type: application/json" \  -d '{"email":"admin@example.com","password":"P@ssw0rd!"}')
AACCESS=$(echo "$ATOKENS" | parse_json access_token)

echo "--- Admin: create category + product ---"
curl -s http://localhost/catalog/v1/categories \  -H "Authorization: Bearer $AACCESS" -H "Content-Type: application/json" \  -d '{"name":"Shoes"}' || true
curl -s http://localhost/catalog/v1/products \  -H "Authorization: Bearer $AACCESS" -H "Content-Type: application/json" \  -d '{"title":"Air Zoom","description":"Runner","price_cents":12999,"currency":"USD","sku":"SKU-001","category_id":1,"active":true}' || true

echo "--- Admin: restock inventory ---"
curl -s http://localhost/catalog/v1/inventory/restock \  -H "Authorization: Bearer $AACCESS" -H "Content-Type: application/json" \  -d '{"items":[{"product_id":1,"qty":50}]}'

echo "--- Customer: register + login ---"
curl -s http://localhost/auth/register -H "Content-Type: application/json" \  -d '{"email":"cust@example.com","password":"P@ssw0rd!"}' >/dev/null || true
CTOKENS=$(curl -s http://localhost/auth/login -H "Content-Type: application/json" \  -d '{"email":"cust@example.com","password":"P@ssw0rd!"}')
CACCESS=$(echo "$CTOKENS" | parse_json access_token)

echo "--- Customer: add to cart ---"
curl -s http://localhost/cart/v1/cart/items -H "Authorization: Bearer $CACCESS" \  -H "Content-Type: application/json" -d '{"product_id":1,"qty":2}'

echo "--- Customer: checkout ---"
ORDER=$(curl -s http://localhost/order/v1/orders/checkout -H "Authorization: Bearer $CACCESS")
echo "$ORDER"
ORDER_ID=$(echo "$ORDER" | parse_json order_id)
AMOUNT=$(echo "$ORDER" | parse_json total_cents)

echo "--- Payment: mock succeed ---"
curl -s http://localhost/payment/v1/payments/mock-succeed \  -H "Content-Type: application/json" \  -d "{\"order_id\": $ORDER_ID, \"amount_cents\": $AMOUNT, \"currency\": \"USD\"}"

echo "--- Wait and check order status ---"
sleep 2
curl -s http://localhost/order/v1/orders/$ORDER_ID | jq .
