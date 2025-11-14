import Game from "./game.js";
import Ui from "./ui.js";
import ReplayController from "./replay.js";
import { sleep } from "./utils.js";

// Asynchronous IIFE
(async () => {
    const ui = new Ui();
    await ui.setup();
    await ui.preload();
    await ui.loadSprites();

    // 创建回放控制器
    const replayController = new ReplayController(ui);

    // 添加全局访问接口，方便调试
    window.replayController = replayController;

    // 在页面加载3秒后显示回放控制器提示
    setTimeout(() => {
        console.log('🎮 游戏回放功能已加载！使用 window.replayController.loadReplayData() 开始回放');
        console.log('可用功能：');
        console.log('- loadReplayData(): 加载回放数据');
        console.log('- togglePlayPause(): 播放/暂停');
        console.log('- setSpeed(speed): 设置播放速度 (0.5x, 1x, 2x, 4x, 8x)');
        console.log('- resetReplay(): 重置回放');
    }, 3000);

    //await ui.showPlayer(1);
    //await ui.showHumanInput("请输入你的名字");

    await ui.showBigText("游戏开始", 1000);
    await ui.showBigText("天黑了，请闭眼", 2000);

    //如果不想显示角色名称，可以传 false
    const game = new Game(ui);
    await game.start();

    let is_end = false;
    while (!is_end) {
        is_end = await game.run();

        // 游戏结束后显示回放控制器
        if (is_end) {
            setTimeout(() => {
                replayController.showReplayControls();
                alert('游戏结束！可以使用右上角的回放控制器回顾游戏过程。\n\n功能说明：\n• 加载回放：获取完整游戏记录\n• 播放控制：播放/暂停/快进/快退\n• 速度调节：0.5x-8x播放速度\n• 进度拖动：跳转到任意时间点');
            }, 2000);
        }
    }
})();
