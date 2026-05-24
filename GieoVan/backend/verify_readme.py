import os

def verify_readme():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    readme_path = os.path.abspath(os.path.join(base_dir, "..", "..", "README.md"))
    
    if not os.path.exists(readme_path):
        raise FileNotFoundError(f"README.md not found at expected path: {readme_path}")
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    required_keywords = [
        "vietnamese_lyrics",
        "end_rhyme",
        "mood",
        "author",
        "rhyme_mode",
        "one_word",
        "two_words",
        "semantic_only",
        "GieoVần - Mạng xã hội Thơ ca & Rap Lyrics tích hợp Trợ lý AI",
        "Bảng tính năng chuẩn mạng xã hội",
        "Feature Matrix",
        "Authentication & User Management",
        "Social Features",
        "Advanced AI Assistant",
        "Hybrid Vector Database",
        "Project Architecture",
        "FastAPI",
        "SQLModel",
        "ChromaDB",
        "Google GenAI SDK"
    ]
    
    missing_keywords = []
    for kw in required_keywords:
        if kw.lower() not in content.lower():
            missing_keywords.append(kw)
            
    if missing_keywords:
        raise ValueError(f"README.md is missing required information: {missing_keywords}")
        
    print("README.md verification passed successfully! All social network specifications, feature matrix, database details, architecture stack, and metadata schema are present.")

if __name__ == "__main__":
    verify_readme()
