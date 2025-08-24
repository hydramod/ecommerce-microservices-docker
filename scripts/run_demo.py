#!/usr/bin/env python3
"""
run_demo.py - Python version of the e-commerce microservices demo runner
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional, List

class DemoRunner:
    def __init__(self):
        self.base_url = "http://localhost"
        self.auth_url = f"{self.base_url}/auth"
        self.catalog_url = f"{self.base_url}/catalog"
        self.cart_url = f"{self.base_url}/cart"
        self.order_url = f"{self.base_url}/order"
        self.payment_url = f"{self.base_url}/payment"
        
        # Health check endpoints
        self.health_endpoints = {
            "auth": f"{self.base_url}/auth/health",
            "catalog": f"{self.base_url}/catalog/health",
            "cart": f"{self.base_url}/cart/health",
            "order": f"{self.base_url}/order/health",
            "payment": f"{self.base_url}/payment/health"
        }
        
        self.admin_email = "admin@example.com"
        self.admin_pass = "P@ssw0rd!"
        self.cust_email = "cust@example.com"
        self.cust_pass = "P@ssw0rd!"
        
        # Get internal key from environment or use default
        self.internal_key = os.getenv("SVC_INTERNAL_KEY", "devkey")
        
        # Token storage
        self.admin_access_token = None
        self.cust_access_token = None

    def show_step(self, title: str):
        """Print a step header"""
        print(f"\n=== {title} ===")

    def mask_token(self, token: str) -> str:
        """Mask a token for display"""
        if not token:
            return "<none>"
        if len(token) <= 12:
            return token
        return f"{token[:8]}...{token[-6:]}"

    def call_api(self, method: str, url: str, headers: Optional[Dict] = None, 
                 data: Optional[Any] = None, expected_status: List[int] = [200, 201, 202, 204]):
        """Make an API call with detailed logging"""
        print(f"\n-> {method} {url}")
        
        if headers:
            print_headers = headers.copy()
            if 'Authorization' in print_headers:
                token = print_headers['Authorization'].replace('Bearer ', '')
                print_headers['Authorization'] = f"Bearer {self.mask_token(token)}"
            print(f"   Headers: {json.dumps(print_headers, indent=2)}")
        else:
            print("   Headers: <none>")
            
        if data:
            print(f"   Body: {json.dumps(data, indent=2)}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                timeout=30
            )
            
            status_color = '\033[92m' if response.status_code in expected_status else '\033[93m'
            print(f"   Status: {status_color}{response.status_code}\033[0m")
            
            try:
                json_response = response.json()
                print("   JSON:")
                print(json.dumps(json_response, indent=2))
                return {
                    "status": response.status_code,
                    "data": json_response,
                    "raw": response.text
                }
            except json.JSONDecodeError:
                if response.text:
                    print("   Content:")
                    print(response.text)
                else:
                    print("   Content: <empty>")
                return {
                    "status": response.status_code,
                    "data": None,
                    "raw": response.text
                }
                
        except requests.exceptions.RequestException as e:
            print(f"   Error: \033[91m{e}\033[0m")
            return {
                "status": None,
                "data": None,
                "raw": None,
                "error": str(e)
            }

    def preflight_health_checks(self):
        """Check health of all services"""
        self.show_step("Preflight: service health")
        
        for service, url in self.health_endpoints.items():
            result = self.call_api("GET", url, expected_status=[200], quiet=True)
            status = "OK" if result.get("status") == 200 else f"FAIL ({result.get('status')})"
            color = '\033[92m' if status == "OK" else '\033[91m'
            print(f"  - {service.ljust(8)} -> {color}{status}\033[0m")

    def run_demo(self):
        """Run the complete demo workflow"""
        print("Starting E-commerce Microservices Demo")
        print("=" * 50)
        
        # Preflight checks
        self.preflight_health_checks()
        
        # 1) Admin register + login
        self.show_step("Admin: register")
        self.call_api("POST", f"{self.auth_url}/register", data={
            "email": self.admin_email,
            "password": self.admin_pass,
            "role": "admin"
        }, expected_status=[201, 409])
        
        self.show_step("Admin: login")
        login_result = self.call_api("POST", f"{self.auth_url}/login", data={
            "email": self.admin_email,
            "password": self.admin_pass
        }, expected_status=[200])
        
        if login_result.get("data"):
            self.admin_access_token = login_result["data"].get("access_token")
            print(f"Admin access token: {self.mask_token(self.admin_access_token)}")
        
        # 2) Admin create category + product
        auth_headers = {"Authorization": f"Bearer {self.admin_access_token}"} if self.admin_access_token else {}
        
        self.show_step("Admin: create category")
        self.call_api("POST", f"{self.catalog_url}/v1/categories/", 
                     headers=auth_headers, data={"name": "Shoes"}, expected_status=[201, 409])
        
        self.show_step("Admin: create product")
        self.call_api("POST", f"{self.catalog_url}/v1/products/", headers=auth_headers, data={
            "title": "Air Zoom",
            "description": "Runner",
            "price_cents": 12999,
            "currency": "USD",
            "sku": "SKU-001",
            "category_id": 1,
            "active": True
        }, expected_status=[201, 409])
        
        # Quick sanity check
        self.show_step("Sanity: fetch product #1 (gateway)")
        self.call_api("GET", f"{self.catalog_url}/v1/products/1", expected_status=[200, 404])
        
        # 3) Admin restock inventory
        self.show_step("Admin: restock inventory (X-Internal-Key + Authorization)")
        internal_headers = auth_headers.copy()
        internal_headers["X-Internal-Key"] = self.internal_key
        
        self.call_api("POST", f"{self.catalog_url}/v1/inventory/restock", 
                     headers=internal_headers, data={
                         "items": [{"product_id": 1, "qty": 50}]
                     }, expected_status=[200])
        
        # 4) Customer register + login
        self.show_step("Customer: register")
        self.call_api("POST", f"{self.auth_url}/register", data={
            "email": self.cust_email,
            "password": self.cust_pass
        }, expected_status=[201, 409])
        
        self.show_step("Customer: login")
        cust_login = self.call_api("POST", f"{self.auth_url}/login", data={
            "email": self.cust_email,
            "password": self.cust_pass
        }, expected_status=[200])
        
        if cust_login.get("data"):
            self.cust_access_token = cust_login["data"].get("access_token")
            print(f"Customer access token: {self.mask_token(self.cust_access_token)}")
        
        # 5) Customer add to cart
        cust_headers = {"Authorization": f"Bearer {self.cust_access_token}"} if self.cust_access_token else {}
        
        self.show_step("Customer: add to cart")
        cart_result = self.call_api("POST", f"{self.cart_url}/v1/cart/items", 
                                   headers=cust_headers, data={
                                       "product_id": 1,
                                       "qty": 2
                                   }, expected_status=[200, 201, 404])
        
        if cart_result.get("status") == 404:
            print("\n\033[93mHint: Cart returned 404. This often means the cart service can't reach catalog.")
            print("      Ensure the cart container has CATALOG_BASE set correctly.\033[0m")
        
        # 6) Checkout
        self.show_step("Customer: checkout")
        checkout_result = self.call_api("POST", f"{self.order_url}/v1/orders/checkout", 
                                       headers=cust_headers, expected_status=[200, 401])
        
        order_id = None
        amount = None
        if checkout_result.get("data"):
            order_id = checkout_result["data"].get("order_id")
            amount = checkout_result["data"].get("total_cents")
        print(f"Order ID: {order_id}; Amount: {amount}")
        
        # 7) Payment: mock succeed
        self.show_step("Payment: mock succeed")
        if order_id and amount:
            self.call_api("POST", f"{self.payment_url}/payments/mock-succeed", data={
                "order_id": order_id,
                "amount_cents": amount,
                "currency": "USD"
            }, expected_status=[200])
        else:
            print("Skipping payment - no order ID or amount available")
        
        # Wait for processing
        time.sleep(2)
        
        # 8) Check order status
        self.show_step("Order: check status")
        if order_id:
            self.call_api("GET", f"{self.order_url}/orders/{order_id}", expected_status=[200, 404])
        else:
            print("Skipping order status check - no order ID available")
        
        print("\n\033[92m=== DEMO COMPLETE ===\033[0m")

    def call_api(self, method: str, url: str, headers: Optional[Dict] = None, 
                 data: Optional[Any] = None, expected_status: List[int] = [200, 201, 202, 204], quiet: bool = False):
        """Make an API call with detailed logging (quiet mode for health checks)"""
        if not quiet:
            print(f"\n-> {method} {url}")
            
            if headers:
                print_headers = headers.copy()
                if 'Authorization' in print_headers:
                    token = print_headers['Authorization'].replace('Bearer ', '')
                    print_headers['Authorization'] = f"Bearer {self.mask_token(token)}"
                print(f"   Headers: {json.dumps(print_headers, indent=2)}")
            else:
                print("   Headers: <none>")
                
            if data:
                print(f"   Body: {json.dumps(data, indent=2)}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                timeout=30
            )
            
            if not quiet:
                status_color = '\033[92m' if response.status_code in expected_status else '\033[93m'
                print(f"   Status: {status_color}{response.status_code}\033[0m")
            
            try:
                json_response = response.json()
                if not quiet:
                    print("   JSON:")
                    print(json.dumps(json_response, indent=2))
                return {
                    "status": response.status_code,
                    "data": json_response,
                    "raw": response.text
                }
            except json.JSONDecodeError:
                if response.text and not quiet:
                    print("   Content:")
                    print(response.text)
                return {
                    "status": response.status_code,
                    "data": None,
                    "raw": response.text
                }
                
        except requests.exceptions.RequestException as e:
            if not quiet:
                print(f"   Error: \033[91m{e}\033[0m")
            return {
                "status": None,
                "data": None,
                "raw": None,
                "error": str(e)
            }

if __name__ == "__main__":
    demo = DemoRunner()
    demo.run_demo()
