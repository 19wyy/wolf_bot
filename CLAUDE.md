# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个AI狼人杀游戏项目，支持多个AI模型与人类玩家混合对战。项目使用FastAPI作为后端Web框架，前端基于PIXIJS构建可视化游戏界面。

## 常用开发命令

### 启动开发服务器
```bash
python web.py
```
服务器运行在 http://127.0.0.1:8000/

### 回放游戏
```bash
python web.py <回放文件路径>
```
回放文件位于 `logs/replay_{timestamp}.json`

### 安装依赖
```bash
pip install -e .
# 或者使用 pip 安装 pyproject.toml 中的依赖
pip install colorama dashscope fastapi openai pydantic pyyaml requests uvicorn volcengine-python-sdk zhipuai
```

## 核心架构

### 后端架构

**游戏核心 (`game.py`)**
- `WerewolfGame` 类：管理游戏状态、玩家、回合流程
- 游戏配置：通过 `config.json` 管理玩家模型、显示选项等
- 支持的功能：角色分配、投票、技能使用、胜负判定

**多模型支持 (`llm.py`)**
- `BaseLlm` 基类：统一的模型接口
- 支持的模型提供商：
  - OpenAI (GPT系列)
  - DeepSeek (deepseek-chat, deepseek-reasoner)
  - 通义千问 (qwen系列)
  - 智谱AI (glm系列)
  - 百川AI (Baichuan系列)
  - 月之暗面 (Kimi)
  - 豆包 (Doubao)
  - 腾讯混元
  - Grok (xAI)
  - SiliconFlow
  - M302AI (支持o3-mini等推理模型)
- `BuildModel()` 工厂函数：根据模型名称创建对应实例

**Web API (`web.py`)**
- FastAPI应用，提供RESTful接口
- 游戏状态管理和操作API
- 支持实时游戏和回放模式
- 游戏记录和存储功能

**角色系统 (`role.py`)**
- `BaseRole` 基类：角色行为和AI交互
- 具体角色类：狼人、预言家、女巫、猎人、村民
- 每个角色都有对应的AI模型和策略提示

### 前端架构

**游戏界面 (`public/src/`)**
- 基于 PIXIJS 的2D渲染引擎
- 模块化结构：
  - `game.js`: 游戏逻辑控制
  - `ui.js`: 用户界面管理
  - `action.js`: 游戏动作封装
  - `data.js`: 数据和API调用
  - `utils.js`: 工具函数

**资源文件 (`public/assets/`)**
- 玩家头像、背景图片、UI元素
- 不同AI模型的logo图片

### 配置系统

**游戏配置 (`config.json`)**
项目需要 `config.json` 文件配置游戏参数：
- 玩家列表和模型分配
- API密钥配置
- 显示选项（角色、思考过程、技能使用等）
- 随机化选项（角色、位置、模型分配）

**提示模板 (`prompts/`)**
- 各角色和行为的YAML格式提示模板
- 游戏规则和策略指导
- 支持中文提示词

## 日志和存储

**日志系统**
- `logs/` 目录存储游戏记录
- `result_{timestamp}.txt`: 游戏结果和玩家配置
- `replay_{timestamp}.json`: 完整游戏回放数据

**历史记录 (`history.py`)**
- 游戏事件的详细记录
- 用于AI模型的上下文理解

## 开发注意事项

1. **模型配置**: 使用前需要正确配置各种AI模型的API密钥
2. **提示词模板**: 游戏行为和策略主要由提示词模板决定，修改模板会影响AI表现
3. **前端依赖**: 前端依赖PIXIJS库，确保网络连接正常
4. **游戏平衡**: 角色配置和技能参数需要仔细调整以保持游戏平衡
5. **并发处理**: 当前版本主要处理单个游戏实例

## 多AI模型支持

项目已支持多种主流AI模型，拥有完整的logo图标展示系统：

**支持的AI提供商:**
- 🏠 **本地模型**: Qwen3-32B-AWQ (您的本地部署)
- 🤖 **OpenAI**: GPT系列 (gpt-4o, gpt-4.1, o1, o3等)
- 🧠 **DeepSeek**: deepseek-chat, deepseek-reasoner
- ☁️ **通义千问**: qwen-max, qwen-plus等
- 🧬 **智谱AI**: GLM系列 (glm-4, glm-4v等)
- 🌙 **月之暗面**: Kimi系列
- 🐸 **豆包**: 火山引擎模型
- 🐲 **腾讯混元**: hunyuan系列
- 🏔️ **百川AI**: Baichuan系列
- 🚀 **xAI**: Grok系列
- ⚡ **SiliconFlow**: 推理模型
- 🔗 **OpenRouter**: 多模型聚合
- 🎯 **M302AI**: 高级推理模型

**快速配置工具:**
```bash
# 运行快速配置向导
python setup_apis.py

# 运行交互式配置管理器
python model_config_manager.py

# 验证API配置
python enhanced_llm.py
```

**配置文件示例:**
- `config_local_only.json` - 纯本地模型
- `config_openai.json` - OpenAI模型
- `config_chinese_models.json` - 国产大模型混合
- `config_premium_models.json` - 高端推理模型
- `config_ai_battle.json` - AI对战配置

**环境变量配置:**
1. 复制 `.env.example` 为 `.env`
2. 填入您的API密钥
3. 系统会自动读取环境变量中的密钥

## 扩展指南

**添加新AI模型**
1. 在 `llm.py` 中继承 `BaseLlm` 类
2. 实现 `generate()` 方法
3. 将模型添加到 `BuildModel()` 工厂函数
4. 更新支持模型列表

**使用增强版LLM管理器**
```python
from enhanced_llm import BuildModel, validate_api_config

# 自动获取API密钥
model = BuildModel("gpt-4o")  # 自动从环境变量读取密钥

# 验证配置
result = validate_api_config("config.json")
```

**添加新角色**
1. 在 `role.py` 中创建新的角色类继承 `BaseRole`
2. 实现角色的特殊技能方法
3. 创建对应的提示模板文件
4. 在游戏初始化中添加角色分配逻辑

**修改游戏规则**
1. 主要逻辑在 `game.py` 的 `WerewolfGame` 类
2. 胜负条件在 `check_winner()` 方法
3. 回合流程在前端 `game.js` 中控制

## Logo资源

项目包含完整的AI模型logo图标：
- `public/assets/logo_*.png` - 各AI提供商的官方logo
- 前端会自动根据玩家使用的模型显示对应logo
- 支持动态加载和显示