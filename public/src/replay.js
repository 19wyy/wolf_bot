class ReplayController {
    constructor(ui) {
        this.ui = ui;
        this.isReplaying = false;
        this.isPlaying = false;
        this.currentEventIndex = 0;
        this.playbackSpeed = 1.0;
        this.replayData = null;
        this.baseInterval = 1000; // 基础间隔 1秒
        this.intervalId = null;

        this.replayContainer = null;
        this.playbackControls = this.createPlaybackControls();
    }

    createPlaybackControls() {
        // 创建回放控制界面
        const container = document.createElement('div');
        container.id = 'replay-controls';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 15px;
            border-radius: 10px;
            z-index: 1000;
            min-width: 300px;
            font-family: '钉钉进步体', sans-serif;
            display: none;
        `;

        container.innerHTML = `
            <h3 style="margin: 0 0 15px 0; font-size: 18px;">🎮 游戏回放</h3>

            <div style="margin-bottom: 15px;">
                <button id="replay-load-btn" style="margin-right: 10px; padding: 8px 15px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">加载回放</button>
                <button id="replay-reset-btn" style="padding: 8px 15px; background: #f44336; color: white; border: none; border-radius: 5px; cursor: pointer;">重置</button>
            </div>

            <div style="margin-bottom: 15px;">
                <button id="replay-play-pause-btn" style="margin-right: 10px; padding: 8px 15px; background: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer;">▶️ 播放</button>
                <button id="replay-prev-btn" style="margin-right: 5px; padding: 8px 10px; background: #FF9800; color: white; border: none; border-radius: 5px; cursor: pointer;">⏪</button>
                <button id="replay-next-btn" style="margin-right: 5px; padding: 8px 10px; background: #FF9800; color: white; border: none; border-radius: 5px; cursor: pointer;">⏩</button>
            </div>

            <div style="margin-bottom: 15px;">
                <label style="margin-right: 10px;">播放速度:</label>
                <select id="replay-speed" style="padding: 5px; border-radius: 5px; border: 1px solid #555; background: #333; color: white;">
                    <option value="0.5">0.5x</option>
                    <option value="1" selected>1x</option>
                    <option value="2">2x</option>
                    <option value="4">4x</option>
                    <option value="8">8x</option>
                </select>
            </div>

            <div style="margin-bottom: 15px;">
                <div style="margin-bottom: 5px;">进度: <span id="replay-progress-text">0/0</span></div>
                <input type="range" id="replay-progress" min="0" max="100" value="0" style="width: 100%; cursor: pointer;">
            </div>

            <div>
                <div style="margin-bottom: 5px;">当前事件:</div>
                <div id="replay-current-event" style="font-size: 14px; color: #FFD700; max-height: 100px; overflow-y: auto;">等待加载回放数据...</div>
            </div>
        `;

        // 绑定事件监听器
        container.querySelector('#replay-load-btn').addEventListener('click', () => this.loadReplayData());
        container.querySelector('#replay-reset-btn').addEventListener('click', () => this.resetReplay());
        container.querySelector('#replay-play-pause-btn').addEventListener('click', () => this.togglePlayPause());
        container.querySelector('#replay-prev-btn').addEventListener('click', () => this.previousEvent());
        container.querySelector('#replay-next-btn').addEventListener('click', () => this.nextEvent());
        container.querySelector('#replay-speed').addEventListener('change', (e) => this.setSpeed(parseFloat(e.target.value)));
        container.querySelector('#replay-progress').addEventListener('input', (e) => this.seekTo(parseFloat(e.target.value)));

        document.body.appendChild(container);
        return container;
    }

    showReplayControls() {
        this.playbackControls.style.display = 'block';
    }

    hideReplayControls() {
        this.playbackControls.style.display = 'none';
    }

    async loadReplayData() {
        try {
            const response = await fetch('/replay_data');
            const data = await response.json();

            if (data.error) {
                alert('加载回放数据失败: ' + data.error);
                return;
            }

            this.replayData = data;
            this.currentEventIndex = 0;
            this.updateProgressDisplay();
            this.showReplayControls();

            // 更新进度条最大值
            const progressSlider = document.getElementById('replay-progress');
            progressSlider.max = data.events.length - 1;

            alert(`成功加载回放数据！共 ${data.events.length} 个事件，总时长 ${Math.round(data.total_duration)} 秒`);
        } catch (error) {
            console.error('加载回放数据失败:', error);
            alert('加载回放数据失败: ' + error.message);
        }
    }

    resetReplay() {
        this.isReplaying = false;
        this.isPlaying = false;
        this.currentEventIndex = 0;
        this.replayData = null;

        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }

        this.updateProgressDisplay();
        document.getElementById('replay-current-event').textContent = '等待加载回放数据...';
        document.getElementById('replay-play-pause-btn').textContent = '▶️ 播放';
    }

    togglePlayPause() {
        if (!this.replayData || this.replayData.events.length === 0) {
            alert('请先加载回放数据！');
            return;
        }

        this.isReplaying = true;
        this.isPlaying = !this.isPlaying;

        if (this.isPlaying) {
            this.startPlayback();
            document.getElementById('replay-play-pause-btn').textContent = '⏸ 暂停';
        } else {
            this.pausePlayback();
            document.getElementById('replay-play-pause-btn').textContent = '▶️ 播放';
        }
    }

    startPlayback() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        const interval = this.baseInterval / this.playbackSpeed;
        this.intervalId = setInterval(() => {
            this.playNextEvent();
        }, interval);
    }

    pausePlayback() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    playNextEvent() {
        if (this.currentEventIndex >= this.replayData.events.length - 1) {
            this.pausePlayback();
            this.isPlaying = false;
            document.getElementById('replay-play-pause-btn').textContent = '▶️ 播放';
            alert('回放结束！');
            return;
        }

        this.nextEvent();
    }

    previousEvent() {
        if (!this.replayData || this.replayData.events.length === 0) return;

        if (this.currentEventIndex > 0) {
            this.currentEventIndex--;
            this.executeEvent(this.replayData.events[this.currentEventIndex]);
            this.updateProgressDisplay();
        }
    }

    nextEvent() {
        if (!this.replayData || this.replayData.events.length === 0) return;

        if (this.currentEventIndex < this.replayData.events.length - 1) {
            this.currentEventIndex++;
            this.executeEvent(this.replayData.events[this.currentEventIndex]);
            this.updateProgressDisplay();
        }
    }

    seekTo(progressValue) {
        if (!this.replayData || this.replayData.events.length === 0) return;

        const targetIndex = Math.floor(progressValue);
        if (targetIndex >= 0 && targetIndex < this.replayData.events.length) {
            this.currentEventIndex = targetIndex;
            this.executeEvent(this.replayData.events[this.currentEventIndex]);
            this.updateProgressDisplay();
        }
    }

    setSpeed(speed) {
        this.playbackSpeed = speed;

        // 如果正在播放，重新启动以应用新速度
        if (this.isPlaying) {
            this.pausePlayback();
            this.startPlayback();
        }
    }

    async executeEvent(event) {
        const eventDisplay = document.getElementById('replay-current-event');
        let eventDescription = '';

        switch (event.type) {
            case 'game_start':
                eventDescription = `🎮 游戏开始 - 第${event.data.day}天${event.data.phase === 'night' ? '夜晚' : '白天'}`;
                await this.ui.showDay(event.data.day);
                break;

            case 'day_change':
                eventDescription = `🌅 第${event.data.day}天${event.data.phase === 'night' ? '夜晚' : '白天'}开始`;
                if (event.data.phase === 'day') {
                    await this.ui.showDayBackground();
                } else {
                    await this.ui.showNightBackground();
                }
                break;

            case 'speak':
                eventDescription = `💬 ${event.player_idx}号玩家发言: "${event.data.speak}"`;
                if (event.data.thinking && this.ui.display_thinking) {
                    await this.ui.showPlayer(event.player_idx);
                    await this.ui.speak(`${event.player_idx}号玩家 思考中`, true, event.data.thinking, true);
                    await this.ui.hidePlayer();
                }
                await this.ui.speak(`${event.player_idx}号玩家`, true, event.data.speak);
                break;

            case 'vote':
                eventDescription = `🗳️ ${event.player_idx}号玩家投票给 ${event.data.vote}号`;
                if (event.data.thinking && this.ui.display_thinking) {
                    await this.ui.showPlayer(event.player_idx);
                    await this.ui.speak(`${event.player_idx}号玩家 思考中`, true, event.data.thinking, true);
                    await this.ui.hidePlayer();
                }
                await this.ui.showVote(event.player_idx, event.data.vote);
                break;

            case 'divine':
                eventDescription = `🔮 ${event.player_idx}号预言家查验了${event.data.divine}号玩家`;
                if (event.data.thinking && this.ui.display_thinking) {
                    await this.ui.showPlayer(event.player_idx);
                    await this.ui.speak(`${event.player_idx}号预言家 思考中`, true, event.data.thinking, true);
                    await this.ui.hidePlayer();
                }
                break;

            case 'wolf_kill':
                eventDescription = `🐺 ${event.player_idx}号狼人选择杀${event.data.kill}号玩家`;
                if (event.data.thinking && this.ui.display_thinking) {
                    await this.ui.showPlayer(event.player_idx);
                    await this.ui.speak(`${event.player_idx}号狼人 思考中`, true, event.data.reason, true);
                    await this.ui.hidePlayer();
                }
                break;

            case 'witch_decision':
                eventDescription = `🧪 ${event.player_idx}号女巫决策: `;
                if (event.data.cure !== -1 && event.data.cure !== false) {
                    eventDescription += `救${event.data.cure}号 `;
                }
                if (event.data.poison !== -1) {
                    eventDescription += `毒${event.data.poison}号 `;
                }
                if (event.data.cure === -1 && event.data.poison === -1) {
                    eventDescription += '不使用技能 ';
                }
                if (event.data.thinking && this.ui.display_thinking) {
                    await this.ui.showPlayer(event.player_idx);
                    await this.ui.speak(`${event.player_idx}号女巫 思考中`, true, event.data.thinking, true);
                    await this.ui.hidePlayer();
                }
                break;

            case 'kill':
                eventDescription = `💀 ${event.player_idx}号玩家被杀`;
                await this.ui.killPlayer(event.player_idx);
                break;

            case 'execute':
                eventDescription = `⚖️ ${event.player_idx}号玩家被处决`;
                await this.ui.killPlayer(event.player_idx);
                break;

            default:
                eventDescription = `📝 ${event.type}: 玩家${event.player_idx}`;
        }

        eventDisplay.textContent = eventDescription;
    }

    updateProgressDisplay() {
        if (!this.replayData) return;

        const progressSlider = document.getElementById('replay-progress');
        const progressText = document.getElementById('replay-progress-text');

        progressSlider.value = this.currentEventIndex;
        progressText.textContent = `${this.currentEventIndex + 1}/${this.replayData.events.length}`;
    }
}

export default ReplayController;