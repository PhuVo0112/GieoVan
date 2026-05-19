# GieoVan - Bilingual Poetry & Rap Assistant

_[Đọc bản Tiếng Việt bên dưới](#gieovan---hệ-thống-hỗ-trợ-sáng-tác-thơ--rap-vietnamese)_

**GieoVan** is a bilingual (Vietnamese & English) lyric writing assistant. It utilizes phonetic extraction, vector-based rhyme filtering, and contextual language models to suggest matching verses based on syllable count, rhyme scheme, and mood.

---

## Key Features

- **Phonetic Analysis:** Extracts the end-rhyme of the last word using CMU Dict for English and a custom phonetic algorithm for Vietnamese.
- **Language Detection:** Adapts processing logic and prompts based on the user-selected language (VI/EN) from the client interface.
- **Context-Aware RAG with Hard Filtering:** Retrieves contextually and phonetically matching references from ChromaDB using strict vector metadata filtering (end_rhyme, mood, author).
- **Constrained Generation:** Integrates Gemini 2.5 Flash to generate subsequent lines that adhere to the established syllable count, extracted rhyme, and desired mood.

## Tech Stack

- **Backend Framework:** FastAPI, Python
- **Vector Database:** ChromaDB
- **LLM:** Google GenAI SDK (Gemini 2.5 Flash)
- **Linguistics & Phonetics:** `pronouncing` (CMU Dict), `langdetect`
- **Environment & Tooling:** `python-dotenv`, `uvicorn`, `uv` (or `pip`)

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/GieoVan.git
cd GieoVan
```

### 2. Setup Environment Variables

Create a `.env` file in the root directory and add your Google Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install Dependencies

You can use `uv` (recommended for speed) or `pip`:

```bash
# Using uv
uv sync

# OR using pip
pip install -r requirements.txt
```

### 4. Initialize the Vector Database

Before running the backend, you must ingest the raw lyric data into the local ChromaDB.

```bash
python ingest_data.py
```

_(This script will process the raw data, extract phonetics, and store embeddings in the local `neon_van_db` folder.)_

### 5. Run the Backend

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. You can now open `index.html` in your browser to interact with GieoVan!

## 📂 Project Structure

```text
GieoVan/
│
├── main.py               # Main FastAPI backend (RAG & Gemini integration)
├── ingest_data.py        # Data ingestion script for ChromaDB
├── raw_data.json         # Raw lyrical data source (mock/actual)
├── neon_van_db/          # Persistent ChromaDB storage (auto-generated)
├── index.html            # Frontend UI (Vanilla JS, HTML, CSS)
├── .env                  # Environment variables (API Keys)
└── .gitignore            # Git ignore rules
```

---

<br>

# 🎙️ GieoVan - Trợ lý AI viết Thơ & Rap (Vietnamese)

**GieoVan** là một trợ lý AI tiên tiến hỗ trợ viết rap và thơ song ngữ (Vietnamese & English). Bằng cách kết hợp khả năng tự động bóc tách âm vị, lọc vần cứng qua Vector Database và sinh câu theo ngữ cảnh bằng Gemini 2.5 Flash, GieoVan giúp bạn dễ dàng tìm thấy sự đồng điệu trong từng câu chữ.

---

## Tính năng cốt lõi

- **Phonetic Analysis (Phân tích ngữ âm):** Trích xuất vần điệu chuẩn xác từ từ cuối cùng của câu bằng thuật toán tiếng Việt tùy chỉnh và CMU Dict cho tiếng Anh.
- **Smart Language Detection (Nhận diện ngôn ngữ thông minh):** Thay đổi logic xử lý và prompt sinh câu dựa trên ngôn ngữ (VI/EN) được người dùng tùy chọn từ Frontend.
- **Dynamic Context-Aware RAG with Hard Filtering:** RAG động kết hợp lọc cứng (Hard Filter). Tìm kiếm các câu có cùng vần, cùng cảm xúc (mood) và tác giả từ ChromaDB làm ngữ cảnh tham khảo.
- **Gemini-Powered Lyric Generation:** Tận dụng sức mạnh của Google Gemini 2.5 Flash để chắp bút sinh ra các câu tiếp theo, đảm bảo khớp vần, khớp cảm xúc và tương đương số lượng âm tiết.

## Công nghệ sử dụng

- **Backend Framework:** FastAPI, Python
- **Vector Database:** ChromaDB
- **LLM:** Google GenAI SDK (Gemini 2.5 Flash)
- **Ngôn ngữ học:** `pronouncing` (từ điển CMU), `langdetect`
- **Công cụ & Môi trường:** `python-dotenv`, `uvicorn`, `uv` (hoặc `pip`)

## Hướng dẫn cài đặt

### 1. Clone repository

```bash
git clone https://github.com/yourusername/GieoVan.git
cd GieoVan
```

### 2. Thiết lập Biến môi trường

Tạo file `.env` ở thư mục gốc của dự án và thêm API key của Google Gemini:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Cài đặt Dependencies

Bạn có thể sử dụng trình quản lý gói `uv` (tốc độ cao) hoặc `pip` truyền thống:

```bash
# Dùng uv
uv sync

# HOẶC dùng pip
pip install -r requirements.txt
```

### 4. Khởi tạo Vector Database

Trước khi khởi động server, bạn cần nạp dữ liệu thô vào cơ sở dữ liệu cục bộ (ChromaDB).

```bash
python ingest_data.py
```

_(Script này sẽ đọc kho dữ liệu thô, phân tích vần, thanh điệu và lưu vào thư mục `neon_van_db`.)_

### 5. Chạy Backend

Khởi động server FastAPI:

```bash
uvicorn main:app --reload
```

API sẽ chạy tại `http://localhost:8000`. Bây giờ, bạn chỉ cần mở file `index.html` bằng trình duyệt để trải nghiệm GieoVan!

## Cấu trúc dự án

```text
GieoVan/
│
├── main.py               # Backend chính (Xử lý API, RAG, gọi Gemini)
├── ingest_data.py        # Script xử lý và nạp dữ liệu vào ChromaDB
├── raw_data.json         # Kho dữ liệu thô chứa các câu rap/thơ
├── neon_van_db/          # Database cục bộ của ChromaDB (tự sinh)
├── index.html            # Giao diện người dùng (HTML/CSS/JS thuần)
├── .env                  # Chứa biến môi trường bảo mật (API Key)
└── .gitignore            # Cấu hình bỏ qua file cho Git
```
