import re
import logging
import pronouncing
from langdetect import detect
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

# Đọc file .env và bơm vào hệ thống NGAY LẬP TỨC khi code vừa chạy
load_dotenv()

app = FastAPI()

# Thêm middleware để mở cổng cho Frontend gọi API thoải mái
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép mọi domain gọi vào (sau này deploy có thể đổi thành link Vercel)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Kết nối duy nhất đến thư mục database trong dự án GieoVan
chroma_client = chromadb.PersistentClient(path="./neon_van_db")
collection = chroma_client.get_or_create_collection(name="vietnamese_lyrics")

# Khởi tạo Gemini Client (sẽ tự động đọc GEMINI_API_KEY từ biến môi trường)
try:
    gemini_client = genai.Client()
except Exception as e:
    logger.warning(f"Could not initialize Gemini Client: {e}")
    gemini_client = None

class LyricsInput(BaseModel):
    text: str
    mood: str = "all"
    author: Optional[str] = None
    lang: str = "vi"

class SearchInput(BaseModel):
    query: str
    end_rhyme: Optional[str] = None
    mood: Optional[str] = None
    limit: int = 5

class SearchMatch(BaseModel):
    text: str
    distance: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchMatch]

class GenerateInput(BaseModel):
    text: str
    mood: str = "all"
    count: int = 3
    lang: str = "vi"

class GenerateResponse(BaseModel):
    suggestions: List[str]

class RhymeAnalyzer:
    """Bộ phân tích ngữ âm tiếng Việt và tiếng Anh để trích xuất phần vần thô (Vần thông)"""
    
    @staticmethod
    def is_vietnamese(text: str) -> bool:
        return bool(re.search(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', text.lower()))

    @staticmethod
    def detect_lang(text: str, last_word: str = "") -> str:
        # 1. Nếu có dấu tiếng Việt -> Chắc chắn là tiếng Việt
        if re.search(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', text.lower()):
            return 'vi'
        # 2. Nếu từ cuối cùng tra được trong từ điển CMU -> Chắc chắn là tiếng Anh
        if last_word and pronouncing.phones_for_word(last_word.lower()):
            return 'en'
        # 3. Fallback
        try:
            return 'en' if detect(text) == 'en' else 'vi'
        except Exception as e:
            logger.warning(f"Language detection failed: {e}. Defaulting to 'vi'.")
            return 'vi'
            
    @staticmethod
    def remove_vietnamese_tones(text: str) -> str:
        tone_map = {
            r'[àáảãạăằắẳẵặâầấẩẫậ]': 'a',
            r'[èéẻẽẹêềếểễệ]': 'e',
            r'[ìíỉĩị]': 'i',
            r'[òóỏõọôồốổỗộơờớởỡợ]': 'o',
            r'[ùúủũụưừứửữự]': 'u',
            r'[ỳýỷỹỵ]': 'y',
            r'[đ]': 'd'
        }
        for regex, replace in tone_map.items():
            text = re.sub(regex, replace, text)
        return text

    @staticmethod
    def extract_rhyme_vi(word: str) -> str:
        word = word.lower().strip()
        word = re.sub(r'[^\w\s]', '', word)
        
        if not word:
            return ""
            
        vowels = "aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵ"
        match = re.search(f'[{vowels}]+.*$', word)
        if match:
            return RhymeAnalyzer.remove_vietnamese_tones(match.group(0))
            return match.group(0)
        return word
        
    @staticmethod
    def extract_rhyme_en(word: str) -> str:
        word = word.lower().strip()
        word = re.sub(r'[^\w\s]', '', word)
        if not word:
            return ""
        phones_list = pronouncing.phones_for_word(word)
        if phones_list:
            return pronouncing.rhyming_part(phones_list[0])
        return ""
        
    @staticmethod
    def get_rhyme(word: str, lang: str) -> str:
        if lang == 'en':
            return RhymeAnalyzer.extract_rhyme_en(word)
        return RhymeAnalyzer.extract_rhyme_vi(word)

def build_chroma_where_clause(end_rhyme: Optional[str] = None, mood: Optional[str] = None, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Helper function tối ưu hóa việc xây dựng mệnh đề filter động cho ChromaDB (DRY)"""
    where_conditions: List[Dict[str, Any]] = []
    if end_rhyme:
        where_conditions.append({"end_rhyme": end_rhyme})
    if mood and mood != "all":
        where_conditions.append({"mood": mood})
    if author:
        where_conditions.append({"author": author})
        
    if len(where_conditions) == 1:
        return where_conditions[0]
    elif len(where_conditions) > 1:
        return {"$and": where_conditions}
    return None

def search_lyrics(query: str, end_rhyme: Optional[str] = None, mood: Optional[str] = None, limit: int = 5) -> List[SearchMatch]:
    where_clause = build_chroma_where_clause(end_rhyme=end_rhyme, mood=mood)
    try:
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        logger.error(f"ChromaDB search query failed for '{query}'. Context: {str(e)}", exc_info=True)
        return []
        
    matches: List[SearchMatch] = []
    if results and results.get("documents") and results["documents"][0]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") and results["metadatas"][0] else [{}] * len(docs)
        dists = results["distances"][0] if results.get("distances") and results["distances"][0] else [0.0] * len(docs)
        
        for doc, meta, dist in zip(docs, metas, dists):
            matches.append(SearchMatch(text=doc, distance=float(dist), metadata=meta))
            
    return matches

@app.post("/api/analyze-and-suggest")
async def analyze_and_suggest(input_data: LyricsInput):
    # HARDCORE PARSING: Chuẩn hóa toàn bộ các kiểu xuống dòng trước khi tách câu
    normalized_text = input_data.text.replace("\\n", "\n")
    lines = [line.strip() for line in re.split(r'[\r\n]+', normalized_text) if line.strip()]
    
    if not lines:
        raise HTTPException(status_code=400, detail="Văn bản trống")
        
    last_line = lines[-1]
    words = last_line.split()
    last_word = words[-1] if words else ""
    
    lang = input_data.lang
    extracted_rhyme = RhymeAnalyzer.get_rhyme(last_word, lang)
    where_clause = build_chroma_where_clause(end_rhyme=extracted_rhyme, mood=input_data.mood, author=input_data.author)
    
    try:
        rag_results = collection.query(
            query_texts=[last_line],
            n_results=5,
            where=where_clause
        )
    except Exception as e:
        logger.error(f"ChromaDB query inside analyze-and-suggest failed: {str(e)}", exc_info=True)
        rag_results = {"documents": [[]], "metadatas": [[]]}

    response = {
        "analysis": {
            "last_word": last_word,
            "detected_rhyme": extracted_rhyme,
            "syllables_count": len(words)
        },
        "contextual_suggestions": []
    }
    
    if rag_results.get("documents") and rag_results["documents"][0]:
        documents = rag_results["documents"][0]
        metas = rag_results["metadatas"][0] if rag_results.get("metadatas") and rag_results["metadatas"][0] else [{}] * len(documents)
        
        for doc, meta in zip(documents, metas):
            if lang == 'en' and RhymeAnalyzer.is_vietnamese(doc):
                continue
            response["contextual_suggestions"].append({
                "text": doc,
                "rhyme": meta.get("end_rhyme"),
                "mood": meta.get("mood"),
                "author": meta.get("author")
            })
            
    return response

@app.post("/api/search", response_model=SearchResponse)
async def api_search_lyrics(input_data: SearchInput) -> SearchResponse:
    matches = search_lyrics(
        query=input_data.query,
        end_rhyme=input_data.end_rhyme,
        mood=input_data.mood,
        limit=input_data.limit
    )
    return SearchResponse(results=matches)

@app.post("/api/generate-next-lines", response_model=GenerateResponse)
async def generate_next_lines(input_data: GenerateInput) -> GenerateResponse:
    # 1. Tiền xử lý chuỗi và bóc tách vần
    normalized_text = input_data.text.replace("\\n", "\n")
    lines = [line.strip() for line in re.split(r'[\r\n]+', normalized_text) if line.strip()]
    
    if not lines:
        raise HTTPException(status_code=400, detail="Văn bản trống")
        
    last_line = lines[-1]
    words = last_line.split()
    last_word = words[-1] if words else ""
    syllables_count = len(words)
    
    lang = input_data.lang
    extracted_rhyme = RhymeAnalyzer.get_rhyme(last_word, lang)
    
    # 2. RAG: Lấy Context từ ChromaDB
    where_clause = build_chroma_where_clause(mood=input_data.mood)
    
    try:
        rag_results = collection.query(
            query_texts=[last_line],
            n_results=5,
            where=where_clause
        )
        docs = rag_results.get("documents")
        context_docs = docs[0] if docs and docs[0] else []
    except Exception as e:
        logger.error(f"ChromaDB query inside generate-next-lines failed: {str(e)}", exc_info=True)
        context_docs = []

    filtered_context_docs = []
    for doc in context_docs:
        if lang == 'en' and RhymeAnalyzer.is_vietnamese(doc):
            continue
        filtered_context_docs.append(doc)
    context_docs = filtered_context_docs

    if not gemini_client:
        logger.error("Gemini client is not initialized due to missing API key or setup failure.")
        return GenerateResponse(suggestions=[])

    # 3. Thiết kế System Instruction và cấu hình sinh JSON
    if lang == 'en':
        context_str = "\n".join(context_docs) if context_docs else "No reference context available."
        if input_data.mood == 'melancholic':
            persona = "a profound US/UK Poet and Contemporary Lyricist who writes soulful, elegant, and deep verses."
        else:
            persona = "a Senior US/UK Rapper and Lyricist who writes sharp, rhythmic street-smart verses."
            
        sys_instruct = (
            f"You are {persona} Your task is to write the next lines of rap/poetry "
            "based on the user's last line and the provided reference context.\n"
            f"Mandatory requirements:\n"
            f"- Generate exactly {input_data.count} next lines.\n"
            f"- The end rhyme of each line must perfectly match the phonetic sound: '{extracted_rhyme}'.\n"
            f"- The mood of the lines must be: {input_data.mood}.\n"
            f"- The syllable count for each line should be approximately: {syllables_count} syllables.\n"
            "- The generated lines MUST logically flow from the user's current line, maintaining a consistent theme, imagery, and emotional tone. Avoid using overly cliché or randomly violent words unless explicitly requested by the mood.\n"
            "- Return ONLY valid JSON according to the requested schema."
        )
        prompt = f"Current line:\n{last_line}\n\nReference context:\n{context_str}\n\nPlease generate {input_data.count} next lines."
    else:
        context_str = "\n".join(context_docs) if context_docs else "Không có ngữ cảnh tham khảo."
        if input_data.mood == 'melancholic':
            persona = "một Nhà thơ và Nhạc sĩ chuyên nghiệp, viết những câu từ sâu lắng, nhẹ nhàng, giàu hình ảnh và nhịp điệu."
        else:
            persona = "một Rapper Senior người Việt, viết những câu rap sắc sảo, gieo vần điêu luyện."
            
        sys_instruct = (
            "Bạn là một Nhà thơ và Nhạc sĩ chuyên nghiệp người Việt, viết những câu từ sâu lắng, nhẹ nhàng, giàu hình ảnh.\n"
            "Nhiệm vụ của bạn là viết tiếp các câu thơ/rap dựa trên câu cuối cùng của người dùng.\n"
            "Yêu cầu bắt buộc:\n"
            f"- Sinh ra chính xác {input_data.count} câu tiếp theo.\n"
            f"- Vần kết thúc (end_rhyme) của mỗi câu PHẢI hiệp vần hoàn toàn với từ '{last_word}' (có phần vần gốc là '{extracted_rhyme}'). Ví dụ nếu từ gốc là 'thể', các câu tiếp theo phải kết thúc bằng các từ cùng vần và thanh điệu như: dễ, bể, kể, lệ, thế, dế... Tuyệt đối không gieo lệch sang vần khác.\n"
            f"- Cảm xúc (mood) của câu: {input_data.mood}.\n"
            f"- Số lượng âm tiết mỗi câu xấp xỉ: {syllables_count} từ.\n"
            "- Chỉ trả về JSON thuần túy theo schema yêu cầu."
        )
        prompt = f"Câu hiện tại:\n{last_line}\n\nNgữ cảnh tham khảo:\n{context_str}\n\nHãy sinh ra {input_data.count} câu tiếp theo."
    
    # 4. Gọi Gemini API an toàn bằng đồng bộ
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                response_mime_type="application/json",
                response_schema=GenerateResponse,
                temperature=0.7
            )
        )
        
        return GenerateResponse.model_validate_json(response.text)
    except Exception as e:
        logger.error(f"Gemini API generation failed: {str(e)}", exc_info=True)
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            raise HTTPException(status_code=429, detail="Giới hạn gọi AI đã hết (API Rate Limit). Vui lòng đợi khoảng 1 phút rồi thử lại.")
            
        raise HTTPException(status_code=500, detail="Hệ thống AI đang tạm thời gián đoạn. Vui lòng thử lại sau.")