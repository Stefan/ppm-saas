#!/usr/bin/env python3
"""
Check API endpoint consistency between backend routers and frontend calls
"""

import re
import os
from pathlib import Path
from collections import defaultdict

# Backend router prefixes
backend_routers = {}
frontend_calls = defaultdict(list)

# Parse backend routers
backend_dir = Path("backend/routers")
for router_file in backend_dir.glob("*.py"):
    content = router_file.read_text()
    
    # Find APIRouter definitions
    matches = re.findall(r'router\s*=\s*APIRouter\(prefix=["\']([^"\']+)["\']', content)
    for prefix in matches:
        backend_routers[router_file.name] = prefix

# Parse frontend API calls
frontend_patterns = [
    "app/**/*.tsx",
    "app/**/*.ts",
    "components/**/*.tsx",
    "components/**/*.ts",
]

for pattern in frontend_patterns:
    for file_path in Path(".").glob(pattern):
        if file_path.is_file():
            try:
                content = file_path.read_text()
                
                # Find getApiUrl calls
                matches = re.findall(r'getApiUrl\(["\']([^"\']+)["\']', content)
                for endpoint in matches:
                    frontend_calls[endpoint].append(str(file_path))
            except:
                pass

# Print results
print("=" * 80)
print("BACKEND ROUTERS")
print("=" * 80)
for router, prefix in sorted(backend_routers.items()):
    print(f"{router:40} -> {prefix}")

print("\n" + "=" * 80)
print("FRONTEND API CALLS")
print("=" * 80)
for endpoint in sorted(frontend_calls.keys()):
    print(f"\n{endpoint}")
    for file in frontend_calls[endpoint][:3]:  # Show first 3 files
        print(f"  - {file}")
    if len(frontend_calls[endpoint]) > 3:
        print(f"  ... and {len(frontend_calls[endpoint]) - 3} more")

# Check consistency
print("\n" + "=" * 80)
print("CONSISTENCY CHECK")
print("=" * 80)

# Group backend prefixes
backend_prefixes = set(backend_routers.values())
frontend_endpoints = set(frontend_calls.keys())

# Check if frontend calls match backend prefixes
issues = []

for endpoint in frontend_endpoints:
    # Check if endpoint starts with any backend prefix
    matched = False
    for prefix in backend_prefixes:
        if endpoint.startswith(prefix):
            matched = True
            break
    
    if not matched:
        # Check if it's a partial match (missing /api or similar)
        potential_matches = []
        for prefix in backend_prefixes:
            # Remove /api from prefix and check
            prefix_without_api = prefix.replace("/api/", "/").replace("/api", "")
            if endpoint.startswith(prefix_without_api):
                potential_matches.append(prefix)
        
        if potential_matches:
            issues.append({
                "endpoint": endpoint,
                "type": "prefix_mismatch",
                "suggestion": potential_matches[0],
                "files": frontend_calls[endpoint]
            })

# Print issues
if issues:
    print("\n⚠️  FOUND ISSUES:\n")
    for issue in issues:
        print(f"❌ {issue['endpoint']}")
        print(f"   Should be: {issue['suggestion']}")
        print(f"   Files: {issue['files'][0]}")
        if len(issue['files']) > 1:
            print(f"   ... and {len(issue['files']) - 1} more")
        print()
else:
    print("\n✅ All endpoints are consistent!")

print("\n" + "=" * 80)
print(f"Summary: {len(backend_routers)} routers, {len(frontend_endpoints)} unique endpoints")
print("=" * 80)
