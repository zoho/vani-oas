#!/usr/bin/env python3
"""
Sample API runner for the Vani REST API.

Shows the whole loop end to end: refresh an OAuth access token, call a few
endpoints, and unwrap Vani's response envelope.

This script talks to the API directly with `requests` so it runs against the
spec as published, with no generated SDK required. If you would rather use a
generated client, see "Generate an SDK" in the README — the auth flow below is
identical, you just hand the access token to the generated Configuration.

Setup
-----
1. Register a client at https://api-console.zoho.com (type: Self Client or
   Server-based) and note the Client ID and Client Secret.

2. Generate a refresh token for the scopes you need. Scopes are granular and
   named Vani.<resource>.<ACTION>; each operation in the spec declares its own
   under `security`. For this script:

       Vani.editions.READ,Vani.spaces.READ,Vani.zones.READ

3. Export your credentials, and the data centre your edition lives in:

       export VANI_CLIENT_ID=...
       export VANI_CLIENT_SECRET=...
       export VANI_REFRESH_TOKEN=...
       export VANI_DC=com            # com | eu | in | com.au | ca | sa | ae | com.cn | jp | sg | uk

4. Install the one dependency and run:

       pip install requests
       python sample_api_runner.py
"""

import os
import sys

import requests

# The accounts host is per-DC too, and uses the same TLD as the API host.
DC = os.getenv("VANI_DC", "com")
ACCOUNTS_HOST = f"https://accounts.zoho.{DC}"
API_HOST = f"https://api.app.vanihq.{DC}"
BASE = f"{API_HOST}/vani/api/v1"

TIMEOUT = 30


class VaniError(RuntimeError):
    """An error reported by the API, or a transport failure."""


def get_access_token():
    """Exchange the long-lived refresh token for a short-lived access token."""
    missing = [k for k in ("VANI_CLIENT_ID", "VANI_CLIENT_SECRET", "VANI_REFRESH_TOKEN")
               if not os.getenv(k)]
    if missing:
        sys.exit(f"Set these environment variables first: {', '.join(missing)}")

    response = requests.post(
        f"{ACCOUNTS_HOST}/oauth/v2/token",
        data={
            "refresh_token": os.environ["VANI_REFRESH_TOKEN"],
            "client_id": os.environ["VANI_CLIENT_ID"],
            "client_secret": os.environ["VANI_CLIENT_SECRET"],
            "grant_type": "refresh_token",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()

    # Zoho Accounts reports failures with HTTP 200 and an `error` key.
    if "access_token" not in payload:
        raise VaniError(f"token refresh failed: {payload.get('error', payload)}")
    return payload["access_token"]


def call(token, method, path, **kwargs):
    """Call an endpoint and unwrap the {status, data, message} envelope.

    Vani wraps almost every response in that envelope. `GET /openapi` is the
    documented exception — it returns the OpenAPI document itself.
    """
    response = requests.request(
        method,
        f"{BASE}{path}",
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
        timeout=TIMEOUT,
        **kwargs,
    )

    try:
        body = response.json()
    except ValueError:
        raise VaniError(f"{method} {path} -> HTTP {response.status_code}, non-JSON body")

    if response.status_code >= 400:
        raise VaniError(f"{method} {path} -> HTTP {response.status_code}: "
                        f"{body.get('message', body)}")

    # Unwrap when enveloped; hand back the raw body when it is not.
    return body.get("data", body) if isinstance(body, dict) else body


def main():
    token = get_access_token()
    print(f"Authenticated against {API_HOST}\n")

    # --- Editions -----------------------------------------------------------
    # Every other resource hangs off an edition, so start here.
    editions = call(token, "GET", "/editions")
    if not editions:
        sys.exit("No editions found for this user.")

    edition_id = editions[0]["id"] if isinstance(editions, list) else editions["id"]
    print(f"Edition {edition_id}")

    # --- Spaces -------------------------------------------------------------
    spaces = call(token, "GET", f"/editions/{edition_id}/spaces")
    spaces = spaces if isinstance(spaces, list) else spaces.get("spaces", [])
    print(f"  {len(spaces)} space(s)")

    if not spaces:
        print("\n  No spaces yet — create one in the Vani app, then rerun.")
        return

    space_id = spaces[0]["id"]
    print(f"  Space {space_id}: {spaces[0].get('name', '(unnamed)')}")

    # --- Zones --------------------------------------------------------------
    # `zones/meta` lists every zone in the space without loading its contents.
    zones = call(token, "GET", f"/editions/{edition_id}/spaces/{space_id}/zones/meta")
    zones = zones if isinstance(zones, list) else zones.get("zones", [])
    print(f"  {len(zones)} zone(s)")

    if not zones:
        print("\n  No zones yet — create one in the Vani app, then rerun.")
        return

    zone_id = zones[0]["id"]
    print(f"  Zone {zone_id}: {zones[0].get('name', '(unnamed)')}")

    # --- Canvas -------------------------------------------------------------
    # Read the shapes on that zone. To create one instead, POST the same path
    # with an `elements` array — see elements.json for the full request shape.
    shapes = call(token, "GET",
                  f"/editions/{edition_id}/spaces/{space_id}/zones/{zone_id}/shapes")
    shapes = shapes if isinstance(shapes, list) else shapes.get("elements", [])
    print(f"  {len(shapes)} shape(s) on the zone")


if __name__ == "__main__":
    try:
        main()
    except (VaniError, requests.RequestException) as exc:
        sys.exit(f"error: {exc}")
