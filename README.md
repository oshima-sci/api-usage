# Oshima API - Upload & Read Papers

Simple Python scripts for uploading papers to Oshima and retrieving their extracted content (claims and evidence).

## What is Oshima?

Oshima is a research paper processing system that:
- Extracts **claims** (main findings/assertions) from papers
- Extracts **evidence** (supporting data/experiments) for those claims
- Links evidence to the claims they support
- Provides bounding boxes for highlighting text in PDFs

## What These Scripts Do

### 1. Upload Papers (`upload_paper.py` & `upload_directory.py`)
- Upload single PDFs or entire directories
- Papers are automatically processed through extraction pipeline
- Get paper IDs for later retrieval

### 2. Get Extracts (`get_paper_extracts.py`)
- Retrieve extracted claims and evidence for papers
- Get bounding boxes for PDF highlighting
- See relationships between evidence and claims

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Authentication

Copy and configure the environment file:

```bash
cp .env.example .env
```

Edit `.env`:
```env
OSHIMA_API_URL=https://api.oshimascience.com/api/v1
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
OSHIMA_EMAIL=your@email.com
OSHIMA_PASSWORD=your-password
```

**Where to find these:**
- **SUPABASE_URL & SUPABASE_ANON_KEY**:
  - See your inivite email
- **OSHIMA_EMAIL & OSHIMA_PASSWORD**:
  - Your Oshima user account credentials
  - If you don't have an account, create one on [Oshima](https://oshimascience.com)

### 3. Usage Examples

**Upload a single paper:**
```bash
python upload_paper.py paper.pdf \
  --title "Deep Learning for Science" \
  --field "Computer Science" \
  --topic "Machine Learning"
```

**Upload entire directory:**
```bash
python upload_directory.py ./papers/ \
  --field "Computer Science" \
  --topic "AI Research" \
  --delay 2.0
```

**Get extracts for papers:**
```bash
python get_paper_extracts.py \
  16a9a57a-33f0-446d-a09d-93e84d994692 \
  59900367-fe96-4bef-9034-4075af91e436
```

---

## Understanding Authentication

### How It Works

Oshima uses **JWT (JSON Web Token) authentication**, the same as the Oshima web app:

1. **Sign in** - Scripts authenticate with your Oshima email/password
2. **Get JWT token** - API returns a temporary token (valid ~1 hour)
3. **Use token** - Token is sent with each API request in the `Authorization` header
4. **Papers linked to you** - All uploaded papers are associated with your account

### What You Need

✅ **Oshima user account** - Regular user credentials (email/password)
✅ **Supabase project credentials** - Public URL and anon key

### Security Notes

- Your password is **only used to get a JWT token** (never sent to Oshima)
- JWT tokens **expire after ~1 hour** (scripts handle re-authentication)

---

## Detailed Usage

### Upload Single Paper

```bash
python upload_paper.py <path-to-pdf> [options]
```

**Options:**
- `--title "Paper Title"` - Paper title (optional)
- `--field "Field Name"` - Research field (optional)
- `--topic "Topic"` - Research topic (optional)
- `--doi "10.1234/example"` - DOI identifier (optional)

**Example:**
```bash
python upload_paper.py attention.pdf \
  --title "Attention Is All You Need" \
  --field "Machine Learning" \
  --topic "Transformers"
```

**Output:**
```
✅ Upload successful!
   Paper ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
   Status: created
   Extraction Run ID: x9y8z7w6-v5u4-3210-dcba-9876543210fe
   Processing Status: queued
```

Save the **Paper ID** - you'll need it to retrieve extracts later!

---

### Upload Directory of Papers

```bash
python upload_directory.py <directory-path> [options]
```

**Options:**
- `--field "Field"` - Default field for all papers
- `--topic "Topic"` - Default topic for all papers
- `--delay <seconds>` - Delay between uploads (default: 1.0)
- `--pattern "*.pdf"` - File pattern to match (default: *.pdf)

**Example:**
```bash
python upload_directory.py ./arxiv_papers/ \
  --field "Physics" \
  --topic "Astrophysics" \
  --delay 2.0
```

**Output:**
```
📁 Found 3 PDF file(s) in ./arxiv_papers/

[1/3] 📤 Uploading: paper1.pdf
   ✅ Success! Paper ID: ...

[2/3] 📤 Uploading: paper2.pdf
   ✅ Success! Paper ID: ...

================================================================================
📊 UPLOAD SUMMARY
================================================================================
Total files: 3
Successful: 3 ✅
Failed: 0 ❌
```

**Features:**
- Automatically uses filename as title (without extension)
- Applies field/topic to all papers if provided
- Configurable delay prevents rate limiting
- Detects duplicates (won't re-upload same file)

---

### Get Paper Extracts

```bash
python get_paper_extracts.py <paper-id-1> [paper-id-2] [...]
```

**Example:**
```bash
python get_paper_extracts.py \
  16a9a57a-33f0-446d-a09d-93e84d994692 \
  59900367-fe96-4bef-9034-4075af91e436
```

**Output:**
```
📄 Paper: Effectiveness of High-Dimensional Distance Metrics
   ID: 16a9a57a-33f0-446d-a09d-93e84d994692
   Filename: 2511.01873v1.pdf
   Claims: 5
   Evidence: 12
   Bounding Boxes: 17

   📝 Sample Claims:
      - Our method achieves 95% accuracy on the benchmark dataset...
      - The proposed algorithm outperforms state-of-the-art approaches...

   🔍 Sample Evidence:
      - Figure 3 shows the comparison with baseline methods...
        → Points to 2 claim(s)
      - Table 2 presents the quantitative results...
        → Points to 1 claim(s)

💾 Full response saved to: paper_extracts.json
```

**What you get:**
- **Claims**: Main findings and assertions from the paper
- **Evidence**: Supporting data, experiments, results
- **Relationships**: Which evidence supports which claims
- **Bounding boxes**: Coordinates for highlighting text in PDF
- **JSON export**: Full response saved for further processing

**Note:** Papers take 2-10 minutes to process after upload. If you see "No claims/evidence found", check back later.

---

## Response Format

### Upload Response
```json
{
  "status": "success",
  "data": {
    "paper_id": "uuid",
    "status": "created",
    "extraction_run_id": "uuid",
    "processing_status": "queued"
  }
}
```

### Extracts Response
```json
{
  "status": "success",
  "data": {
    "papers": [
      {
        "id": "paper-uuid",
        "metadata": {
          "title": "Paper Title",
          "original_filename": "paper.pdf",
          "sha256": "hash..."
        },
        "elements": [
          {
            "id": "claim-uuid",
            "type": "claim",
            "text": "Our method achieves...",
            "bbox_id": "paper-uuid:p1:bbox_abc123"
          },
          {
            "id": "evidence-uuid",
            "type": "evidence",
            "text": "Figure 1 shows...",
            "evidence_data": {
              "points_to": ["claim-uuid"],
              "direction": "supports"
            }
          }
        ],
        "bboxes": [
          {
            "id": "paper-uuid:p1:bbox_abc123",
            "page": 1,
            "x": 0.5,
            "y": 2.0,
            "w": 3.5,
            "h": 1.0
          }
        ]
      }
    ]
  }
}
```

---

## Troubleshooting

### Authentication Errors

**Error: "Invalid login credentials"**
- Check your email/password in `.env`
- Ensure you have an Oshima user account

**Error: "Invalid or expired token"**
- Token expired (happens after ~1 hour)
- Script will automatically re-authenticate

### Upload Errors

**Error: "Only PDF files are allowed"**
- File must be a valid PDF
- Check file extension is `.pdf`

**Error: "File too large"**
- Maximum file size is usually 40MB
- Try compressing the PDF

**Error: "Connection refused"**
- Oshima API is not running
- Check `OSHIMA_API_URL` in `.env`
- For production: `https://api.oshimascience.com/api/v1`

### Extracts Errors

**Warning: "No claims/evidence found"**
- Paper is still processing (takes 2-10 minutes)
- Wait a few minutes and try again

---

## API Endpoints Used

See API Documentation [here](https://api.oshimascience.com/docs)

### Upload Paper
- **Endpoint:** `POST /api/v1/papers/`
- **Auth:** Required (User JWT)
- **Purpose:** Upload PDF and queue for processing

### Get Extracts
- **Endpoint:** `POST /api/v1/papers/extracts`
- **Auth:** Required (User JWT)
- **Purpose:** Retrieve claims, evidence, and bounding boxes

---

## Files in This Repository

- `upload_paper.py` - Upload a single PDF with metadata
- `upload_directory.py` - Batch upload PDFs from a directory
- `get_paper_extracts.py` - Retrieve extracts for papers
- `requirements.txt` - Python dependencies (httpx, python-dotenv)
- `.env.example` - Example configuration file

---

## Next Steps

After uploading papers and retrieving extracts, you can:

1. **Use the Oshima web app** to visualize claims/evidence
2. **Process the JSON** programmatically for your own applications
3. **Highlight PDFs** using the bounding box coordinates
4. **Build custom tools** on top of the extracted data

For more advanced usage (creating libraries, managing collections, etc.), see the [Oshima API documentation](https://docs.oshimascience.com).

---

## Support

- **API Documentation:** Check the [Oshima API docs](https://api.oshimascience.com/docs)
- **Questions:** Contact the Oshima team or check documentation
