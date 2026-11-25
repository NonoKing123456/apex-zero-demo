# APEX ZERO | 零号弯道

> **30 秒 AI 漫剧商用先导 Demo** · 2.5D 唯美韩漫半厚涂 × 3D 半写实国漫 · 都市暗夜重机飙车题材  
> 从 **资产先行（角色 4 视图 / 载具 3 视图 / 核心场景空镜）→ 多图垫底 2K 分镜首帧 → Seedance 2.5 分段节拍图生视频（6/6 零废片）→ 双人 VO 配音 + 纯器乐赛博 BGM → FFmpeg 1080P 60fps 全代码精剪混音** 的端到端工业化 AI 短剧实践。

![APEX ZERO Cover](outputs/keyframes/S05.png)

---

## 🎬 最终成片（1080P · 60fps · 29.2s）

- **主成片下载 / 播放**：[`outputs/APEX_ZERO_零号弯道_30s_FINAL_1080P.mp4`](outputs/APEX_ZERO_零号弯道_30s_FINAL_1080P.mp4)（33.6 MB，`1920×1080`，`60fps`，`48kHz Stereo AAC`）
- **画风定位**：低饱和莫兰迪冷灰蓝 + 珊瑚粉橘点缀 + 逆光空气发丝光晕
- **剪辑亮点**：反派男声 L-Cut 玩梗开场、S03 点火爆灯踩鼓点、S04→S05 高潮 0.8s 嘴角微挑极速闪切、S06 破晓 BGM 骤降凸显引擎熄火余温滴答声、结尾 55Hz 电影低音炮“咚” + 极简珊瑚橘细线片名卡

---

## 🧱 核心视觉资产（Assets First）

所有分镜首帧严格由以下 3 大母版资产多图参考生成，保证整片人物五官、穿搭、机车机械细节与雨夜螺旋隧道空间 100% 统一：

| 主角林汐 · 4 视图母版 | 概念重型仿赛机车 · 3 视图 | 雨夜螺旋高架隧道 · 核心空镜 |
| :---: | :---: | :---: |
| ![Hero 4-View](inputs/hero_female_4view_master.jpg) | ![Superbike 3-View](inputs/asset_superbike_3view.jpg) | ![Rainy Tunnel](inputs/asset_env_rainy_tunnel.png) |

---

## 🖼️ 全片 6 镜 2K 定稿首帧画廊

| S01 · 高跟踩水钩子 | S02 · 逆光回眸（颜值暴击） | S03 · 跨坐蓄势·点火爆亮 |
| :---: | :---: | :---: |
| ![S01](outputs/keyframes/S01.png) | ![S02](outputs/keyframes/S02.png) | ![S03](outputs/keyframes/S03.png) |
| **S04 · 俯身狂飙·车头怼脸** | **S05 · 螺旋急弯极限压弯** | **S06 · 破晓终点·倚车定格** |
| ![S04](outputs/keyframes/S04.png) | ![S05](outputs/keyframes/S05.png) | ![S06](outputs/keyframes/S06.png) |

---

## ⚙️ 全链路生产管线与工程文件

| 阶段 | 工具 / 模型 | 工程文件 |
| :--- | :--- | :--- |
| **1. 剧本与分镜设计** | 黄金 30s 预告片双人声线冲突结构 | [`scripts/demo_30s_零号弯道.md`](scripts/demo_30s_零号弯道.md) |
| **2. 角色 & 资产生成** | 即梦 `Seedream 5.5`（16:9 · 2K） | [`prompts/4视图角色母版提示词模板.md`](prompts/4视图角色母版提示词模板.md)<br>[`prompts/零号弯道_前置视觉资产提示词.md`](prompts/零号弯道_前置视觉资产提示词.md) |
| **3. 自动化视频 & 音频生成** | 即梦 CLI（`dreamina-canvas`）<br>`Seedance 2.5` (720p · 60fps) + `Seed TTS` + `SeedMusic 1.0` | 6 条分镜全部 1 发通关（0 废片） |
| **4. 全代码精剪与混音** | Python + FFmpeg 8.0（1080P 超清锐化、闪切、7 轨 Ducking 混音、ASS 字幕、55Hz Boom 合成） | [`scripts/assemble_apex_zero.py`](scripts/assemble_apex_zero.py) |
| **5. 实战踩坑与避坑手册** | 防 4 视图分身、防肢体重叠/同侧双腿、防飙车忘收侧撑、Seedance 2.5 分段节拍法等 11 条硬核经验 | [`prompts/AI漫剧生图与视频避坑经验库.md`](prompts/AI漫剧生图与视频避坑经验库.md) |
