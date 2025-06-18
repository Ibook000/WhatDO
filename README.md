# WhatDO 服务端

## 项目简介
WhatDO 服务端是一个基于 FastAPI 的日记与多媒体管理后端，支持文本、图片、音频、视频等内容的上传与管理，适合个人或团队高效整理和追踪日常记录。

## 主要功能
- 日记条目的增删改查
- 多媒体文件上传与管理
- 数据持久化（本地 JSON 文件）
- RESTful API 接口

## 快速开始

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 启动服务
   ```bash
   python main.py
   ```

3. 访问接口文档
   - 主页: http://127.0.0.1:8000/
   - API 文档: http://127.0.0.1:8000/docs

## 文件说明

- `main.py`：主程序入口
- `requirements.txt`：依赖包列表
- `api.txt`：API 说明文档

## 许可证

MIT License