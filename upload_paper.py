#!/usr/bin/env python3
"""
Upload paper to Oshima API using POST /papers/ endpoint

This uses JWT authentication (no service role key needed).
Based on: api/docs/temporary/frontend_endpoints_authentication_overview.md

Requirements:
    pip install httpx python-dotenv
"""

import httpx
import sys
import os
from pathlib import Path
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

    print(f"✅ Authenticated successfully")
    return access_token


def upload_paper_with_jwt(
    api_url: str,
    jwt_token: str,
    pdf_path: str,
    title: str = None,
    doi: str = None,
    field: str = None,
    topic: str = None
):
    """
    Upload a paper PDF using the POST /papers/ endpoint with JWT auth.

    Args:
        api_url: Oshima API URL
        jwt_token: JWT access token from Supabase auth
        pdf_path: Path to PDF file
        title: Paper title (optional)
        doi: Paper DOI (optional)
        field: Research field (optional)
        topic: Research topic (optional)

    Returns:
        Response dict with paper_id and status
    """
    # Check PDF exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Build request
    url = f"{api_url}/api/v1/papers/"

    with open(pdf_file, 'rb') as f:
        # Build multipart form data
        files = {
            'file': (pdf_file.name, f, 'application/pdf')
        }

        data = {}
        if title:
            data['title'] = title
        if doi:
            data['doi'] = doi
        if field:
            data['field'] = field
        if topic:
            data['topic'] = topic

        headers = {
            "Authorization": f"Bearer {jwt_token}"
        }

        print(f"\n📤 Uploading {pdf_file.name}...")
        print(f"   API: {url}")
        if title:
            print(f"   Title: {title}")
        if field:
            print(f"   Field: {field}")
        if topic:
            print(f"   Topic: {topic}")

        response = httpx.post(
            url,
            files=files,
            data=data,
            headers=headers,
            timeout=120.0  # 2 min timeout for large files
        )

        # Check for errors
        if response.status_code not in [200, 201]:
            print(f"\n❌ Upload failed with status {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

    result = response.json()

    print(f"\n✅ Upload successful!")
    print(f"   Paper ID: {result['data']['paper_id']}")
    print(f"   Status: {result['data']['status']}")
    if 'extraction_run_id' in result['data']:
        print(f"   Extraction Run ID: {result['data']['extraction_run_id']}")
    if 'processing_status' in result['data']:
        print(f"   Processing Status: {result['data']['processing_status']}")

    return result


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
        print("\nCreate a .env file with:")
        print("  OSHIMA_API_URL=http://127.0.0.1:8000")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_ANON_KEY=your-anon-key")
        print("  OSHIMA_EMAIL=your@email.com")
        print("  OSHIMA_PASSWORD=your-password")
        sys.exit(1)

    # Get PDF path from command line
    if len(sys.argv) < 2:
        print("Usage: python upload_paper.py <path-to-pdf> [options]")
        print("\nRequired:")
        print("  <path-to-pdf>    Path to PDF file")
        print("\nOptional (via command line or edit script):")
        print("  --title 'Paper Title'")
        print("  --field 'Research Field'")
        print("  --topic 'Topic'")
        print("  --doi '10.1234/example'")
        print("\nConfiguration:")
        print("  Set in .env file:")
        print("    OSHIMA_API_URL")
        print("    SUPABASE_URL")
        print("    SUPABASE_ANON_KEY")
        print("    OSHIMA_EMAIL")
        print("    OSHIMA_PASSWORD")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Parse optional arguments (simple implementation)
    title = None
    field = None
    topic = None
    doi = None

    for i in range(2, len(sys.argv), 2):
        if i + 1 < len(sys.argv):
            arg = sys.argv[i]
            value = sys.argv[i + 1]
            if arg == '--title':
                title = value
            elif arg == '--field':
                field = value
            elif arg == '--topic':
                topic = value
            elif arg == '--doi':
                doi = value

    try:
        # Step 1: Authenticate and get JWT
        jwt_token = get_jwt_token(supabase_url, supabase_anon_key, email, password)

        # Step 2: Upload paper
        result = upload_paper_with_jwt(
            api_url=api_url,
            jwt_token=jwt_token,
            pdf_path=pdf_path,
            title=title,
            doi=doi,
            field=field,
            topic=topic
        )

        print(f"\n📊 Full response:")
        import json
        print(json.dumps(result, indent=2))

    except FileNotFoundError as e:
        print(f"❌ {e}")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Status: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
