#!/usr/bin/env python3
"""
Upload all PDFs from a directory to Oshima API using POST /papers/ endpoint

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
import time


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
        Response dict with paper_id and status, or None if failed
    """
    # Check PDF exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"   ⚠️  File not found: {pdf_path}")
        return None

    # Build request
    url = f"{api_url}/api/v1/papers/"

    try:
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

            response = httpx.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=120.0  # 2 min timeout for large files
            )

            # Check for errors
            if response.status_code not in [200, 201]:
                print(f"   ❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        result = response.json()
        return result

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def upload_directory(
    directory: str,
    api_url: str,
    jwt_token: str,
    field: str = None,
    topic: str = None,
    delay: float = 1.0,
    pattern: str = "*.pdf"
):
    """
    Upload all PDFs from a directory.

    Args:
        directory: Path to directory containing PDFs
        api_url: Oshima API URL
        jwt_token: JWT access token
        field: Default research field for all papers
        topic: Default research topic for all papers
        delay: Delay in seconds between uploads (to avoid rate limiting)
        pattern: File pattern to match (default: *.pdf)

    Returns:
        Dictionary with upload statistics
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise ValueError(f"Directory not found: {directory}")

    if not dir_path.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    # Find all PDFs
    pdf_files = sorted(dir_path.glob(pattern))

    if not pdf_files:
        print(f"⚠️  No PDF files found in {directory}")
        return {"total": 0, "success": 0, "failed": 0}

    print(f"\n📁 Found {len(pdf_files)} PDF file(s) in {directory}")
    print("=" * 80)

    results = {
        "total": len(pdf_files),
        "success": 0,
        "failed": 0,
        "uploads": []
    }

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] 📤 Uploading: {pdf_path.name}")

        # Use filename (without extension) as title if available
        title = pdf_path.stem

        result = upload_paper_with_jwt(
            api_url=api_url,
            jwt_token=jwt_token,
            pdf_path=str(pdf_path),
            title=title,
            field=field,
            topic=topic
        )

        if result:
            print(f"   ✅ Success!")
            print(f"      Paper ID: {result['data']['paper_id']}")
            print(f"      Status: {result['data']['status']}")
            results["success"] += 1
            results["uploads"].append({
                "filename": pdf_path.name,
                "paper_id": result['data']['paper_id'],
                "status": "success"
            })
        else:
            print(f"   ❌ Failed")
            results["failed"] += 1
            results["uploads"].append({
                "filename": pdf_path.name,
                "status": "failed"
            })

        # Delay between uploads to avoid rate limiting
        if i < len(pdf_files):
            print(f"   ⏳ Waiting {delay}s before next upload...")
            time.sleep(delay)

    return results


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

    # Get directory path from command line
    if len(sys.argv) < 2:
        print("Usage: python upload_directory.py <directory-path> [options]")
        print("\nRequired:")
        print("  <directory-path>    Path to directory containing PDFs")
        print("\nOptional:")
        print("  --field 'Research Field'")
        print("  --topic 'Topic'")
        print("  --delay <seconds>      Delay between uploads (default: 1.0)")
        print("  --pattern '*.pdf'      File pattern (default: *.pdf)")
        print("\nExample:")
        print("  python upload_directory.py ./papers --field 'Computer Science' --topic 'AI'")
        sys.exit(1)

    directory = sys.argv[1]

    # Parse optional arguments
    field = None
    topic = None
    delay = 1.0
    pattern = "*.pdf"

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--field' and i + 1 < len(sys.argv):
            field = sys.argv[i + 1]
            i += 2
        elif arg == '--topic' and i + 1 < len(sys.argv):
            topic = sys.argv[i + 1]
            i += 2
        elif arg == '--delay' and i + 1 < len(sys.argv):
            delay = float(sys.argv[i + 1])
            i += 2
        elif arg == '--pattern' and i + 1 < len(sys.argv):
            pattern = sys.argv[i + 1]
            i += 2
        else:
            print(f"⚠️  Unknown argument: {arg}")
            i += 1

    try:
        # Step 1: Authenticate and get JWT
        jwt_token = get_jwt_token(supabase_url, supabase_anon_key, email, password)

        # Step 2: Upload all PDFs from directory
        results = upload_directory(
            directory=directory,
            api_url=api_url,
            jwt_token=jwt_token,
            field=field,
            topic=topic,
            delay=delay,
            pattern=pattern
        )

        # Step 3: Print summary
        print("\n" + "=" * 80)
        print("📊 UPLOAD SUMMARY")
        print("=" * 80)
        print(f"Total files: {results['total']}")
        print(f"Successful: {results['success']} ✅")
        print(f"Failed: {results['failed']} ❌")
        print("=" * 80)

        if results['failed'] > 0:
            print("\n⚠️  Some uploads failed. Check the output above for details.")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ {e}")
    except ValueError as e:
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
