# main.py
# FastAPI 主程序入口

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "server/journal_data.json"
UPLOAD_DIR = "server/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# 日志数据操作

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/journals")
def get_journals():
    return load_data()

@app.post("/journals")
def create_journal(journal: dict):
    data = load_data()
    journal["id"] = max([j["id"] for j in data], default=0) + 1
    data.append(journal)
    save_data(data)
    return journal

@app.get("/journals/{journal_id}")
def get_journal(journal_id: int):
    data = load_data()
    for j in data:
        if j["id"] == journal_id:
            return j
    raise HTTPException(status_code=404, detail="Journal not found")

@app.put("/journals/{journal_id}")
def update_journal(journal_id: int, journal: dict):
    data = load_data()
    for idx, j in enumerate(data):
        if j["id"] == journal_id:
            journal["id"] = journal_id
            data[idx] = journal
            save_data(data)
            return journal
    raise HTTPException(status_code=404, detail="Journal not found")

@app.delete("/journals/{journal_id}")
def delete_journal(journal_id: int):
    data = load_data()
    for idx, j in enumerate(data):
        if j["id"] == journal_id:
            del data[idx]
            save_data(data)
            return {"result": "success"}
    raise HTTPException(status_code=404, detail="Journal not found")

# 多媒体上传
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

@app.get("/media/{filename}")
def get_media(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/stats")
def get_stats():
    data = load_data()
    num_journals = len(data)
    num_media = len(os.listdir(UPLOAD_DIR))
    return {"journals": num_journals, "media": num_media}
