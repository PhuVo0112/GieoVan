import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

app = FastAPI()

# Khởi tạo ChromaDB Client (Persistent)
chroma_client = chromadb.PersistentClient(path="./neon_van_db")
# Sử dụng embedding function mặc định hoặc cấu hình FastEmbed tại đây
embedding_fn = DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="vietnamese_lyrics", 
    embedding_function=embedding_fn
)

class LyricsInput(BaseModel):
    text: str
    mood: str = "all"

class RhymeAnalyzer:
    """Bộ phân tích ngữ âm tiếng Việt để trích xuất phần vần"""
    @staticmethod
    def extract_rhyme(word: str) -> str:
        word = word.lower().strip()
        # Loại bỏ các ký tự đặc biệt
        word = re.sub(r'[^\w\s]', '', word)
        
        if not word:
            return ""
            
        # Bảng ký tự nguyên âm tiếng Việt để xác định phần vần
        vowels = "aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵ"
        
        # Tìm vị trí nguyên âm đầu tiên xuất hiện từ trái sang phải
        match = re.search(f'[{vowels}]+.*$', word)
        if match:
            # Trích xuất phần vần (bao gồm cả nguyên âm và phụ âm cuối nếu có)
            rhyme = match.group(0)
            # Chuẩn hóa dấu (Bỏ dấu để tìm vần thông, giữ dấu để tìm vần chính xác)
            # Tạm thời trả về phần vần thô để tối ưu hóa việc khớp vần thông
            return rhyme
        return word

@app.post("/api/analyze-and-suggest")
async def analyze_and_suggest(input_data: LyricsInput):
    lines = [line.strip() for line in input_data.text.split("\n") if line.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="Văn bản trống")
        
    last_line = lines[-1]
    words = last_line.split()
    last_word = words[-1] if words else ""
    
    # 1. Xử lý tìm vần cứng qua thuật toán Phonetic
    extracted_rhyme = RhymeAnalyzer.extract_rhyme(last_word)
    
    # 2. Xử lý RAG tìm ý tưởng liên quan dựa trên ngữ nghĩa câu cuối
    # Lọc theo Mood nếu người dùng có yêu cầu
    where_clause = {"mood": input_data.mood} if input_data.mood != "all" else None
    
    try:
        rag_results = collection.query(
            query_texts=[last_line],
            n_results=5,
            where=where_clause
        )
    except Exception as e:
        rag_results = {"documents": [[]], "metadatas": [[]]}

    # 3. Tổng hợp kết quả phản hồi
    response = {
        "analysis": {
            "last_word": last_word,
            "detected_rhyme": extracted_rhyme,
            "syllables_count": len(words)
        },
        "contextual_suggestions": []
    }
    
    # Cấu trúc lại dữ liệu trả về từ ChromaDB
    if rag_results["documents"] and rag_results["documents"][0]:
        for doc, meta in zip(rag_results["documents"][0], rag_results["metadatas"][0]):
            response["contextual_suggestions"].append({
                "text": doc,
                "rhyme": meta.get("end_rhyme"),
                "mood": meta.get("mood")
            })
            
    return response