#!/usr/bin/env python3
"""
Fetch extracts for papers using POST /papers/extracts endpoint

This uses JWT authentication to retrieve claims and evidence for given paper IDs.
Based on: api/docs/temporary/extract_fetching_analysis.md

Requirements:
    pip install httpx python-dotenv
"""

import httpx
import sys
import os
import json
from dotenv import load_dotenv


def get_jwt_token(supabase_url: str, supabase_anon_key: str, email: str, password: str) -> str:
    """
    Sign in to Supabase and get a JWT token.

    Args:
        supabase_url: Supabase project URL
        supabase_anon_key: Supabase anon/public key
        email: User email
        password: User password

    Returns:
        JWT access token
    """
    url = f"{supabase_url}/auth/v1/token?grant_type=password"

    headers = {
        "apikey": supabase_anon_key,
        "Content-Type": "application/json"
    }

    data = {
        "email": email,
        "password": password
    }

    print(f"🔑 Authenticating as {email}...")

    response = httpx.post(url, json=data, headers=headers, timeout=30.0)

    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        response.raise_for_status()

    result = response.json()
    access_token = result.get("access_token")

    if not access_token:
        raise ValueError("No access token in response")

    print(f"✅ Authenticated successfully\n")
    return access_token


def get_paper_extracts(api_url: str, jwt_token: str, paper_ids: list) -> dict:
    """
    Fetch extracts for given paper IDs.

    Args:
        api_url: Oshima API URL
        jwt_token: JWT access token
        paper_ids: List of paper UUIDs

    Returns:
        Response dict with papers and their extracts
    """
    url = f"{api_url}/api/v1/papers/extracts"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    data = {
        "paper_ids": paper_ids
    }

    print(f"📥 Fetching extracts for {len(paper_ids)} paper(s)...")
    print(f"   API: {url}")
    for i, paper_id in enumerate(paper_ids, 1):
        print(f"   {i}. {paper_id}")

    response = httpx.post(
        url,
        json=data,
        headers=headers,
        timeout=60.0
    )

    if response.status_code != 200:
        print(f"\n❌ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
        response.raise_for_status()

    result = response.json()
    return result


def print_paper_summary(paper_data: dict, elements_for_paper: list):
    """Print a summary of paper extracts."""
    metadata = paper_data.get('metadata', {})
    title = metadata.get('title', 'Untitled')

    print(f"\n📄 Paper: {title}")
    print(f"   ID: {paper_data['id']}")
    print(f"   Filename: {metadata.get('original_filename', 'N/A')}")

    # Count elements
    claims = [e for e in elements_for_paper if e['type'] == 'claim']
    evidence = [e for e in elements_for_paper if e['type'] == 'evidence']

    bboxes = paper_data.get('bboxes', [])

    print(f"   Claims: {len(claims)}")
    print(f"   Evidence: {len(evidence)}")
    print(f"   Bounding Boxes: {len(bboxes)}")

    # Show sample claims
    if claims:
        print(f"\n   📝 Sample Claims:")
        for claim in claims[:3]:
            text = claim.get('text_rephrased', claim.get('text_verbatim', ''))
            text = text[:100] + "..." if len(text) > 100 else text
            print(f"      - {text}")
    else:
        print(f"\n   ⚠️  No claims found - paper may still be processing")

    # Show sample evidence
    if evidence:
        print(f"\n   🔍 Sample Evidence:")
        for ev in evidence[:3]:
            text = ev.get('text_rephrased', ev.get('text_verbatim', ''))
            text = text[:100] + "..." if len(text) > 100 else text
            points_to = ev.get('evidence_data', {}).get('points_to', [])
            print(f"      - {text}")
            if points_to:
                print(f"        → Points to {len(points_to)} claim(s)")
    else:
        print(f"\n   ⚠️  No evidence found - paper may still be processing")


def main():
    """Main entry point"""

    # Load environment variables
    load_dotenv()

    # Get configuration
    api_url = os.getenv("OSHIMA_API_URL", "http://127.0.0.1:8000")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    email = os.getenv("OSHIMA_EMAIL")
    password = os.getenv("OSHIMA_PASSWORD")

    # Validate required config
    missing = []
    if not supabase_url:
        missing.append("SUPABASE_URL")
    if not supabase_anon_key:
        missing.append("SUPABASE_ANON_KEY")
    if not email:
        missing.append("OSHIMA_EMAIL")
    if not password:
        missing.append("OSHIMA_PASSWORD")

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nSet these in your .env file")
        sys.exit(1)

    # Get paper IDs from command line
    if len(sys.argv) < 2:
        print("Usage: python get_paper_extracts.py <paper-id-1> [paper-id-2] ...")
        print("\nExample:")
        print("  python get_paper_extracts.py \\")
        print("    16a9a57a-33f0-446d-a09d-93e84d994692 \\")
        print("    59900367-fe96-4bef-9034-4075af91e436")
        print("\nThis will fetch all claims and evidence for the specified papers.")
        sys.exit(1)

    paper_ids = sys.argv[1:]

    print("=" * 80)
    print("📚 OSHIMA PAPER EXTRACTS FETCHER")
    print("=" * 80)

    try:
        # Step 1: Authenticate and get JWT
        jwt_token = get_jwt_token(supabase_url, supabase_anon_key, email, password)

        # Step 2: Fetch extracts
        result = get_paper_extracts(api_url, jwt_token, paper_ids)

        # Save full response to file first (for debugging)
        output_file = "paper_extracts.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full response saved to: {output_file}")

        # Step 3: Display results
        print("\n" + "=" * 80)
        print("📊 RESULTS")
        print("=" * 80)

        data = result.get('data', {})
        papers = data.get('papers', [])
        all_elements = data.get('elements', [])
        stats = data.get('stats', {})

        if not papers:
            print("⚠️  No papers found or no extracts available yet")
            print("   Papers might still be processing. Check back later.")
        else:
            # Show overall stats
            print(f"\n✅ Retrieved {len(papers)} paper(s) with extracts")
            print(f"   Total Claims: {stats.get('total_claims', 0)}")
            print(f"   Total Evidence: {stats.get('total_evidence', 0)}\n")

            # Group elements by paper_id
            elements_by_paper = {}
            for element in all_elements:
                paper_id = element.get('paper_id')
                if paper_id not in elements_by_paper:
                    elements_by_paper[paper_id] = []
                elements_by_paper[paper_id].append(element)

            # Print summary for each paper
            for paper in papers:
                paper_id = paper['id']
                paper_elements = elements_by_paper.get(paper_id, [])
                print_paper_summary(paper, paper_elements)

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e}")
        print(f"   Status: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
