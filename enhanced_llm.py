"""
增强版LLM模块
支持从环境变量自动读取API密钥
"""

from llm import BaseLlm, BuildModel as OriginalBuildModel
import os
import json
from typing import Dict, Any, Optional

class EnhancedLlmManager:
    """增强的LLM管理器，自动处理API密钥"""

    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.provider_configs = {
            "openai": {
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o1-mini", "o3-mini", "o4-mini"],
                "env_key": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1"
            },
            "deepseek": {
                "models": ["deepseek-chat", "deepseek-reasoner"],
                "env_key": "DEEPSEEK_API_KEY",
                "base_url": "https://api.deepseek.com"
            },
            "qwen": {
                "models": ["qwen-max", "qwen-plus", "qwen-long", "qwen-max-longcontext", "qwen-max-2025-01-25"],
                "env_key": "QWEN_API_KEY",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
            },
            "zhipuai": {
                "models": ["glm-3-turbo", "glm-4", "glm-4v", "glm-4-plus"],
                "env_key": "ZHIPUAI_API_KEY",
                "base_url": "https://open.bigmodel.cn/api/paas/v4"
            },
            "moonshot": {
                "models": ["moonshot-v1-32k"],
                "env_key": "MOONSHOT_API_KEY",
                "base_url": "https://api.moonshot.cn/v1"
            },
            "doubao": {
                "models": ["ep-20250114111111-example"],  # 需要具体endpoint
                "env_key": "DOUBAO_API_KEY",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3"
            },
            "hunyuan": {
                "models": ["hunyuan-large", "hunyuan-turbo-latest"],
                "env_key": "HUNYUAN_API_KEY",
                "base_url": "https://api.hunyuan.cloud.tencent.com/v1"
            },
            "baichuan": {
                "models": ["Baichuan4", "Baichuan3-Turbo", "Baichuan3-Turbo-128k", "Baichuan2-Turbo", "Baichuan2-Turbo-192k"],
                "env_key": "BAICHUAN_API_KEY",
                "base_url": "https://api.baichuan-ai.com/v1"
            },
            "xai": {
                "models": ["grok-3-latest", "grok-3-mini-beta", "grok-3-mini-fast-beta"],
                "env_key": "XAI_API_KEY",
                "base_url": "https://api.x.ai/v1"
            },
            "siliconflow": {
                "models": ["deepseek-ai/DeepSeek-R1", "Pro/deepseek-ai/DeepSeek-R1"],
                "env_key": "SILICONFLOW_API_KEY",
                "base_url": "https://api.siliconflow.cn/v1"
            },
            "openrouter": {
                "models": [
                    "openrouter/google/gemini-2.5-pro-exp-03-25:free",
                    "openrouter/anthropic/claude-3.7-sonnet",
                    "openrouter/anthropic/claude-3.7-sonnet:thinking",
                    "openrouter/moonshotai/kimi-vl-a3b-thinking:free",
                    "openrouter/deepseek/deepseek-r1:free"
                ],
                "env_key": "OPENROUTER_API_KEY",
                "base_url": "https://openrouter.ai/api/v1"
            },
            "m302ai": {
                "models": ["m302/o3-mini", "m302/o3-mini-2025-01-31", "gemini-2.0-flash-thinking-exp-01-21", "claude-3-7-sonnet-latest", "claude-3-7-sonnet-thinking"],
                "env_key": "M302AI_API_KEY",
                "base_url": "https://api.302.ai"
            }
        }

    def _load_api_keys(self) -> Dict[str, str]:
        """从.env文件加载API密钥"""
        api_keys = {}

        # 尝试加载.env文件
        if os.path.exists('.env'):
            from dotenv import load_dotenv
            load_dotenv()

            # 读取所有环境变量
            for key, value in os.environ.items():
                if key.endswith('_API_KEY'):
                    api_keys[key] = value

        return api_keys

    def get_api_key(self, provider: str) -> Optional[str]:
        """获取指定提供商的API密钥"""
        if provider in self.provider_configs:
            env_key = self.provider_configs[provider]["env_key"]
            return self.api_keys.get(env_key)
        return None

    def get_provider_for_model(self, model_name: str) -> Optional[str]:
        """根据模型名称获取提供商"""
        for provider, config in self.provider_configs.items():
            if model_name in config["models"]:
                return provider
        return None

    def build_model_with_auto_key(self, model_name: str, api_key: str = None, force_json: bool = False):
        """自动获取API密钥并构建模型"""

        # 如果是本地模型，使用原来的方式
        if model_name == "Qwen3-32B-AWQ":
            return OriginalBuildModel(model_name, api_key or "dummy_key", force_json)

        # 如果是human，返回HumanLlm
        if model_name == "human":
            return OriginalBuildModel(model_name, "", force_json)

        # 尝试自动获取API密钥
        provider = self.get_provider_for_model(model_name)
        if provider and not api_key:
            auto_key = self.get_api_key(provider)
            if auto_key:
                print(f"🔑 自动使用环境变量中的 {provider} API密钥")
                return OriginalBuildModel(model_name, auto_key, force_json)

        # 使用提供的API密钥或原来的方式
        return OriginalBuildModel(model_name, api_key, force_json)

    def validate_config(self, config_path: str = "config.json") -> Dict[str, Any]:
        """验证配置文件中的API密钥"""
        if not os.path.exists(config_path):
            return {"valid": False, "error": f"配置文件 {config_path} 不存在"}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            issues = []
            warnings = []

            # 检查玩家配置
            for i, player in enumerate(config.get("players", [])):
                model_name = player.get("model_name", "")
                api_key = player.get("api_key", "")

                if model_name == "human":
                    continue

                if not api_key:
                    provider = self.get_provider_for_model(model_name)
                    if provider:
                        auto_key = self.get_api_key(provider)
                        if auto_key:
                            warnings.append(f"玩家{i+1}: 将自动使用环境变量中的{provider} API密钥")
                        else:
                            issues.append(f"玩家{i+1}: 缺少{model_name}的API密钥，且环境变量中未找到")
                    else:
                        issues.append(f"玩家{i+1}: 未知模型 {model_name}")

            # 检查裁判配置
            judge = config.get("judge", {})
            judge_model = judge.get("model_name", "")
            judge_key = judge.get("api_key", "")

            if judge_model and judge_model != "human" and not judge_key:
                provider = self.get_provider_for_model(judge_model)
                if provider:
                    auto_key = self.get_api_key(provider)
                    if auto_key:
                        warnings.append(f"裁判: 将自动使用环境变量中的{provider} API密钥")
                    else:
                        issues.append(f"裁判: 缺少{judge_model}的API密钥，且环境变量中未找到")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings
            }

        except Exception as e:
            return {"valid": False, "error": f"配置文件解析错误: {str(e)}"}

# 全局增强管理器实例
enhanced_manager = EnhancedLlmManager()

def BuildModel(model_name: str, api_key: str = None, force_json: bool = False):
    """增强的BuildModel函数，支持自动API密钥获取"""
    return enhanced_manager.build_model_with_auto_key(model_name, api_key, force_json)

def validate_api_config(config_path: str = "config.json"):
    """验证API配置"""
    return enhanced_manager.validate_config(config_path)

def list_supported_models():
    """列出所有支持的模型"""
    print("\n🤖 支持的AI模型:")
    print("=" * 80)

    for provider, config in enhanced_manager.provider_configs.items():
        print(f"\n📌 {provider.upper()}")
        print(f"   模型: {', '.join(config['models'][:3])}{'...' if len(config['models']) > 3 else ''}")
        print(f"   环境变量: {config['env_key']}")
        has_key = enhanced_manager.get_api_key(provider) is not None
        print(f"   API密钥: {'✅ 已配置' if has_key else '❌ 未配置'}")

if __name__ == "__main__":
    print("🔧 API配置验证工具")

    # 列出支持的模型
    list_supported_models()

    # 验证当前配置
    print("\n📋 验证当前配置...")
    result = validate_api_config()

    if result["valid"]:
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败")
        for issue in result.get("issues", []):
            print(f"   - {issue}")

    if result.get("warnings"):
        print("⚠️  警告:")
        for warning in result.get("warnings", []):
            print(f"   - {warning}")