from datetime import datetime
import time

class Event:
    def __init__(self, event_type, player_idx, timestamp=None):
        self.event_type = event_type  # 事件类型
        self.player_idx = player_idx
        self.is_public = True  # 是否公开事件
        self.timestamp = timestamp if timestamp else time.time()  # 添加时间戳
        self.game_data = {}  # 存储详细的回放数据

    def desc(self)->str:
        pass

    def set_replay_data(self, **kwargs):
        """设置回放所需的数据"""
        self.game_data.update(kwargs)


class SpeakEvent(Event):
    def __init__(self, player_idx, description):
        super().__init__("speak", player_idx)
        self.description = description

    def desc(self)->str:
        return f'【{self.player_idx}号玩家】发言: "{self.description})"'


class VoteEvent(Event):
    def __init__(self, player_idx, target_idx):
        super().__init__("vote", player_idx)
        self.target_idx = target_idx
        self.is_public = False

    def desc(self)->str:
        if self.target_idx == -1:
            return f'【{self.player_idx}号玩家】在投票环节弃票'
        return f'【{self.player_idx}号玩家】投票给: 【{self.target_idx}号玩家】'

class ExecuteEvent(Event):
    def __init__(self, player_idx,  vote_result):
        super().__init__("execute", player_idx)
        self.vote_result = []
        for vote in vote_result:
            vote_id = vote["vote_id"]
            if vote_id == -1:
                self.vote_result.append(f'【{vote["player_idx"]}号玩家】弃票.')
            else:
                self.vote_result.append(f'【{vote["player_idx"]}号玩家】 投票给 {vote["vote_id"]}号玩家.')
        
    def desc(self)->str:
        desc_str = '白天投票结果:'
        for vote in self.vote_result:
            desc_str += f'{vote} '
        desc_str += f'【{self.player_idx}号玩家】被处决.'
        return desc_str

class AttackEvent(Event):
    def __init__(self, player_idx):
        super().__init__("attack", player_idx)

    def desc(self)->str:
        return f'【{self.player_idx}号玩家】被猎人反击杀死'

class LastWordEvent(Event):
    def __init__(self, player_idx, description):
        super().__init__("last_word", player_idx)
        self.description = description
    def desc(self)->str:
        return f'【{self.player_idx}号玩家】最后发言: "{self.description}"'

class KillEvent(Event):
    def __init__(self, player_idx):
        super().__init__("kill", player_idx)

    def desc(self)->str:
        return f'【{self.player_idx}号玩家】被杀死'

class CureEvent(Event):
    def __init__(self, player_idx):
        super().__init__("cure", player_idx)
        self.is_public = False

    def desc(self)->str:
        return f'{self.player_idx}号玩家】被女巫救治'

class PoisonEvent(Event):
    def __init__(self, player_idx):
        super().__init__("poison", player_idx)
        self.is_public = False

    def desc(self)->str:
        return f'【{self.player_idx}号玩家】被投毒'

# 新增回放专用事件类型
class DivineEvent(Event):
    def __init__(self, player_idx, target_idx, result):
        super().__init__("divine", player_idx)
        self.target_idx = target_idx
        self.result = result  # "狼人" 或 "好人"
        self.is_public = False

    def desc(self)->str:
        return f'【{self.player_idx}号预言家】查验了【{self.target_idx}号】玩家，结果是【{self.result}】'

class WolfKillEvent(Event):
    def __init__(self, player_idx, target_idx, reason, round_num=1):
        super().__init__("wolf_kill", player_idx)
        self.target_idx = target_idx
        self.reason = reason
        self.round_num = round_num
        self.is_public = False

    def desc(self)->str:
        return f'【{self.player_idx}号狼人】第{self.round_num}轮投票选择杀【{self.target_idx}号】，理由：{self.reason}'

class WitchDecisionEvent(Event):
    def __init__(self, player_idx, cure_target, poison_target, thinking):
        super().__init__("witch_decision", player_idx)
        self.cure_target = cure_target
        self.poison_target = poison_target
        self.thinking = thinking
        self.is_public = False

    def desc(self)->str:
        desc = f'【{self.player_idx}号女巫】决策：'
        if self.cure_target != -1:
            desc += f'救【{self.cure_target}号】'
        if self.poison_target != -1:
            desc += f'毒【{self.poison_target}号】'
        if self.cure_target == -1 and self.poison_target == -1:
            desc += '不使用技能'
        return desc

class GameStartEvent(Event):
    def __init__(self, players_config):
        super().__init__("game_start", -1)
        self.players_config = players_config
        self.is_public = True

    def desc(self)->str:
        return "游戏开始"

class DayChangeEvent(Event):
    def __init__(self, day_num, is_daytime):
        super().__init__("day_change", -1)
        self.day_num = day_num
        self.is_daytime = is_daytime
        self.is_public = True

    def desc(self)->str:
        time_str = "白天" if self.is_daytime else "夜晚"
        return f"第{self.day_num}天{time_str}开始"

class Round:
    def __init__(self, day_count):
        self.day_count = day_count
        self.day_events = []
        self.night_events = []

    def get_events(self, show_all = False):
        events = {
            "时间": f"第{self.day_count+1}天",
            "白天事件": [],
            "夜晚事件": []
        }
        for event in self.day_events:
            if show_all:
                events["白天事件"].append(event.desc())
            else:
                if event.is_public:
                    events["白天事件"].append(event.desc())
        for event in self.night_events:
            if show_all:
                events["夜晚事件"].append(event.desc())
            else:
                if event.is_public:
                    events["夜晚事件"].append(event.desc())
        if self.day_count == 0:
            events["白天事件"].append("此时游戏还没开始,不会发言和投票事件")
        
        if not events["白天事件"]:
            del events["白天事件"]
        if not events["夜晚事件"]:
            del events["夜晚事件"]
        return events
    
    def add_event(self, is_daytime, event):
        if is_daytime:
            self.day_events.append(event)
        else:
            self.night_events.append(event)

class History:
    def __init__(self):
        self.day_count = 0  # 当前是第几天,从0开始
        self.rounds = []  # 存储所有事件
        self.rounds.append(Round(self.day_count)) #创建第一个回合
        self.is_daytime = False  # 从晚上开始
        self.start_time = time.time()  # 游戏开始时间
        self.is_recording = True  # 是否正在记录

    def dump(self):
        for round in self.rounds:
            print(round.get_events())

    def add_event(self, event):
        if self.is_recording:
            self.rounds[self.day_count].add_event(self.is_daytime, event)

    def get_history(self, show_all = False):
        '''
        构造一个事件列表
        '''
        history = []
        for round in self.rounds:
            history.append(round.get_events(show_all))
        return history

    def toggle_day_night(self):
        self.is_daytime = not self.is_daytime
        if self.is_daytime:
            self.day_count += 1
            #新的一天开始新回合
            self.rounds.append(Round(self.day_count))

    def get_replay_data(self):
        """获取完整的回放数据"""
        replay_events = []

        for round_idx, round in enumerate(self.rounds):
            # 添加昼夜变化事件
            if round.day_count == 0:
                replay_events.append({
                    "type": "game_start",
                    "timestamp": self.start_time,
                    "data": {
                        "day": 1,
                        "phase": "night"
                    }
                })

            # 添加夜晚事件
            for event in round.night_events:
                replay_events.append({
                    "type": event.event_type,
                    "timestamp": event.timestamp,
                    "player_idx": event.player_idx,
                    "data": event.game_data
                })

            # 添加昼夜变化
            if round.day_count > 0:
                replay_events.append({
                    "type": "day_change",
                    "timestamp": event.timestamp if round.night_events else self.start_time + round.day_count * 100,
                    "data": {
                        "day": round.day_count + 1,
                        "phase": "day"
                    }
                })

            # 添加白天事件
            for event in round.day_events:
                replay_events.append({
                    "type": event.event_type,
                    "timestamp": event.timestamp,
                    "player_idx": event.player_idx,
                    "data": event.game_data
                })

        return {
            "events": replay_events,
            "total_duration": time.time() - self.start_time,
            "start_time": self.start_time
        }

    def stop_recording(self):
        """停止记录游戏事件"""
        self.is_recording = False

