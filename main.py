import os
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI(title="Daily Journal API", version="1.0.0")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 数据模型
class MediaItem(BaseModel):
    id: str
    type: str  # 'image', 'video', 'audio'
    url: str
    name: str
    size: int
    thumbnail: Optional[str] = None

class Mood(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    CALM = "calm"
    STRESSED = "stressed"

class JournalEntry(BaseModel):
    id: Optional[str] = None
    date: str
    content: str
    media: List[MediaItem] = []
    mood: Optional[Mood] = None
    tags: List[str] = []
    created_at: str = Field(alias='createdAt')
    updated_at: str = Field(alias='updatedAt')

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# 文件存储配置
DATA_FILE = "journal_data.json"

# 内存存储（实际项目中应该使用数据库）
journal_entries: List[JournalEntry] = []

# 加载日记条目
def load_entries():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 将加载的数据转换为 JournalEntry 对象列表
            return [JournalEntry(**entry) for entry in data]
    return []

# 保存日记条目
def save_entries():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        # 将 JournalEntry 对象列表转换为字典列表进行保存
        json.dump([entry.model_dump(by_alias=True) for entry in journal_entries], f, ensure_ascii=False, indent=4)

# API路由
@app.get("/")
async def root():
    return {"message": "Daily Journal API is running"}

@app.get("/api/entries", response_model=List[JournalEntry])
async def get_entries():
    """获取所有日记条目"""
    return sorted(journal_entries, key=lambda x: x.date, reverse=True)

@app.get("/api/entries/{entry_id}", response_model=JournalEntry)
async def get_entry(entry_id: str):
    """通过ID获取单个日记条目"""
    for entry in journal_entries:
        if entry.id == entry_id:
            return entry
    raise HTTPException(status_code=404, detail="Entry not found")

@app.post("/api/entries", response_model=JournalEntry)
async def create_entry(entry: JournalEntry):
    """创建新的日记条目"""
    if not entry.id:
        entry.id = str(uuid.uuid4())
    
    current_time = datetime.now().isoformat()
    entry.created_at = current_time
    entry.updated_at = current_time
    
    journal_entries.append(entry)
    save_entries() # 保存数据
    return entry

@app.put("/api/entries/{entry_id}", response_model=JournalEntry)
async def update_entry(entry_id: str, entry_data: JournalEntry):
    """更新日记条目"""
    for i, entry in enumerate(journal_entries):
        if entry.id == entry_id:
            # 使用 model_copy 进行部分更新，并确保 updated_at 更新
            updated_entry = entry.model_copy(update=entry_data.model_dump(exclude_unset=True))
            updated_entry.id = entry_id # 确保ID不变
            updated_entry.updated_at = datetime.now().isoformat()
            journal_entries[i] = updated_entry
            save_entries() # 保存数据
            return updated_entry
    
    raise HTTPException(status_code=404, detail="Entry not found")

@app.delete("/api/entries/{entry_id}")
async def delete_entry(entry_id: str):
    """删除日记条目"""
    for i, entry in enumerate(journal_entries):
        if entry.id == entry_id:
            del journal_entries[i]
            save_entries() # 保存数据
            return {"message": "Entry deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Entry not found")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传媒体文件"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # 创建上传目录
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 返回文件信息
    return [{
        "id": str(uuid.uuid4()),
        "type": "image" if file.content_type and file.content_type.startswith("image/") else 
               "video" if file.content_type and file.content_type.startswith("video/") else "audio",
        "url": f"/uploads/{unique_filename}",
        "name": file.filename,
        "size": len(content)
    }]

@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    if not journal_entries:
        return {
            "total_entries": 0,
            "total_days": 0,
            "average_entries_per_day": 0,
            "most_used_tags": [],
            "mood_distribution": {}
        }
    
    # 基本统计
    total_entries = len(journal_entries)
    
    # 统计唯一天数
    unique_dates = set(entry.date.split('T')[0] for entry in journal_entries)
    total_days = len(unique_dates)
    
    average_entries_per_day = total_entries / total_days if total_days > 0 else 0
    
    # 标签统计
    tag_counts = {}
    for entry in journal_entries:
        for tag in entry.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    most_used_tags = [
        {"tag": tag, "count": count}
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    # 心情分布
    mood_distribution = {}
    for entry in journal_entries:
        if entry.mood:
            mood_distribution[entry.mood] = mood_distribution.get(entry.mood, 0) + 1
    
    return {
        "total_entries": total_entries,
        "total_days": total_days,
        "average_entries_per_day": round(average_entries_per_day, 2),
        "most_used_tags": most_used_tags,
        "mood_distribution": mood_distribution
    }

if __name__ == "__main__":
    # 在应用启动时加载现有数据
    journal_entries.extend(load_entries())
    uvicorn.run(app, host="127.0.0.1", port=8000)
