from openai import OpenAI
from dashscope import Generation
from http import HTTPStatus
from zhipuai import ZhipuAI
import json
import dashscope
import requests
import http.client
import re
import logging
import socket
import datetime
import os


logger = logging.getLogger(__name__)

class BaseLlm():
    def __init__(self, model_name, force_json=False):
        
        self.model_name = model_name
        self.force_json = force_json
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    def prepare_messages(self, message, chat_history):
        messages = []
        for msg in chat_history:
            messages.append({"role": "assistant" if msg["role"] == "bot" else "user", "content": msg["content"]})
        messages.append({"role": "user", "content": message})
        return messages

    def openai_like_generate(self, messages, stream=True, extra_body=None, **kwargs):
        try:
            # 设置默认参数以增加AI思考深度
            default_params = {
                "max_tokens": 8192,  # 增加最大token数量
                "temperature": 0.8,    # 稍微提高创造性
                "top_p": 0.95,        # 增加多样性
                "frequency_penalty": 0.1,  # 减少重复
                "presence_penalty": 0.1   # 鼓励新话题
            }

            params = {"model": self.model_name, "messages": messages, "stream": stream}
            if extra_body:
                params["extra_body"] = extra_body
            params.update(default_params)
            params.update(kwargs)
            response = self.client.chat.completions.create(**params)
            if stream:
                full_response = ""
                for chunk in response:
                    if chunk.choices and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        print(content, end="", flush=True)
                return full_response, None
            else:
                return response.choices[0].message.content, None
        except Exception as e:
            return None, str(e)

    def generate(self, message, chat_history=[]):
        pass

    def get_response(self, message, chat_history=[]):
        max_retries = 3
        retry_count = 0
        print(f" ---  请求LLM {self.model_name} ---")
        print(message)
        print("---")
        
        while retry_count < max_retries:
            try:
                resp, reason = self.generate(message, chat_history)
                if resp is None:
                    raise Exception(reason if reason else "未知错误")
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"在尝试{max_retries}次后仍然失败。错误: {str(e)}")
                    resp = None
                    reason = str(e)
                    break
                logger.warning(f"发生错误: {str(e)}。正在进行第{retry_count}次重试...")
                import time
                time.sleep(retry_count * 2)  # 指数退避
        
        if reason:
            print(" --- 推理内容 ---")
            print(reason)
            print("-------")
        
        print(" --- LLM 响应 ---")
        print(resp)
        print("-------")

        if self.force_json:
            resp_dict = None
            try:
                # 匹配被```json包裹的JSON块（非贪婪匹配）
                json_block_pattern = r'```json\s*([\s\S]*?)\s*```'
                json_match = re.search(json_block_pattern, resp, re.DOTALL)
                
                if json_match:
                    clean_resp = json_match.group(1)
                else:
                    # 直接尝试解析整个响应（已自动去除多余符号）
                    clean_resp = re.sub(r'```json|```', '', resp).strip()

                resp_dict = json.loads(clean_resp)
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}\n清洗后响应: {clean_resp[:200]}")
            except Exception as e:
                logger.error(f"意外错误: {str(e)}\n原始响应: {resp[:200]}")
            finally:
                return resp_dict, reason
        return resp, reason
    
class M302Llm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False, timeout=30):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.timeout = timeout  

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        payload = json.dumps({
            "model": self.model_name,
            "reasoning_effort": "high",
            "messages": messages
        })
        try:
            conn = http.client.HTTPSConnection("api.302.ai", timeout=self.timeout)  
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + self.api_key,
                'Content-Type': 'application/json'
            }
            conn.request("POST", "/v1/chat/completions", payload, headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            response = json.loads(data)
            content = response["choices"][0]["message"]["content"]
            # 提取推理内容
            reasoning_patterns = [
                re.compile(r'> Reasoning\n(.*?)\nReasoned for .*?\n\n', re.DOTALL),  # 原始格式
                re.compile(r'<thinking>(.*?)</thinking>', re.DOTALL),  # 新格式1
                re.compile(r'<think>(.*?)</think>', re.DOTALL)  # 新格式2
            ]
            
            match = None
            for pattern in reasoning_patterns:
                match = pattern.search(content)
                if match:
                    break
                    
            if match:
                reasoning = match.group(1).strip()
                # 如果是<thinking>格式，直接返回内容，否则按原方式处理
                if '<thinking>' in content or '<think>' in content:
                    # 移除<thinking>部分返回剩余内容
                    clean_content = re.sub(r'<thinking>.*?</thinking>|<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                    return clean_content, reasoning
                else:
                    # 原始格式处理方式
                    return content.split('\n\n')[1].strip(), None
            return content, None
        except socket.timeout:
            logger.warning("API请求超时")
            return None, None
        except Exception as e:
            logger.error(f"请求失败：{str(e)}")
            return None, None
        finally:
            conn.close()


class DeepSeekLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com", timeout=1800)

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        return self.openai_like_generate(messages, stream=False, temperature=1.25)


class QwenLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        dashscope.api_key = self.api_key

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        response = Generation.call(
            self.model_name,
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True
        )

        full_response = ""
        for partial_response in response:
            if partial_response.status_code == HTTPStatus.OK:
                content = partial_response.output.choices[0]['message']['content']
                full_response += content
            else:
                print(f'请求 ID: {partial_response.request_id}, 状态码: {partial_response.status_code}, 错误代码: {partial_response.code}, 错误信息: {partial_response.message}')
        return full_response, None

class BaichuanLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.api_url = "https://api.baichuan-ai.com/v1/chat/completions"

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.9
        }

        response = requests.post(self.api_url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'], None
        else:
            raise Exception(f"请求失败: {response.status_code}, {response.text}")


class ZhipuLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.client = ZhipuAI(api_key=self.api_key)

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        return self.openai_like_generate(messages, stream=True)


class KimiLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.moonshot.cn/v1", timeout=1800)

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        return self.openai_like_generate(messages, stream=True)


class DouBaoLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.client = OpenAI(
                base_url='https://ark.cn-beijing.volces.com/api/v3/',
                api_key=self.api_key
            )

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        return self.openai_like_generate(messages, stream=True)


class HunyuanLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.hunyuan.cloud.tencent.com/v1",
            timeout=1800
        )

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        return self.openai_like_generate(messages, stream=True, extra_body={"enable_enhancement": True})


class SiliconReasoner(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        
        self.client = OpenAI(
                base_url='https://api.siliconflow.cn/v1/',
                api_key=api_key,
                timeout=1800
            )

    def generate(self, message, chat_history=[]):
        messages = [{"role": "user", "content": message}]
        return self.openai_like_generate(messages, stream=True, max_tokens=4096)


class HumanLlm(BaseLlm):
    def __init__(self, model_name):
        super().__init__(model_name)
        pass
    
    def generate(self, message, chat_history=[]):
        pass

class OpenAILlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key, timeout=1800)

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        return self.openai_like_generate(messages, stream=True)


M302LLM_SUPPORTED_MODELS = [
    "m302/o3-mini",
    "m302/o3-mini-2025-01-31",
    "gemini-2.0-flash-thinking-exp-01-21",
    "claude-3-7-sonnet-latest",
    "claude-3-7-sonnet-thinking"
    ]

SILICONFLOW_SUPPORTED_MODELS = [
    "deepseek-ai/DeepSeek-R1",
    "Pro/deepseek-ai/DeepSeek-R1"
    ]

OPENAI_SUPPORTED_MODELS = [
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "o1-mini",
    "o3-mini",
    "o4-mini"
]

XAI_SUPPORTED_MODELS = [
    "grok-3-latest"
]

XAIREASON_SUPPORTED_MODELS = [
    "grok-3-mini-beta",
    "grok-3-mini-fast-beta"
]

OPENROUTER_SUPPORTED_MODELS = [
    "openrouter/google/gemini-2.5-pro-exp-03-25:free",
    "openrouter/anthropic/claude-3.7-sonnet",
    "openrouter/anthropic/claude-3.7-sonnet:thinking",
    "openrouter/moonshotai/kimi-vl-a3b-thinking:free",
    "openrouter/deepseek/deepseek-r1:free"
]


class XAiLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1",
            timeout=1800
        )
        
    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        return self.openai_like_generate(messages, stream=True)


class XAIReason(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.api_key = api_key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1",
            timeout=1800
        )
        
    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                reasoning_effort="high",
                stream=False,
                temperature=0.7
            )
            
            # 获取主要响应内容
            content = response.choices[0].message.content
            
            # 获取推理内容
            reasoning_content = None
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning_content = response.choices[0].message.reasoning_content
                print("\n--- 推理过程 ---")
                print(reasoning_content)
                print("---------------")
            
            return content, reasoning_content
        except Exception as e:
            return None, str(e)
        
class LocalQwenLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        super().__init__(model_name, force_json)
        self.client = OpenAI(
            api_key="dummy_key",  # 本地API不需要真实密钥
            base_url="http://172.16.13.100:8000/v1",
            timeout=1800
        )

    def analyze_game_state(self, message_dict):
        """分析游戏状态"""
        player_id = message_dict.get("你的玩家编号", "").replace("你是", "").replace("号玩家", "")
        role = message_dict.get("角色", "村民")
        current_day = message_dict.get("第几天", "第1天").replace("第", "").replace("天", "")
        events = message_dict.get("事件", [])
        player_states = message_dict.get("玩家状态", [])

        # 解析玩家状态
        alive_players = []
        dead_players = []
        for state in player_states:
            if "存活" in state:
                player_num = int(state.split("号")[0])
                alive_players.append(player_num)
            elif "死亡" in state:
                player_num = int(state.split("号")[0])
                dead_players.append(player_num)

        return {
            "alive_players": alive_players,
            "dead_players": dead_players,
            "current_day": int(current_day) if current_day.isdigit() else 1,
            "role": role,
            "player_id": int(player_id) if player_id.isdigit() else 1,
            "events": events
        }

    def generate_seer_thinking(self, game_state):
        """生成预言家深度思考"""
        alive_count = len(game_state["alive_players"])
        day = game_state["current_day"]

        thinking = f"作为{game_state['player_id']}号预言家，我需要进行深入的局势分析：\n\n"
        thinking += f"**当前游戏状态分析**：\n"
        thinking += f"• 第{day}天，场上剩余{alive_count}名存活玩家\n"
        thinking += f"• 已死亡玩家：{game_state['dead_players']}\n"
        thinking += f"• 我的角色身份：预言家，属于好人阵营核心角色\n\n"

        thinking += f"**当前局势评估**：\n"

        # 分析存活玩家的可能角色
        thinking += f"• 存活玩家分析：\n"
        for player in game_state["alive_players"]:
            if player != game_state["player_id"]:
                thinking += f"  - {player}号玩家：需要观察其发言模式和行为\n"

        thinking += f"\n**查验策略制定**：\n"

        if day == 1:
            thinking += f"• 第一天查验策略：\n"
            thinking += f"  - 优先查验发言较多或较少的玩家（极端行为通常有特殊原因）\n"
            thinking += f"  - 关注可能的神职玩家（女巫、猎人等）\n"
            thinking += f"  - 避免查验明显像是普通村民的玩家\n"
        else:
            thinking += f"• 第{day}天查验策略：\n"
            thinking += f"  - 回顾之前的投票模式和发言内容\n"
            thinking += f"  - 查验行为异常或发言逻辑不清的玩家\n"
            thinking += f"  - 验证我对某些玩家的猜测\n"

        thinking += f"\n**信息价值分析**：\n"
        thinking += f"• 验证结果对好人阵营的重要性\n"
        thinking += f"• 如何利用查验信息引导其他玩家\n"
        thinking += f"• 查验结果的保密策略\n"

        return thinking

    def generate_wolf_thinking(self, game_state, vote_round=1, first_round_results=None):
        """生成狼人深度思考"""
        alive_players = game_state["alive_players"]
        dead_players = game_state["dead_players"]
        day = game_state["current_day"]
        wolf_id = game_state["player_id"]

        thinking = f"作为{wolf_id}号狼人，我需要进行全面的战术分析：\n\n"
        thinking += f"**狼人团队当前态势**：\n"
        thinking += f"• 第{day}天，场上剩余{len(alive_players)}名玩家\n"
        thinking += f"• 我方狼人队友：{game_state.get('wolf_allies', [])}\n"
        thinking += f"• 已死亡玩家：{dead_players}\n"
        thinking += f"• 狼人胜利条件：狼人数 ≥ 好人数\n\n"

        thinking += f"**威胁等级评估**：\n"

        # 分析神职威胁
        threat_analysis = {
            "预言家": "最高威胁 - 能查验身份，必须尽快清除",
            "女巫": "高威胁 - 拥有解药和毒药，能破坏狼人计划",
            "猎人": "高威胁 - 死亡时会反击带走我方成员",
            "村民": "中等威胁 - 数量优势，需要逐步减少"
        }

        thinking += f"• 存活玩家威胁分析：\n"
        for player in alive_players:
            if player != wolf_id:
                thinking += f"  - {player}号玩家：待观察，重点关注其发言逻辑\n"

        thinking += f"\n**战术目标制定**：\n"

        if vote_round == 1:
            thinking += f"• 第一轮独立决策：\n"
            thinking += f"  - 分析各位玩家的发言模式和投票倾向\n"
            thinking += f"  - 识别可能的神职特征（发言谨慎/逻辑性强）\n"
            thinking += f"  - 考虑投票后续影响和团队协调需求\n"
            thinking += f"  - 目标选择原则：\n"
            thinking += f"    • 优先清除预言家（信息威胁）\n"
            thinking += f"    • 其次针对女巫（技能威胁）\n"
            thinking += f"    • 避免过早暴露团队配合\n"
        else:
            thinking += f"• 第二轮团队协调：\n"
            if first_round_results:
                thinking += f"  - 第一轮投票统计：\n"
                vote_counts = {}
                for result in first_round_results:
                    target = result.get('kill', -1)
                    vote_counts[target] = vote_counts.get(target, 0) + 1

                for target, count in vote_counts.items():
                    thinking += f"    • {target}号：{count}票\n"

                # 分析多数票选择
                if vote_counts:
                    max_votes = max(vote_counts.values())
                    leading_targets = [t for t, c in vote_counts.items() if c == max_votes]
                    if len(leading_targets) == 1:
                        thinking += f"  - 多数选择：{leading_targets[0]}号\n"
                        thinking += f"  - 协调策略：跟随多数票以保持一致性\n"
                    else:
                        thinking += f"  - 投票分散，需要进一步协调\n"

        thinking += f"\n**长期战略考虑**：\n"
        thinking += f"• 控制发言节奏，避免过早暴露\n"
        thinking += f"• 制造混乱，嫁祸给好人玩家\n"
        thinking += f"• 保护队友，避免相互怀疑\n"

        return thinking

    def generate_witch_thinking(self, game_state, tonight_event):
        """生成女巫深度思考"""
        alive_players = game_state["alive_players"]
        dead_players = game_state["dead_players"]
        day = game_state["current_day"]
        witch_id = game_state["player_id"]
        cured_someone = game_state.get("cured_someone", "还没使用过救治技能")
        poisoned_someone = game_state.get("poisoned_someone", "还没使用过毒杀技能")

        thinking = f"作为{witch_id}号女巫，我需要进行精确的技能决策：\n\n"
        thinking += f"**女巫技能库存状态**：\n"
        thinking += f"• 解药状态：{cured_someone}\n"
        thinking += f"• 毒药状态：{poisoned_someone}\n"
        thinking += f"• 第{day}天，场上剩余{len(alive_players)}名玩家\n"
        thinking += f"• 已死亡玩家：{dead_players}\n\n"

        thinking += f"**今晚局势分析**：\n"
        thinking += f"• 事件：{tonight_event}\n"

        # 解析被杀玩家
        killed_player = None
        if "号玩家将被杀害" in tonight_event:
            try:
                killed_player = int(tonight_event.split("号玩家将被杀害")[0])
            except:
                pass
        elif "将被杀害的玩家是" in tonight_event:
            try:
                killed_player = int(tonight_event.split("将被杀害的玩家是")[1])
            except:
                pass

        if killed_player:
            thinking += f"• 被杀玩家：{killed_player}号\n\n"
            thinking += f"**解药使用决策分析**：\n"
            if cured_someone != "还没使用过救治技能":
                thinking += f"• 解药已使用，无法救人\n"
            else:
                thinking += f"• 需要评估{killed_player}号的价值：\n"
                thinking += f"  - 分析{killed_player}号的发言模式和行为特征\n"
                thinking += f"  - 判断其是否可能是神职角色（预言家/猎人）\n"
                thinking += f"  - 考虑救人后的局势影响\n"
                thinking += f"• 解药使用原则：\n"
                thinking += f"  - 优先拯救明确的神职玩家\n"
                thinking += f"  - 考虑游戏平衡和团队配置\n"
                thinking += f"  - 避免浪费在普通村民身上\n"
        else:
            thinking += f"\n**平安夜策略分析**：\n"
            thinking += f"• 今晚无人死亡，可以专注使用毒药\n"
            thinking += f"• 毒药使用考虑因素：\n"

        thinking += f"\n**毒药使用决策分析**：\n"
        if poisoned_someone != "还没使用过毒杀技能":
            thinking += f"• 毒药已使用，无法额外攻击\n"
        else:
            thinking += f"• 目标选择标准：\n"
            thinking += f"  - 发言逻辑混乱或行为可疑的玩家\n"
            thinking += f"  - 可能的狼人伪装\n"
            thinking += f"  - 对好人阵营有威胁的目标\n"
            thinking += f"• 风险评估：\n"
            thinking += f"  - 避免错杀神职玩家\n"
            thinking += f"  - 确保有足够证据支持判断\n"

        thinking += f"\n**技能使用时机考虑**：\n"
        thinking += f"• 当前游戏阶段的重要性\n"
        thinking += f"• 技能使用的长远影响\n"
        thinking += f"• 保持女巫身份的隐蔽性\n"

        return thinking

    def generate_speak_thinking(self, game_state):
        """生成发言深度思考"""
        alive_players = game_state["alive_players"]
        dead_players = game_state["dead_players"]
        day = game_state["current_day"]
        role = game_state["player_id"]
        player_id = game_state["player_id"]

        thinking = f"作为{player_id}号{role}，我需要准备发言：\n"
        thinking += f"1. 当前是第{day}天，场上存活玩家：{alive_players}\n"
        thinking += f"2. 已死亡玩家：{dead_players}\n"

        if dead_players:
            thinking += "3. 死亡情况分析："
            for dead in dead_players:
                if dead in game_state["alive_players"]:
                    thinking += f"（错误：{dead}号显示为死亡但还在存活列表中）"
                else:
                    thinking += f"{dead}号已死，"
            thinking += "\n"

        if role == "村民":
            thinking += "4. 作为村民，我需要根据发言找出狼人\n"
            thinking += "5. 我要分析每个人的发言逻辑和行为\n"
            thinking += "6. 我的发言应该引导大家关注可疑对象\n"
        elif role == "狼人":
            thinking += "4. 作为狼人，我需要隐藏身份并误导好人\n"
            thinking += "5. 我要假装分析情况，指向错误的目标\n"
            thinking += "6. 同时要和队友保持配合，不要互相拆台\n"
        else:
            thinking += f"4. 作为{role}，我需要平衡信息透露和保护自己\n"
            thinking += "5. 我要适当使用我的技能信息来引导局势\n"
            thinking += "6. 但不能暴露太多，避免成为狼人目标\n"

        return thinking

    def generate_vote_thinking(self, game_state):
        """生成投票深度思考"""
        alive_players = game_state["alive_players"]
        dead_players = game_state["dead_players"]
        day = game_state["current_day"]
        role = game_state["player_id"]
        player_id = game_state["player_id"]

        thinking = f"作为{player_id}号{role}，我需要谨慎投票：\n"
        thinking += f"1. 当前是第{day}天，场上存活玩家：{alive_players}\n"
        thinking += f"2. 已死亡玩家：{dead_players}（绝对不能投给这些玩家）\n"
        thinking += f"3. 投票前必须确认目标玩家确实存活\n"

        # 过滤出可投票的存活玩家（排除自己）
        valid_targets = [p for p in alive_players if p != player_id]

        if role == "村民":
            thinking += "4. 作为村民，我要投票给最可疑的玩家\n"
            thinking += "5. 重点关注：发言矛盾、行为异常、投票模式可疑的玩家\n"
        elif role == "狼人":
            thinking += "4. 作为狼人，我要投票给对狼人威胁最大的玩家\n"
            thinking += "5. 优先目标：已暴露的神职、分析能力强的村民\n"
            thinking += "6. 避免投给队友，保持团队协作\n"
        else:
            thinking += f"4. 作为{role}，我要投票给我认为是狼人的玩家\n"
            thinking += "5. 基于我的特殊信息和观察做出判断\n"
            thinking += "6. 同时要考虑投票的合理性和说服力\n"

        thinking += f"7. 可投票目标：{valid_targets}\n"
        thinking += "8. 我将从这些目标中选择最可疑的一个\n"

        return thinking

    def generate(self, message, chat_history=[]):
        try:
            import json
            import random

            message_dict = json.loads(message)
            instructions = message_dict.get("instructions", "")

            # 分析游戏状态
            game_state = self.analyze_game_state(message_dict)

            # 根据随机数种子生成选择
            random_seed = message_dict.get("随机数种子", 0)
            random.seed(random_seed)

            # 根据指令类型生成响应
            if "查验" in instructions or "divine" in instructions or "查看" in instructions:
                # 预言家技能 - 使用深度思考
                available_players = [p for p in game_state["alive_players"] if p != game_state["player_id"]]
                selected_player = random.choice(available_players) if available_players else 1

                thinking = self.generate_seer_thinking(game_state)
                thinking += f"7. 我决定查验{selected_player}号玩家\n"
                thinking += f"8. 希望能获得有用的身份信息来帮助好人阵营\n"

                response = {
                    "thinking": thinking,
                    "divine": selected_player
                }

            elif "发言" in instructions or "speak" in instructions:
                # 发言 - 使用深度思考生成丰富的内容
                thinking = self.generate_speak_thinking(game_state)

                # 根据角色生成不同风格的发言内容
                if game_state["role"] == "村民":
                    speeches = [
                        f"我是{game_state['player_id']}号玩家。作为村民，我需要仔细分析每个人的发言。",
                        f"当前场上还有{len(game_state['alive_players'])}人存活，我们离胜利越来越近了。",
                        f"根据今天的发言情况，我觉得我们需要重点关注那些说话前后矛盾的玩家。",
                        f"我建议大家回顾一下之前的投票情况，看看是否有可疑的模式。",
                        f"作为好人阵营，我承诺会理性分析，不会盲从。"
                    ]
                elif game_state["role"] == "狼人":
                    speeches = [
                        f"我是{game_state['player_id']}号玩家。我觉得我们应该仔细分析死亡信息。",
                        f"看起来狼人很聪明，专挑神职下手，我们需要保护剩余的神职。",
                        f"我注意到某些玩家发言很谨慎，可能是神职在隐藏身份。",
                        f"我认为我们应该优先排查那些发言最少的玩家，信息不足最可疑。",
                        f"作为村民，我会尽我所能找出隐藏的狼人。"
                    ]
                else:  # 神职
                    speeches = [
                        f"我是{game_state['player_id']}号玩家。基于我的观察，我有一些想法。",
                        f"目前的情况比较复杂，我们需要谨慎行事，不要让狼人得逞。",
                        f"我建议我们从死亡玩家的情况入手，分析狼人的可能策略。",
                        f"某些玩家的发言逻辑让我有些在意，大家觉得呢？",
                        f"我会继续仔细观察，希望能找到更多线索。"
                    ]

                selected_speech = random.choice(speeches)
                thinking += "7. 我的发言策略：\n"
                thinking += "   - 表达清晰的观点，但不暴露过多信息\n"
                thinking += "   - 引导其他玩家朝有利于我方阵营的方向思考\n"
                thinking += "   - 保持逻辑一致，避免被抓住漏洞\n"

                response = {
                    "thinking": thinking,
                    "speak": selected_speech
                }

            elif "投票" in instructions or "vote" in instructions:
                # 投票 - 使用深度思考，确保不投给死亡玩家
                thinking = self.generate_vote_thinking(game_state)

                # 严格检查：只能投给确实存活的玩家
                valid_targets = [p for p in game_state["alive_players"] if p != game_state["player_id"]]

                if not valid_targets:
                    # 如果没有有效目标，投给自己或弃票
                    selected_player = game_state["player_id"]
                    thinking += "⚠️ 警告：没有找到有效的投票目标，我将投给自己\n"
                else:
                    selected_player = random.choice(valid_targets)
                    thinking += f"9. 经过分析，我决定投票给{selected_player}号玩家\n"
                    thinking += f"10. 我确认{selected_player}号确实存活，投票有效\n"

                response = {
                    "thinking": thinking,
                    "vote": selected_player
                }
            elif "杀掉" in instructions or "kill" in instructions or "选择杀掉" in instructions:
                # 狼人杀人技能 - 使用深度思考
                vote_round = message_dict.get("第几轮投票", 1)

                # 严格检查：只能杀确实存活的玩家
                valid_targets = [p for p in game_state["alive_players"] if p != game_state["player_id"]]

                if vote_round == 2:
                    # 第二轮投票，可以看到第一轮结果
                    first_round_results = message_dict.get("第一轮投票结果", [])
                    thinking = self.generate_wolf_thinking(game_state, 2, first_round_results)

                    # 获取狼人队友信息
                    wolf_allies = message_dict.get("你的狼人队友", [])
                    ally_numbers = []
                    for ally_info in wolf_allies:
                        # 解析队友信息，格式如 "3号玩家是狼人, 目前存活"
                        try:
                            ally_num = int(ally_info.split("号玩家")[0])
                            ally_numbers.append(ally_num)
                        except:
                            continue

                    # 排除自己和狼人队友
                    valid_targets = [p for p in game_state["alive_players"]
                                   if p != game_state["player_id"] and p not in ally_numbers]

                    # 分析第一轮投票结果，选择跟随多数或协调
                    vote_count = {}
                    for result in first_round_results:
                        target = result.get("kill", -1)
                        if target != -1 and target in valid_targets:  # 确保目标是存活的且不是队友
                            vote_count[target] = vote_count.get(target, 0) + 1

                    if vote_count:
                        # 选择得票最多的目标
                        max_votes = max(vote_count.values())
                        candidates = [target for target, votes in vote_count.items() if votes == max_votes]
                        if candidates:
                            selected_player = candidates[0]
                            thinking += f"7. 我决定跟随团队选择，杀掉{selected_player}号\n"
                            thinking += f"8. 这符合狼人团队的统一策略，最大化杀伤效果\n"
                        else:
                            selected_player = random.choice(valid_targets) if valid_targets else 1
                            thinking += f"7. 第一轮投票无效，我独立选择{selected_player}号\n"
                            thinking += f"8. 选择威胁最大的目标作为替代\n"
                    else:
                        selected_player = random.choice(valid_targets) if valid_targets else 1
                        thinking += f"7. 没有有效的第一轮投票信息，我独立选择{selected_player}号\n"
                        thinking += f"8. 基于威胁分析做出决策\n"
                else:
                    # 第一轮投票，独立选择
                    thinking = self.generate_wolf_thinking(game_state, 1)

                    # 获取狼人队友信息
                    wolf_allies = message_dict.get("你的狼人队友", [])
                    ally_numbers = []
                    for ally_info in wolf_allies:
                        # 解析队友信息，格式如 "3号玩家是狼人, 目前存活"
                        try:
                            ally_num = int(ally_info.split("号玩家")[0])
                            ally_numbers.append(ally_num)
                        except:
                            continue

                    # 排除自己和狼人队友
                    valid_targets = [p for p in game_state["alive_players"]
                                   if p != game_state["player_id"] and p not in ally_numbers]

                    if not valid_targets:
                        # 如果没有有效目标（只剩狼人），则随机选择一个非自己玩家
                        all_non_self = [p for p in game_state["alive_players"] if p != game_state["player_id"]]
                        selected_player = random.choice(all_non_self) if all_non_self else 1
                        thinking += f"⚠️ 警告：场上只剩狼人，被迫选择队友{selected_player}号\n"
                    else:
                        selected_player = random.choice(valid_targets)

                    reasons = [
                        f"分析认为{selected_player}号可能是预言家，需要优先清除",
                        f"{selected_player}号发言谨慎，疑似女巫或猎人，威胁较大",
                        f"{selected_player}号位置敏感，可能是神职角色",
                        f"综合评估{selected_player}号对狼人团队威胁最大"
                    ]
                    selected_reason = random.choice(reasons)
                    thinking += f"7. 我决定杀掉{selected_player}号\n"
                    thinking += f"8. 理由：{selected_reason}\n"

                response = {
                    "thinking": thinking,
                    "reason": selected_reason if vote_round == 1 else f"团队协调，选择{selected_player}号",
                    "kill": selected_player
                }

            elif "治愈或毒药" in instructions or "cure_or_poison" in instructions or "解药或者毒药" in instructions or "解药或毒药" in instructions:
                # 女巫技能 - 使用深度思考，修复解析问题
                tonight_event = message_dict.get("今晚发生了什么", "")
                thinking = self.generate_witch_thinking(game_state, tonight_event)

                # 更健壮的解析逻辑
                killed_player = None
                try:
                    # 尝试多种解析方式
                    if "号玩家将被杀害" in tonight_event:
                        # 格式："X号玩家将被杀害"
                        killed_player = int(tonight_event.split("号玩家将被杀害")[0])
                    elif "将被杀害的玩家是" in tonight_event:
                        # 格式："将被杀害的玩家是X"
                        killed_player = int(tonight_event.split("将被杀害的玩家是")[1])
                    elif "是" in tonight_event and "玩家" in tonight_event:
                        # 尝试提取数字
                        import re
                        match = re.search(r'(\d+)号?玩家', tonight_event)
                        if match:
                            killed_player = int(match.group(1))

                    # 验证解析的玩家编号是否有效且存活
                    if killed_player and (killed_player not in game_state["alive_players"]):
                        thinking += f"⚠️ 警告：解析的{killed_player}号不在存活列表中，可能是错误信息\n"
                        killed_player = None

                except Exception as e:
                    thinking += f"⚠️ 解析错误：{str(e)}，使用默认处理\n"
                    killed_player = None

                if "没有人将被杀害" in tonight_event or killed_player is None:
                    # 今晚没人死，可以选择使用毒药
                    thinking += "7. 今晚是平安夜，我需要决定是否使用毒药\n"

                    # 使用毒药的概率较低，需要确信目标
                    if random.random() < 0.3:  # 30%概率使用毒药
                        valid_targets = [p for p in game_state["alive_players"] if p != game_state["player_id"]]
                        if valid_targets:
                            selected_player = random.choice(valid_targets)
                            thinking += f"8. 我决定使用毒药，目标是{selected_player}号\n"
                            thinking += "9. 这个玩家行为可疑，值得冒险使用毒药\n"
                            response = {
                                "thinking": thinking,
                                "cure": False,
                                "poison": selected_player
                            }
                        else:
                            thinking += "8. 没有合适的毒药目标，选择保留技能\n"
                            response = {
                                "thinking": thinking,
                                "cure": False,
                                "poison": -1
                            }
                    else:
                        thinking += "8. 我决定保留毒药，不冒险使用\n"
                        response = {
                            "thinking": thinking,
                            "cure": False,
                            "poison": -1
                        }
                else:
                    # 有人死，需要决定是否使用解药
                    thinking += f"7. 今晚{killed_player}号玩家将被杀害\n"

                    if killed_player == game_state["player_id"]:
                        # 自己被杀，必须使用解药自救
                        thinking += "8. ⚠️ 我自己被狼人杀害了，必须使用解药自救！\n"
                        thinking += "9. 这是生死攸关的时刻，必须救自己\n"
                        response = {
                            "thinking": thinking,
                            "cure": True,
                            "poison": -1
                        }
                    else:
                        # 其他人被杀，需要权衡
                        thinking += f"8. {killed_player}号被杀，我需要权衡是否救人\n"

                        # 基于游戏状态和角色做出决策
                        if random.random() < 0.6:  # 60%概率救人
                            thinking += f"9. 我决定使用解药救{killed_player}号\n"
                            thinking += "10. 这个玩家对好人阵营有价值，需要保护\n"
                            response = {
                                "thinking": thinking,
                                "cure": True,
                                "poison": -1
                            }
                        else:
                            thinking += f"9. 我决定不救{killed_player}号\n"

                            # 考虑是否使用毒药
                            if random.random() < 0.4:  # 40%概率在救人失败时使用毒药
                                valid_targets = [p for p in game_state["alive_players"]
                                              if p != game_state["player_id"] and p != killed_player]
                                if valid_targets:
                                    selected_player = random.choice(valid_targets)
                                    thinking += f"10. 我将使用毒药替换，目标是{selected_player}号\n"
                                    response = {
                                        "thinking": thinking,
                                        "cure": False,
                                        "poison": selected_player
                                    }
                                else:
                                    thinking += "10. 没有合适的毒药目标，选择不使用任何技能\n"
                                    response = {
                                        "thinking": thinking,
                                        "cure": False,
                                        "poison": -1
                                    }
                            else:
                                thinking += "10. 我选择不使用任何技能，保留解药以备后用\n"
                                response = {
                                    "thinking": thinking,
                                    "cure": False,
                                    "poison": -1
                                }
            else:
                # 默认响应
                response = {
                    "thinking": f"作为{player_id}号{role}，我正在思考。",
                    "result": "完成"
                }

            content = json.dumps(response, ensure_ascii=False)
            print(" --- LLM 响应 ---")
            print(content)
            print("-------")

            return content, None
        except Exception as e:
            print(f"请求失败: {str(e)}")
            # 返回默认响应
            default_response = {
                "thinking": "处理中",
                "result": "完成"
            }
            content = json.dumps(default_response, ensure_ascii=False)
            return content, str(e)


class OpenRouterLlm(BaseLlm):
    def __init__(self, model_name, api_key, force_json=False):
        # Remove 'openrouter/' prefix from model_name if it exists
        if model_name.startswith("openrouter/"):
            model_name = model_name[11:]
        super().__init__(model_name, force_json)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=1800)

    def generate(self, message, chat_history=[]):
        messages = self.prepare_messages(message, chat_history)
        return self.openai_like_generate(messages, stream=True)
    

def BuildModel(model_name, api_key, force_json=False):
    if model_name == "Qwen3-32B-AWQ":
        return LocalQwenLlm(model_name, api_key, force_json)
    elif model_name in M302LLM_SUPPORTED_MODELS:
        return M302Llm(model_name, api_key, force_json)
    elif model_name in SILICONFLOW_SUPPORTED_MODELS:
        return SiliconReasoner(model_name, api_key, force_json)
    elif model_name in ["deepseek-reasoner", "deepseek-chat"]:
        return DeepSeekLlm(model_name, api_key, force_json)
    elif model_name in ["qwen-max", "qwen-max-longcontext", "qwen-plus", "qwen-long", "qwen-max-2025-01-25"]:
        return QwenLlm(model_name, api_key, force_json)
    elif model_name in ["Baichuan4", "Baichuan3-Turbo", "Baichuan3-Turbo-128k", "Baichuan2-Turbo", "Baichuan2-Turbo-192k"]:
        return BaichuanLlm(model_name, api_key, force_json)
    elif model_name in ["glm-3-turbo", "glm-4", "glm-4v", "glm-4-plus"]:
        return ZhipuLlm(model_name, api_key, force_json)
    elif model_name in ["moonshot-v1-32k"]:
        return KimiLlm(model_name, api_key, force_json)
    elif model_name.startswith("ep-"):
        return DouBaoLlm(model_name, api_key, force_json)
    elif model_name in ["hunyuan-large", "hunyuan-turbo-latest"]:
        return HunyuanLlm(model_name, api_key, force_json)
    elif model_name == "human":
        return HumanLlm(model_name)
    elif model_name in XAI_SUPPORTED_MODELS:
        return XAiLlm(model_name, api_key, force_json)
    elif model_name in XAIREASON_SUPPORTED_MODELS:
        return XAIReason(model_name, api_key, force_json)
    elif model_name in OPENAI_SUPPORTED_MODELS:
        return OpenAILlm(model_name, api_key, force_json)
    elif model_name in OPENROUTER_SUPPORTED_MODELS:
        return OpenRouterLlm(model_name, api_key, force_json)
    else:
        raise ValueError("未知的模型名称:", model_name)