#!/usr/bin/env python3
"""
快速API配置脚本
一键配置各种AI模型的示例配置文件
"""

from model_config_manager import ModelConfigManager
import json

def create_local_only_config():
    """创建纯本地模型配置"""
    manager = ModelConfigManager()

    player_configs = []
    for i in range(8):
        player_configs.append({
            "model_name": "Qwen3-32B-AWQ",
            "api_key": "dummy_key"
        })
    player_configs.append({"model_name": "human", "api_key": ""})

    judge_config = {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"}

    config = manager.generate_full_config(player_configs, judge_config)
    manager.save_config(config, "config_local_only.json")
    print("✅ 本地模型配置已创建: config_local_only.json")

def create_openai_config():
    """创建OpenAI模型配置"""
    manager = ModelConfigManager()

    print("⚠️  请先在config_openai.json中填入您的OpenAI API密钥")

    player_configs = []
    for i in range(8):
        player_configs.append({
            "model_name": "gpt-4o-mini",
            "api_key": "your_openai_api_key_here"
        })
    player_configs.append({"model_name": "human", "api_key": ""})

    judge_config = {"model_name": "gpt-4o", "api_key": "your_openai_api_key_here"}

    config = manager.generate_full_config(player_configs, judge_config)
    manager.save_config(config, "config_openai.json")
    print("✅ OpenAI模型配置已创建: config_openai.json")

def create_chinese_models_config():
    """创建国产大模型配置"""
    manager = ModelConfigManager()

    player_configs = [
        {"model_name": "qwen-max", "api_key": "your_qwen_api_key"},
        {"model_name": "glm-4", "api_key": "your_zhipuai_api_key"},
        {"model_name": "deepseek-chat", "api_key": "your_deepseek_api_key"},
        {"model_name": "moonshot-v1-32k", "api_key": "your_moonshot_api_key"},
        {"model_name": "hunyuan-large", "api_key": "your_hunyuan_api_key"},
        {"model_name": "Baichuan4", "api_key": "your_baichuan_api_key"},
        {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
        {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
        {"model_name": "human", "api_key": ""}
    ]

    judge_config = {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"}

    config = manager.generate_full_config(player_configs, judge_config, random_model=True)
    manager.save_config(config, "config_chinese_models.json")
    print("✅ 国产大模型配置已创建: config_chinese_models.json")

def create_premium_models_config():
    """创建高端模型配置（包含推理模型）"""
    manager = ModelConfigManager()

    player_configs = [
        {"model_name": "gpt-4o", "api_key": "your_openai_key"},
        {"model_name": "deepseek-reasoner", "api_key": "your_deepseek_key"},
        {"model_name": "m302/o3-mini", "api_key": "your_m302_key"},
        {"model_name": "grok-3-latest", "api_key": "your_xai_key"},
        {"model_name": "openrouter/anthropic/claude-3.7-sonnet:thinking", "api_key": "your_openrouter_key"},
        {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
        {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
        {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
        {"model_name": "human", "api_key": ""}
    ]

    judge_config = {"model_name": "deepseek-reasoner", "api_key": "your_deepseek_key"}

    config = manager.generate_full_config(player_configs, judge_config, random_model=True)
    manager.save_config(config, "config_premium_models.json")
    print("✅ 高端模型配置已创建: config_premium_models.json")

def create_ai_battle_config():
    """创建AI对战配置（8个不同AI模型对战）"""
    manager = ModelConfigManager()

    player_configs = [
        {"model_name": "gpt-4o-mini", "api_key": "your_openai_key"},
        {"model_name": "qwen-plus", "api_key": "your_qwen_key"},
        {"model_name": "glm-4", "api_key": "your_zhipuai_key"},
        {"model_name": "deepseek-chat", "api_key": "your_deepseek_key"},
        {"model_name": "moonshot-v1-32k", "api_key": "your_moonshot_key"},
        {"model_name": "hunyuan-turbo-latest", "api_key": "your_hunyuan_key"},
        {"model_name": "Baichuan3-Turbo", "api_key": "your_baichuan_key"},
        {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
        {"model_name": "human", "api_key": ""}
    ]

    judge_config = {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"}

    config = manager.generate_full_config(player_configs, judge_config, random_model=False)
    manager.save_config(config, "config_ai_battle.json")
    print("✅ AI对战配置已创建: config_ai_battle.json")

def main():
    print("🚀 AI狼人杀快速配置工具")
    print("=" * 50)

    print("\n选择要创建的配置类型:")
    print("1. 纯本地模型配置 (Qwen3-32B-AWQ)")
    print("2. OpenAI模型配置")
    print("3. 国产大模型混合配置")
    print("4. 高端推理模型配置")
    print("5. AI对战配置 (8个不同AI)")
    print("6. 创建所有配置文件")

    choice = input("\n请选择 (1-6): ").strip()

    if choice == "1":
        create_local_only_config()
    elif choice == "2":
        create_openai_config()
    elif choice == "3":
        create_chinese_models_config()
    elif choice == "4":
        create_premium_models_config()
    elif choice == "5":
        create_ai_battle_config()
    elif choice == "6":
        print("\n📦 创建所有配置文件...")
        create_local_only_config()
        create_openai_config()
        create_chinese_models_config()
        create_premium_models_config()
        create_ai_battle_config()
        print("\n✅ 所有配置文件已创建!")
        print("\n📝 使用说明:")
        print("1. 编辑对应的配置文件，填入您的API密钥")
        print("2. 将配置文件重命名为 config.json")
        print("3. 运行 python web.py 开始游戏")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()