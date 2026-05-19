import re
import uuid
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# 1. Khởi tạo ChromaDB Client (Persistent - Lưu trữ vật lý xuống đĩa)
chroma_client = chromadb.PersistentClient(path="./neon_van_db")
embedding_fn = DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="vietnamese_lyrics", 
    embedding_function=embedding_fn
)

# 2. Bộ phân tích ngữ âm học để tự động trích xuất metadata khi ingest
class IngestionAnalyzer:
    @staticmethod
    def extract_rhyme_and_tone(word: str) -> tuple:
        word = word.lower().strip()
        word = re.sub(r'[^\w\s]', '', word)
        if not word:
            return "", "ngang"
            
        # Xác định thanh điệu dựa trên dấu tự nhiên của từ
        tones = {
            "sắc": "áắấéếíóốớúứý",
            "huyền": "àằầèềìòồờùừỳ",
            "hỏi": "ảẳẩẻểỉỏổởủửỷ",
            "ngã": "ãẵẫẽễĩõỗỡũữỹ",
            "nặng": "ạặậẹệịọộợụựỵ"
        }
        detected_tone = "ngang"
        for tone_name, chars in tones.items():
            if any(char in word for char in chars):
                detected_tone = tone_name
                break

        # Tách lấy phần vần (nguyên âm + phụ âm cuối)
        vowels = "aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵ"
        match = re.search(f'[{vowels}]+.*$', word)
        if match:
            return match.group(0), detected_tone
        return word, detected_tone

# 3. Tập dữ liệu thô (Mock Data) mang bầu không khí tối giản, trắc ẩn
raw_data = [
    {
        "text": "Bước qua từng con phố ngập tràn ánh đèn dầu",
        "author": "Đen Vâu",
        "mood": "melancholic"
    },
    {
        "text": "Ta thấy mình lạc lõng giữa dòng đời chìm sâu",
        "author": "Ẩn danh",
        "mood": "melancholic"
    },
    {
        "text": "Tiếng còi xe xé nát màn đêm tĩnh mịch này",
        "author": "GhostWriter",
        "mood": "aggressive"
    },
    {
        "text": "Khói thuốc tàn rơi rụng trên đôi bàn tay",
        "author": "Thơ xưa",
        "mood": "melancholic"
    },
    {
        "text": "Dưới ánh đèn neon lập lòe nơi góc quán",
        "author": "HongKong90s",
        "mood": "nostalgic"
    },
    {
        "text": "Bán hết muộn phiền cho những kẻ cùng chung hoạn nạn",
        "author": "Rap Việt",
        "mood": "nostalgic"
    },
    {
        "text": "Đập tan mọi xiềng xích đang cùm kẹp đôi chân",
        "author": "Underground",
        "mood": "aggressive"
    },
    {
        "text": "Ta đứng đây hiên ngang bất kể bao thế nhân",
        "author": "Cổ phong",
        "mood": "aggressive"
    }
]

# 4. Thực hiện đóng gói và Ingest vào Vector Database
print("=== BẮT ĐẦU INGEST DỮ LIỆU VÀO CHROMADB ===")

documents = []
metadatas = []
ids = []

for item in raw_data:
    text = item["text"]
    words = text.split()
    last_word = words[-1] if words else ""
    
    # Trích xuất tự động vần và dấu để làm trường lọc (filter) sau này
    rhyme, tone = IngestionAnalyzer.extract_rhyme_and_tone(last_word)
    
    documents.append(text)
    metadatas.append({
        "end_rhyme": rhyme,
        "tone": tone,
        "mood": item["mood"],
        "author": item["author"],
        "syllables": len(words)
    })
    ids.append(f"lyric_{uuid.uuid4().hex[:8]}")

# Khởi tạo lệnh lưu trữ vào ChromaDB
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print(f"Đã ingest thành công {len(documents)} câu vào collection 'vietnamese_lyrics'.")
print("Cấu trúc metadata mẫu của câu cuối cùng được phân tích:")
print(metadatas[-1])
print("=== HOÀN THÀNH ===")
