#!/usr/bin/env python3
"""
AI模型配置管理器
支持配置多种AI API，方便用户管理和切换不同的AI模型
"""

import json
import os
from typing import Dict, List, Any

class ModelConfigManager:
    def __init__(self):
        self.supported_models = {
            # 本地模型
            "local": {
                "name": "本地模型",
                "models": ["Qwen3-32B-AWQ"],
                "api_key_required": False,
                "base_url": "http://172.16.13.100:8000/v1",
                "description": "本地部署的Qwen模型"
            },

            # OpenAI模型
            "openai": {
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o1-mini", "o3-mini", "o4-mini"],
                "api_key_required": True,
                "base_url": "https://api.openai.com/v1",
                "description": "OpenAI官方模型"
            },

            # DeepSeek模型
            "deepseek": {
                "name": "DeepSeek",
                "models": ["deepseek-chat", "deepseek-reasoner"],
                "api_key_required": True,
                "base_url": "https://api.deepseek.com",
                "description": "DeepSeek AI模型"
            },

            # 通义千问模型
            "qwen": {
                "name": "通义千问",
                "models": ["qwen-max", "qwen-plus", "qwen-long", "qwen-max-longcontext", "qwen-max-2025-01-25"],
                "api_key_required": True,
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "description": "阿里云通义千问模型"
            },

            # 智谱AI模型
            "zhipuai": {
                "name": "智谱AI",
                "models": ["glm-3-turbo", "glm-4", "glm-4v", "glm-4-plus"],
                "api_key_required": True,
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "description": "智谱AI GLM模型"
            },

            # 月之暗面模型
            "moonshot": {
                "name": "月之暗面",
                "models": ["moonshot-v1-32k"],
                "api_key_required": True,
                "base_url": "https://api.moonshot.cn/v1",
                "description": "月之暗面Kimi模型"
            },

            # 豆包模型
            "doubao": {
                "name": "豆包",
                "models": ["ep-xxxx"],  # 需要具体endpoint
                "api_key_required": True,
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "description": "字节跳动豆包模型"
            },

            # 腾讯混元模型
            "hunyuan": {
                "name": "腾讯混元",
                "models": ["hunyuan-large", "hunyuan-turbo-latest"],
                "api_key_required": True,
                "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
                "description": "腾讯混元大模型"
            },

            # 百川AI模型
            "baichuan": {
                "name": "百川AI",
                "models": ["Baichuan4", "Baichuan3-Turbo", "Baichuan3-Turbo-128k", "Baichuan2-Turbo", "Baichuan2-Turbo-192k"],
                "api_key_required": True,
                "base_url": "https://api.baichuan-ai.com/v1",
                "description": "百川AI大模型"
            },

            # xAI模型
            "xai": {
                "name": "xAI",
                "models": ["grok-3-latest", "grok-3-mini-beta", "grok-3-mini-fast-beta"],
                "api_key_required": True,
                "base_url": "https://api.x.ai/v1",
                "description": "马斯克xAI Grok模型"
            },

            # SiliconFlow模型
            "siliconflow": {
                "name": "SiliconFlow",
                "models": ["deepseek-ai/DeepSeek-R1", "Pro/deepseek-ai/DeepSeek-R1"],
                "api_key_required": True,
                "base_url": "https://api.siliconflow.cn/v1",
                "description": "SiliconFlow推理模型"
            },

            # OpenRouter模型
            "openrouter": {
                "name": "OpenRouter",
                "models": [
                    "openrouter/google/gemini-2.5-pro-exp-03-25:free",
                    "openrouter/anthropic/claude-3.7-sonnet",
                    "openrouter/anthropic/claude-3.7-sonnet:thinking",
                    "openrouter/moonshotai/kimi-vl-a3b-thinking:free",
                    "openrouter/deepseek/deepseek-r1:free"
                ],
                "api_key_required": True,
                "base_url": "https://openrouter.ai/api/v1",
                "description": "OpenRouter多模型聚合"
            },

            # M302AI模型
            "m302ai": {
                "name": "M302AI",
                "models": ["m302/o3-mini", "m302/o3-mini-2025-01-31", "gemini-2.0-flash-thinking-exp-01-21", "claude-3-7-sonnet-latest", "claude-3-7-sonnet-thinking"],
                "api_key_required": True,
                "base_url": "https://api.302.ai",
                "description": "M302AI推理模型"
            }
        }

    def list_supported_providers(self) -> List[Dict[str, Any]]:
        """列出所有支持的AI提供商"""
        return [
            {
                "id": provider_id,
                "name": info["name"],
                "models": info["models"],
                "api_key_required": info["api_key_required"],
                "description": info["description"]
            }
            for provider_id, info in self.supported_models.items()
        ]

    def create_config_template(self, provider: str, model: str, api_key: str = "") -> Dict[str, Any]:
        """为指定提供商和模型创建配置模板"""
        if provider not in self.supported_models:
            raise ValueError(f"不支持的提供商: {provider}")

        provider_info = self.supported_models[provider]
        if model not in provider_info["models"]:
            raise ValueError(f"提供商 {provider} 不支持模型 {model}")

        return {
            "model_name": model,
            "api_key": api_key,
            "provider": provider,
            "base_url": provider_info["base_url"]
        }

    def generate_full_config(self, player_configs: List[Dict[str, Any]],
                           judge_config: Dict[str, Any],
                           randomize_roles: bool = True,
                           randomize_position: bool = True,
                           random_model: bool = False) -> Dict[str, Any]:
        """生成完整的游戏配置文件"""

        # 检查人类玩家
        human_players = [p for p in player_configs if p.get("model_name") == "human"]
        if not human_players:
            print("⚠️  警告：没有配置人类玩家")

        # 生成模型列表（如果启用随机模型）
        models = []
        if random_model:
            ai_players = [p for p in player_configs if p.get("model_name") != "human"]
            models = [{"model_name": p["model_name"], "api_key": p["api_key"]} for p in ai_players]

        return {
            "players": player_configs,
            "judge": judge_config,
            "randomize_roles": randomize_roles,
            "randomize_position": randomize_position,
            "random_model": random_model,
            "models": models,
            "display_role": True,
            "display_thinking": True,
            "display_witch_action": True,
            "display_wolf_action": True,
            "display_hunter_action": True,
            "display_divine_action": True,
            "display_vote_action": True,
            "display_model": True,
            "auto_play": True
        }

    def save_config(self, config: Dict[str, Any], filename: str = "config.json"):
        """保存配置到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置已保存到 {filename}")

    def print_providers(self):
        """打印所有支持的提供商"""
        print("\n🤖 支持的AI模型提供商:")
        print("=" * 80)

        for provider_id, info in self.supported_models.items():
            print(f"\n📌 {info['name']} ({provider_id})")
            print(f"   描述: {info['description']}")
            print(f"   模型: {', '.join(info['models'][:3])}{'...' if len(info['models']) > 3 else ''}")
            print(f"   API密钥: {'必需' if info['api_key_required'] else '可选'}")
            print(f"   基础URL: {info['base_url']}")

def main():
    """命令行交互界面"""
    manager = ModelConfigManager()

    print("🎮 AI狼人杀模型配置管理器")
    print("=" * 50)

    while True:
        print("\n请选择操作:")
        print("1. 查看支持的AI提供商")
        print("2. 创建游戏配置文件")
        print("3. 创建混合模型配置")
        print("4. 退出")

        choice = input("\n请输入选项 (1-4): ").strip()

        if choice == "1":
            manager.print_providers()

        elif choice == "2":
            print("\n创建游戏配置文件:")
            provider = input("请输入提供商ID (如: openai, qwen, local): ").strip()
            model = input("请输入模型名称: ").strip()
            api_key = input("请输入API密钥 (本地模型可留空): ").strip()

            try:
                # 创建9个玩家配置（8个AI + 1个人类）
                player_configs = []
                for i in range(8):
                    player_configs.append({
                        "model_name": model,
                        "api_key": api_key
                    })
                player_configs.append({"model_name": "human", "api_key": ""})

                judge_config = {"model_name": model, "api_key": api_key}

                config = manager.generate_full_config(player_configs, judge_config)
                manager.save_config(config)

            except Exception as e:
                print(f"❌ 创建配置失败: {e}")

        elif choice == "3":
            print("\n创建混合模型配置示例:")
            print("这里创建一个包含多种AI模型的配置示例")

            # 示例混合配置
            player_configs = [
                {"model_name": "gpt-4o", "api_key": "your_openai_key"},
                {"model_name": "qwen-max", "api_key": "your_qwen_key"},
                {"model_name": "glm-4", "api_key": "your_zhipuai_key"},
                {"model_name": "deepseek-chat", "api_key": "your_deepseek_key"},
                {"model_name": "moonshot-v1-32k", "api_key": "your_moonshot_key"},
                {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
                {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
                {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"},
                {"model_name": "human", "api_key": ""}
            ]

            judge_config = {"model_name": "Qwen3-32B-AWQ", "api_key": "dummy_key"}

            config = manager.generate_full_config(player_configs, judge_config, random_model=True)
            manager.save_config(config, "config_mixed_models.json")
            print("✅ 混合模型配置已保存到 config_mixed_models.json")

        elif choice == "4":
            print("👋 再见!")
            break

        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main()