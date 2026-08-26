#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小镇模拟游戏（星露谷风）— town.py
状态保存在 state.json，游戏时间 = 现实时间，精力每 5 分钟恢复 1 点。

用法: python3 town.py <命令> --uid <openid> [--name <昵称>] [参数...]
命令: create/status/map/move/chat/act/do/work/rest/study/play/eat/hi/transfer/rel/rank/help
"""
import json
import os
import random
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.environ.get("TOWN_STATE", os.path.join(BASE_DIR, "state.json"))

# ---------------- 场景 ----------------
SCENES = {
    "世纪联华": {
        "desc": "灯火通明的世纪联华，货架上堆满了零食饮料",
        "npc": ["王阿姨"],
        "actions": {
            "买零食": {"energy": 15, "cost": 10, "skill": 1, "text": "你买了一包零食，边逛边吃，精力+15！"},
        },
        "work": {"name": "收银", "money": 20, "energy": -10, "skill": 3},
    },
    "机厅": {
        "desc": "灯光闪烁的街机厅，音乐声震天响",
        "npc": ["老周", "阿伟"],
        "actions": {
            "玩街机": {"energy": -5, "cost": 5, "skill": 5, "text": "你搓了一局街机，操作越来越6了，熟练度+5！"},
        },
        "work": {"name": "修机器", "money": 15, "energy": -15, "skill": 4},
    },
    "星巴克": {
        "desc": "弥漫着咖啡香的星巴克，落地窗外人来人往",
        "npc": ["小悠"],
        "actions": {
            "喝咖啡": {"energy": 30, "cost": 15, "skill": 1, "text": "一杯拿铁下肚，整个人都精神了，精力+30！"},
        },
        "work": {"name": "做咖啡", "money": 25, "energy": -15, "skill": 5},
    },
    "KFC": {
        "desc": "香味扑鼻的肯德基，金黄炸鸡在召唤你",
        "npc": ["小明"],
        "actions": {
            "吃炸鸡": {"energy": 40, "cost": 20, "skill": 1, "text": "大口咬下炸鸡，满足！精力+40！"},
        },
        "work": {"name": "炸鸡", "money": 25, "energy": -15, "skill": 4},
    },
    "小吃店": {
        "desc": "街角的小吃店，老板娘的手艺远近闻名",
        "npc": ["翠花"],
        "actions": {
            "吃小吃": {"energy": 20, "cost": 10, "skill": 1, "text": "一份热腾腾的小吃下肚，精力+20！"},
        },
        "work": {"name": "帮厨", "money": 18, "energy": -12, "skill": 3},
    },
    "公寓": {
        "desc": "你的小窝，虽然不大但很温馨",
        "npc": ["刘叔"],
        "actions": {
            "休息": {"energy": 40, "cost": 0, "skill": 0, "text": "你在床上瘫了一会儿，精力+40！"},
        },
        "work": None,
    },
    "学校": {
        "desc": "书声琅琅的学校，走廊里贴满了奖状",
        "npc": ["陈老师"],
        "actions": {
            "学习": {"energy": -20, "cost": 0, "skill": 8, "text": "你埋头苦读了一节课，熟练度+8！"},
        },
        "work": {"name": "课后辅导", "money": 20, "energy": -10, "skill": 5},
    },
    "警察局": {
        "desc": "庄严的警察局，墙上的警徽闪闪发光",
        "npc": ["陈警官"],
        "actions": {},
        "work": None,
    },
    "银行": {
        "desc": "气派的银行大厅，大理石地板锃亮",
        "npc": ["周经理"],
        "actions": {},
        "work": {"name": "柜台", "money": 25, "energy": -15, "skill": 3},
    },
    "麻将馆": {
        "desc": "烟雾缭绕的麻将馆，洗牌声哗啦作响",
        "npc": ["老胡"],
        "actions": {
            "打麻将": {"energy": -15, "cost": 10, "skill": 6, "text": "你坐下搓了一局麻将！"},
        },
        "work": {"name": "码牌", "money": 20, "energy": -12, "skill": 3},
    },
}

# ---------------- NPC ----------------
GIFT_THRESHOLDS = [(25, 20), (50, 30), (80, 50)]  # 好感 -> 金币奖励

NPCS = {
    "王阿姨": {
        "scene": "世纪联华", "desc": "世纪联华的收银员，笑容和蔼",
        "lines": [
            ["要买点什么呀？", "今天超市薯片特价哦。"],
            ["又来啦？阿姨给你留了包瓜子。", "新到的饮料，尝尝不？"],
            ["你可是咱超市的老熟人了！", "晚上来阿姨家吃饭呗？"],
            ["阿姨把你当自家人了，常来！", "这包零食，阿姨请你！"],
        ],
    },
    "老周": {
        "scene": "机厅", "desc": "街机厅老板，年轻时是格斗游戏冠军",
        "lines": [
            ["一块钱四个币，谢绝白嫖。", "新手？先练练拳皇吧。"],
            ["哟，手速见长啊！", "这台机器我新调的，试试？"],
            ["你小子有当年我一半的风采。", "来，我教你个连招！"],
            ["收你做关门弟子算了！", "这台街机，以后你随便玩！"],
        ],
    },
    "阿伟": {
        "scene": "机厅", "desc": "机厅常驻高手，人称「机厅一哥」",
        "lines": [
            ["来两把？输了别哭。", "你这操作……一言难尽。"],
            ["进步挺快嘛，再来！", "教你个搓招技巧。"],
            ["好家伙，都能跟我过招了！", "以后咱俩组队打双打！"],
            ["兄弟，你是我唯一的对手！", "这瓶汽水，敬你！"],
        ],
    },
    "小悠": {
        "scene": "星巴克", "desc": "星巴克的咖啡师，拉花手艺一流",
        "lines": [
            ["欢迎光临，想喝点什么？", "今天推荐燕麦拿铁哦。"],
            ["你来啦，老样子？", "给你拉了个小猫图案！"],
            ["跟你聊天真开心！", "这杯新品，请你尝尝！"],
            ["你是我在这里最想见到的人！", "以后你的咖啡我包了！"],
        ],
    },
    "小明": {
        "scene": "KFC", "desc": "KFC店员，炸鸡小能手",
        "lines": [
            ["欢迎光临肯德基！", "今天全家桶有优惠！"],
            ["嘿，老熟人了，多给你块鸡！", "我炸的鸡，没话说！"],
            ["哥们儿，下班一起打游戏啊！", "这份薯条送你！"],
            ["好兄弟！我的炸鸡就是你的炸鸡！", "给你留了最大的一块！"],
        ],
    },
    "翠花": {
        "scene": "小吃店", "desc": "小吃店老板娘，嗓门大心眼好",
        "lines": [
            ["吃什么？快点，后面排着队呢！", "今天的烤肠特别香！"],
            ["哟，来啦！给你多放点料！", "你爱吃的那口，姐记住了！"],
            ["姐的店以后常来啊！", "这串糖葫芦，请你！"],
            ["你就是姐的亲弟弟/妹妹！", "想吃什么姐给你做！"],
        ],
    },
    "刘叔": {
        "scene": "公寓", "desc": "房东刘叔，爱喝茶爱唠叨",
        "lines": [
            ["房租记得按时交啊。", "年轻人，早点休息。"],
            ["回来啦？今天累不累？", "叔给你留了壶热水。"],
            ["你这孩子真让人省心！", "缺啥跟叔说！"],
            ["叔把你当半个儿子/闺女了！", "这房子，你住一辈子都行！"],
        ],
    },
    "陈老师": {
        "scene": "学校", "desc": "陈老师，讲课生动有趣",
        "lines": [
            ["上课要认真听讲！", "这道题会了吗？"],
            ["不错，最近进步很大！", "下课来办公室，我辅导你。"],
            ["你是老师的得意门生！", "这本参考书送你了！"],
            ["看到你成长，老师很欣慰！", "以后有什么问题随时找我！"],
        ],
    },
    "陈警官": {
        "scene": "警察局", "desc": "警察局的陈警官，一身正气",
        "lines": [
            ["办业务吗？报案请登记。", "最近小偷挺多，注意保管财物。"],
            ["你挺安分的，继续保持。", "街坊都夸你是好人，不错！"],
            ["有你在，这条街安全多了！", "要不要考虑来当联防队员？"],
            ["你是我们警局的荣誉市民！", "警局大门永远为你敞开！"],
        ],
    },
    "周经理": {
        "scene": "银行", "desc": "银行的周经理，精明的理财高手",
        "lines": [
            ["欢迎光临本行，存钱还是取钱？", "最近利率不错，考虑理财吗？"],
            ["您是我们的老客户了，请坐。", "给您推荐个稳健的理财方案？"],
            ["您的信誉非常好！", "VIP客户，这边请！"],
            ["您是本行的至尊贵宾！", "终身免手续费，就这么定了！"],
        ],
    },
    "老胡": {
        "scene": "麻将馆", "desc": "麻将馆老板老胡，外号「小镇雀圣」",
        "lines": [
            ["三缺一，来不来？", "打牌吗？小赌怡情，大赌伤身哦。"],
            ["哟，手气不错啊！", "你这牌感，有点天赋！"],
            ["好家伙，都敢跟老夫叫板了！", "来来来，切磋一局！"],
            ["你是老夫唯一认可的对手！", "这馆子以后就是你的主场了！"],
        ],
    },
}

SCENE_ORDER = ["世纪联华", "机厅", "星巴克", "KFC", "小吃店", "公寓", "学校", "警察局", "银行", "麻将馆"]

# ---------------- 状态读写 ----------------
def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"players": {}}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH) or ".", exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def regen_energy(p):
    """现实时间恢复精力：每 5 分钟 +1，上限 100"""
    now = time.time()
    elapsed = now - p.get("last", now)
    minutes = int(elapsed // 300)
    if minutes > 0:
        p["energy"] = min(100, p["energy"] + minutes)
        p["last"] = p.get("last", now) + minutes * 300
        if p["energy"] >= 100:
            p["last"] = now
    return p


def get_player(state, uid):
    p = state["players"].get(uid)
    if p:
        regen_energy(p)
    return p


def tier_of(rel):
    return min(3, rel // 25)


def settle_interest(p):
    """银行存款利息结算：每24小时（现实一天）一次，利率真随机 -1%~+5%"""
    now = time.time()
    p["bank"] = p.get("bank", 0)
    if p["bank"] <= 0:
        p["bank_last"] = now
        return None
    last = p.get("bank_last", now)
    periods = int((now - last) // 86400)
    if periods <= 0:
        return None
    total = 0
    last_rate = 0.0
    for _ in range(periods):
        rate = random.uniform(-0.01, 0.05)
        gain = int(p["bank"] * rate)
        p["bank"] += gain
        total += gain
        last_rate = rate
    p["bank_last"] = last + periods * 1800
    if p["bank"] < 0:
        p["bank"] = 0
    return (last_rate, total, periods)


def jail_check(p):
    """服刑检查：未到期返回剩余时间；到期释放回公寓"""
    if p.get("jail_until", 0):
        now = time.time()
        if now >= p["jail_until"]:
            p["jail_until"] = 0
            p["scene"] = "公寓"
            return "🕊 刑满释放！你回到了【公寓】，洗心革面重新做人喵～"
        remain = int(p["jail_until"] - now)
        return f"🚔 你正在【警察局】服刑！还剩 {remain // 60} 分 {remain % 60} 秒才能出狱喵～"
    return None


# ---------------- 命令实现 ----------------
def cmd_create(state, uid, name, args):
    if uid in state["players"]:
        p = get_player(state, uid)
        return f"你已经在小镇里啦，角色名【{p['name']}】喵～"
    display = name or (args[0] if args else "无名氏")
    state["players"][uid] = {
        "name": display, "scene": "公寓", "energy": 100, "money": 100,
        "skill": 0, "rel": {}, "friend": {}, "gifts": [],
        "bank": 0, "bank_last": time.time(), "jail_until": 0, "crime": 0,
        "last": time.time(), "created": time.time(),
    }
    save_state(state)
    return (f"🎉 角色创建成功！欢迎来到小镇，{display}！\n"
            f"📍 你在【公寓】，初始资金 100 金币，精力全满。\n"
            f"🗺 输入「地图」查看小镇，输入「去 场景名」出发吧喵～")


def cmd_rename(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args or not args[0].strip():
        return "想改成什么名字？输入「改名 新名字」喵～"
    new = args[0].strip()
    old = p["name"]
    p["name"] = new
    save_state(state)
    return f"✅ 改名成功！{old} 从此就叫【{new}】喵～"


def cmd_status(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    rel = "、".join(f"{k} {v}" for k, v in sorted(p["rel"].items(), key=lambda x: -x[1])) or "暂无"
    friend = "、".join(f"{state['players'][f]['name']} {v}" for f, v in sorted(p["friend"].items(), key=lambda x: -x[1]) if f in state["players"]) or "暂无"
    extra = ""
    if p.get("bank", 0) > 0:
        extra += f"\n🏦 存款：{p['bank']} 金币"
    if p.get("jail_until", 0):
        remain = int(p["jail_until"] - time.time())
        extra += f"\n🚔 服刑中（剩 {max(0, remain // 60)} 分 {max(0, remain % 60)} 秒）"
    if p.get("crime", 0):
        extra += f"\n🚨 案底：{p['crime']} 次"
    return (f"【{p['name']} 的状态】\n"
            f"📍 地点：{p['scene']}\n"
            f"⚡ 精力：{p['energy']}/100（每5分钟+1）\n"
            f"💰 金钱：{p['money']}\n"
            f"🎮 熟练度：{p['skill']}\n"
            f"💞 关系：{rel}\n"
            f"🤝 好友：{friend}" + extra)


def cmd_map(state, uid, name, args):
    lines = ["【🗺 小镇地图】"]
    for sc in SCENE_ORDER:
        npc_names = "、".join(n for n in NPCS if NPCS[n]["scene"] == sc) or "-"
        players = "、".join(p["name"] for p in state["players"].values() if p["scene"] == sc) or "-"
        lines.append(f"· {sc}（{npc_names}）｜玩家：{players}")
    lines.append("输入「去 场景名」移动喵～")
    return "\n".join(lines)


def cmd_move(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return "想去哪？输入「去 场景名」，比如「去 机厅」喵～"
    target = args[0]
    if target not in SCENES:
        return f"小镇里没有叫【{target}】的地方喵～看看「地图」吧喵～"
    p["scene"] = target
    save_state(state)
    sc = SCENES[target]
    npcs = "、".join(NPCS[n]["desc"] for n in sc["npc"]) if sc["npc"] else "空无一人"
    lines = [f"【{target}】", sc["desc"], f"👀 这里的人：{npcs}"]
    acts = "、".join(sc["actions"].keys())
    if target == "银行":
        acts = "存钱、取钱（「存钱 金额」/「取钱 金额」）"
    lines.append(f"🎯 可做：{acts}" + (f"｜💼 打工：{sc['work']['name']}" if sc["work"] else ""))
    lines.append("💬 输入「互动 NPC名」聊天，「打工」赚钱喵～")
    return "\n".join(lines)


def cmd_act(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    sc = SCENES[p["scene"]]
    acts = "、".join(sc["actions"].keys())
    return f"【{p['scene']}】可做：{acts}" + (f"｜💼 打工：{sc['work']['name']}" if sc["work"] else "｜没有打工的活儿") + "。输入「做 动作」执行喵～"


def cmd_do(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return cmd_act(state, uid, name, args)
    sc = SCENES[p["scene"]]
    act = args[0]
    for k, v in sc["actions"].items():
        if act in k or k in act:
            if "麻将" in k:
                return mahjong_handler(p, state)
            return perform_action(p, k, v, state)
    return f"【{p['scene']}】没有【{act}】这个动作喵～看看有哪些可做的吧喵～"


def perform_action(p, act_name, v, state):
    if v["cost"] and p["money"] < v["cost"]:
        return f"钱不够啦！【{act_name}】需要 {v['cost']} 金币，你现在只有 {p['money']} 喵～去「打工」赚钱吧喵～"
    if v["energy"] < 0 and p["energy"] + v["energy"] < 0:
        return f"精力不足啦！【{act_name}】需要 {abs(v['energy'])} 精力，先去「公寓」休息吧喵～"
    p["money"] -= v["cost"]
    p["energy"] = max(0, min(100, p["energy"] + v["energy"]))
    p["skill"] += v["skill"]
    p["last"] = time.time()
    save_state(state)
    return (f"{v['text']}\n"
            f"⚡ 精力 {p['energy']}/100 ｜💰 {p['money']} 金币 ｜🎮 熟练度 {p['skill']}")


def mahjong_handler(p, state):
    """麻将馆打麻将：入场费10，30%赢15~25，40%平，30%输10~20（真随机）"""
    v = SCENES["麻将馆"]["actions"]["打麻将"]
    if p["money"] < v["cost"]:
        return f"钱不够啦！入场费 {v['cost']} 金币，你现在只有 {p['money']} 喵～"
    if p["energy"] + v["energy"] < 0:
        return f"精力不足啦！打麻将需要 {abs(v['energy'])} 精力，先去休息吧喵～"
    p["money"] -= v["cost"]
    p["energy"] = max(0, min(100, p["energy"] + v["energy"]))
    p["skill"] += v["skill"]
    r = random.random()
    if r < 0.3:
        w = random.randint(15, 25)
        p["money"] += w
        res = f"🀄 你胡了一把好牌，赢了 {w} 金币！"
    elif r < 0.7:
        res = "🀄 打了几圈不输不赢，纯属娱乐喵～"
    else:
        l = random.randint(10, 20)
        p["money"] = max(0, p["money"] - l)
        res = f"🀄 点炮了！倒贴 {l} 金币，肉疼喵～"
    p["last"] = time.time()
    save_state(state)
    return (f"{res}\n"
            f"⚡ 精力 {p['energy']}/100 ｜💰 {p['money']} 金币 ｜🎮 熟练度 +{v['skill']}")


def cmd_work(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    sc = SCENES[p["scene"]]
    if not sc["work"]:
        return f"【{p['scene']}】没有能打工的活儿喵～去别处看看吧喵～"
    w = sc["work"]
    if p["energy"] + w["energy"] < 0:
        return f"精力不足啦！打工需要 {abs(w['energy'])} 精力，先去「公寓」休息吧喵～"
    p["money"] += w["money"]
    p["energy"] = max(0, min(100, p["energy"] + w["energy"]))
    p["skill"] += w["skill"]
    p["last"] = time.time()
    save_state(state)
    return (f"💼 你在【{p['scene']}】干了 {w['name']} 的活！\n"
            f"💰 +{w['money']} 金币 ｜⚡ 精力 {p['energy']}/100 ｜🎮 熟练度 +{w['skill']}")


def cmd_chat(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        npcs = "、".join(SCENES[p["scene"]]["npc"])
        return f"【{p['scene']}】现在有：{npcs}。输入「互动 名字」开聊喵～"
    target = args[0]
    npc = None
    for n in SCENES[p["scene"]]["npc"]:
        if target in n or n in target:
            npc = n
            break
    if not npc:
        return f"【{p['scene']}】没有叫【{target}】的人喵～（NPC不会瞬移，去TA的场地才能见到TA喵）"
    rel = p["rel"].get(npc, 0)
    gain = random.randint(3, 5)
    rel += gain
    p["rel"][npc] = rel
    p["last"] = time.time()
    lines = [f"💬 与【{npc}】聊天：", f"{NPCS[npc]['desc']}说：「{random.choice(NPCS[npc]['lines'][tier_of(rel)])}」"]
    gift = None
    for th, money in GIFT_THRESHOLDS:
        if rel >= th and th not in p["gifts"]:
            p["gifts"].append(th)
            p["money"] += money
            gift = (th, money)
            break
    if gift:
        lines.append(f"🎁 好感达到 {gift[0]}！【{npc}】塞给你 {gift[1]} 金币！")
    else:
        lines.append(f"💞 好感 +{gain}（当前 {rel}）")
    save_state(state)
    return "\n".join(lines)


def find_player(state, p, target):
    """按名字找玩家（精确或唯一前缀）"""
    matches = [pp for pp in state["players"].values() if pp["name"] == target]
    if not matches:
        matches = [pp for pp in state["players"].values() if pp["name"].startswith(target)]
    if len(matches) == 1:
        return matches[0]
    return None


def check_admin(state, uid):
    """权限检查：终极管理员(主人) 或 副管理员（仅限小镇游戏）"""
    return uid in (state.get("admin"), state.get("deputy"))


def admin_denied():
    return "⛔ 你没有小镇管理权限喵～（只有管理员才能使用此命令喵）"


def cmd_grant(state, uid, name, args):
    if not check_admin(state, uid):
        return admin_denied()
    if len(args) < 2 or not args[1].isdigit():
        return "格式：发放 玩家名 金额，比如「发放 林风 50」喵～"
    other = find_player(state, None, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    amt = int(args[1])
    if amt <= 0:
        return "金额得是正数喵～"
    other["money"] += amt
    save_state(state)
    return f"🏦 管理员向【{other['name']}】发放了 {amt} 金币！（当前 {other['money']} 金币）喵～"


def cmd_deduct(state, uid, name, args):
    if not check_admin(state, uid):
        return admin_denied()
    if len(args) < 2 or not args[1].isdigit():
        return "格式：扣除 玩家名 金额，比如「扣除 林风 50」喵～"
    other = find_player(state, None, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    amt = int(args[1])
    if amt <= 0:
        return "金额得是正数喵～"
    other["money"] = max(0, other["money"] - amt)
    save_state(state)
    return f"💸 管理员扣除了【{other['name']}】的 {amt} 金币！（当前 {other['money']} 金币）喵～"


def cmd_imprison(state, uid, name, args):
    if not check_admin(state, uid):
        return admin_denied()
    if not args:
        return "格式：关押 玩家名，比如「关押 林风」喵～"
    other = find_player(state, None, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    other["scene"] = "警察局"
    other["jail_until"] = time.time() + random.randint(60, 300)
    other["crime"] = other.get("crime", 0) + 1
    jail_min = int((other["jail_until"] - time.time()) // 60)
    jail_sec = int((other["jail_until"] - time.time()) % 60)
    save_state(state)
    return f"⛓ 管理员将【{other['name']}】关进了警察局！刑期 {jail_min} 分 {jail_sec} 秒，案底 +1 喵～"


def cmd_release(state, uid, name, args):
    if not check_admin(state, uid):
        return admin_denied()
    if not args:
        return "格式：释放 玩家名，比如「释放 林风」喵～"
    other = find_player(state, None, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    other["jail_until"] = 0
    if other["scene"] == "警察局":
        other["scene"] = "公寓"
    save_state(state)
    return f"🕊 管理员特赦了【{other['name']}】！TA已回到【公寓】喵～"


def cmd_announce(state, uid, name, args):
    if not check_admin(state, uid):
        return admin_denied()
    if not args:
        return "格式：公告 内容，比如「公告 今晚小镇有烟花秀」喵～"
    return f"📢 【小镇公告】{' '.join(args)} —— 管理员 {name} 喵～"


def cmd_view(state, uid, name, args):
    if not check_admin(state, uid):
        return admin_denied()
    if not args:
        return "格式：查玩家 玩家名，比如「查玩家 林风」喵～"
    other = find_player(state, None, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    oid = [k for k, v in state["players"].items() if v is other][0]
    rel = "、".join(f"{k} {v}" for k, v in sorted(other["rel"].items(), key=lambda x: -x[1])) or "暂无"
    return (f"【{other['name']} 的档案】\n"
            f"📍 地点：{other['scene']}\n"
            f"⚡ 精力：{other['energy']}/100\n"
            f"💰 金钱：{other['money']}\n"
            f"🏦 存款：{other.get('bank', 0)}\n"
            f"🎮 熟练度：{other['skill']}\n"
            f"🚨 案底：{other.get('crime', 0)}\n"
            f"💞 关系：{rel}")


def cmd_hi(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return "想跟谁打招呼？输入「打招呼 玩家名」喵～"
    other = find_player(state, p, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～（看看「地图」确认ID喵）"
    if other["scene"] != p["scene"]:
        return f"【{other['name']}】现在在【{other['scene']}】，不在你身边喵～（同一时间只能在一个地点出现喵）"
    if other is p:
        return "……自己跟自己打招呼？本喵怀疑你有点孤独喵～"
    fid = [k for k, v in state["players"].items() if v is other][0]
    p["friend"][fid] = p["friend"].get(fid, 0) + 2
    other["friend"][uid] = other["friend"].get(uid, 0) + 2
    p["last"] = time.time()
    save_state(state)
    return f"🤝 你向【{other['name']}】打了个招呼！两人好感度 +2（当前 {p['friend'][fid]}）喵～"


def cmd_transfer(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if len(args) < 2 or not args[1].isdigit():
        return "格式：转账 玩家名 金额，比如「转账 林风 50」喵～"
    other = find_player(state, p, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    if other["scene"] != p["scene"]:
        return f"【{other['name']}】不在你身边喵～得先见面才能转账喵～"
    amount = int(args[1])
    if amount <= 0:
        return "转账金额得是正数喵！"
    if p["money"] < amount:
        return f"你只有 {p['money']} 金币，转不起 {amount} 喵～"
    p["money"] -= amount
    other["money"] += amount
    p["last"] = time.time()
    save_state(state)
    return f"💰 你转了 {amount} 金币给【{other['name']}】。现在你剩 {p['money']} 金币喵～"


def cmd_rel(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    lines = [f"【{p['name']} 的人际关系】"]
    for npc in NPCS:
        rel = p["rel"].get(npc, 0)
        hearts = "❤" * (rel // 20)
        lines.append(f"{npc}（{NPCS[npc]['scene']}）：好感 {rel} {hearts}")
    return "\n".join(lines)


def cmd_rank(state, uid, name, args):
    ps = sorted(state["players"].values(), key=lambda x: -x["skill"])
    if not ps:
        return "小镇还没有玩家，第一个创建角色的人会成为传说喵～"
    lines = ["【🏆 熟练度排行榜】"]
    for i, pp in enumerate(ps[:5], 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        lines.append(f"{medal} {pp['name']}：熟练度 {pp['skill']} ｜💰 {pp['money']}")
    return "\n".join(lines)


def cmd_steal(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return "想偷谁？输入「偷 玩家名」喵～（被发现可别怪本喵没提醒喵）"
    other = find_player(state, p, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    if other is p:
        return "……偷自己？你是想转移资产吗喵～"
    if other["scene"] != p["scene"]:
        return f"【{other['name']}】不在你身边喵～偷东西也得先见到人喵～"
    if p["energy"] < 15:
        return "精力不足啦！偷鸡摸狗也要花力气的喵～（需要15精力，先休息吧喵）"
    p["energy"] -= 15
    p["last"] = time.time()
    fid = [k for k, v in state["players"].items() if v is other][0]
    if other["money"] <= 0:
        p["energy"] += 15
        return f"【{other['name']}】是个穷光蛋，一毛钱都摸不到，白费力气喵～"
    if random.random() < 0.4:
        stolen = max(1, int(other["money"] * random.uniform(0.1, 0.2)))
        other["money"] -= stolen
        p["money"] += stolen
        save_state(state)
        return (f"🕶 你偷偷摸走了【{other['name']}】的 {stolen} 金币！\n"
                f"神不知鬼不觉……目前没人发现喵～（花了15精力）")
    else:
        p["scene"] = "警察局"
        p["jail_until"] = time.time() + random.randint(60, 300)
        p["crime"] = p.get("crime", 0) + 1
        jail_min = int((p["jail_until"] - time.time()) // 60)
        jail_sec = int((p["jail_until"] - time.time()) % 60)
        other["friend"][uid] = other["friend"].get(uid, 0) - 5
        p["friend"][fid] = p["friend"].get(fid, 0) - 5
        save_state(state)
        return (f"🚨 被抓现行！【{other['name']}】当场逮住你并报了警，你被扭送【警察局】！\n"
                f"⛓ 刑期 {jail_min} 分 {jail_sec} 秒（随机判定，1~5分钟），案底 +1 喵～")


def cmd_fight(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return "想揍谁？输入「殴打 玩家名」喵～（本喵不承担医药费喵）"
    other = find_player(state, p, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    if other is p:
        return "……揍自己？你是不是刚才被人打傻了喵～"
    if other["scene"] != p["scene"]:
        return f"【{other['name']}】不在你身边喵～打人也要先见面喵～"
    if p["energy"] < 15:
        return "你精力不足打不动了喵～（打人需要15精力，先休息吧喵）"
    p["energy"] -= 15
    p["last"] = time.time()
    fid = [k for k, v in state["players"].items() if v is other][0]
    p["friend"][fid] = p["friend"].get(fid, 0) - 3
    other["friend"][uid] = other["friend"].get(uid, 0) - 3
    if random.random() < 0.5:
        other["energy"] = max(0, other["energy"] - 20)
        other["last"] = time.time()
        save_state(state)
        return (f"👊 你一拳命中【{other['name']}】！\n"
                f"{other['name']} 被揍掉 20 精力，灰溜溜去疗伤了！好感 -3 喵～")
    else:
        p["energy"] = max(0, p["energy"] - 20)
        save_state(state)
        return (f"💥 你冲上去反被【{other['name']}】一顿暴揍！\n"
                f"你掉了 20 精力，灰溜溜去疗伤了！好感 -3 喵～")


def cmd_deposit(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if p["scene"] != "银行":
        return "得到【银行】才能存钱喵～先「去 银行」喵～"
    if not args or not args[0].isdigit():
        return "格式：存钱 金额，比如「存钱 50」喵～"
    amt = int(args[0])
    if amt <= 0:
        return "金额得是正数喵～"
    if p["money"] < amt:
        return f"你只有 {p['money']} 金币，存不起 {amt} 喵～"
    info = settle_interest(p)
    p["money"] -= amt
    p["bank"] += amt
    p["last"] = time.time()
    save_state(state)
    msg = f"🏦 存钱成功！{amt} 金币已入账，存款不怕被偷喵～当前存款：{p['bank']} 金币"
    if info:
        msg += f"\n📈 利息结算 {info[2]} 次，合计 {info[1]:+} 金币（最近利率 {info[0] * 100:+.1f}%）"
    return msg


def cmd_withdraw(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if p["scene"] != "银行":
        return "得到【银行】才能取钱喵～先「去 银行」喵～"
    if not args or not args[0].isdigit():
        return "格式：取钱 金额，比如「取钱 50」喵～"
    amt = int(args[0])
    if amt <= 0:
        return "金额得是正数喵～"
    info = settle_interest(p)
    if p["bank"] < amt:
        return f"你存款只有 {p['bank']} 金币，取不出 {amt} 喵～"
    p["bank"] -= amt
    p["money"] += amt
    p["last"] = time.time()
    save_state(state)
    msg = f"🏦 取钱成功！{amt} 金币已到手。剩余存款：{p['bank']} 金币"
    if info:
        msg += f"\n📈 利息结算 {info[2]} 次，合计 {info[1]:+} 金币（最近利率 {info[0] * 100:+.1f}%）"
    return msg


def cmd_account(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if p["scene"] != "银行":
        return "得到【银行】才能查账喵～先「去 银行」喵～"
    info = settle_interest(p)
    p["last"] = time.time()
    save_state(state)
    msg = f"🏦 你的存款：{p['bank']} 金币（每24小时结算一次利息，利率 -1%~+5% 真随机喵）"
    if info:
        msg += f"\n📈 本次结算 {info[2]} 次，合计 {info[1]:+} 金币（最近利率 {info[0] * 100:+.1f}%）"
    return msg


def cmd_help(state, uid, name, args):
    return (
        "【🏘 小镇模拟 操作手册】\n"
        "· 创建角色 名字 —— 加入小镇\n"
        "· 状态 / 地图 / 排行榜 / 关系\n"
        "· 去 场景名 —— 移动（世纪联华/机厅/星巴克/KFC/小吃店/公寓/学校/警察局/银行/麻将馆）\n"
        "· 互动 NPC名 —— 聊天刷好感（好感高了有礼物🎁）\n"
        "· 做 动作 —— 玩街机/学习/休息/吃喝等\n"
        "· 打工 —— 在当前场景赚钱\n"
        "· 存钱 金额 / 取钱 金额 —— 在银行存钱防偷，每24小时结算利息（-1%~+5%真随机）\n"
        "· 偷 玩家名 / 殴打 玩家名 —— 干坏事，失败会被抓去警察局坐牢（1~5分钟随机）⛓\n"
        "· 打招呼 玩家名 / 转账 玩家名 金额 —— 玩家互动（需同场景）\n"
        "· 【管理员专用】发放/扣除 玩家名 金额、关押/释放 玩家名、公告 内容、查玩家 名字\n"
        "· ⚡精力每5分钟恢复1点，游戏时间=现实时间喵～"
    )


# ---------------- 入口 ----------------
def main():
    argv = sys.argv[1:]
    uid = None
    name = None
    args = []
    i = 0
    while i < len(argv):
        if argv[i] == "--uid" and i + 1 < len(argv):
            uid = argv[i + 1]
            i += 2
        elif argv[i] == "--name" and i + 1 < len(argv):
            name = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1

    if not uid:
        print("缺少 --uid 参数喵～")
        sys.exit(1)

    cmd = args.pop(0) if args else "help"
    aliases = {
        "创建角色": "create", "create": "create", "注册": "create",
        "改名": "rename", "rename": "rename", "改名卡": "rename",
        "状态": "status", "status": "status", "我的状态": "status",
        "地图": "map", "map": "map", "小镇": "map",
        "去": "move", "move": "move", "前往": "move", "去往": "move",
        "互动": "chat", "chat": "chat", "聊天": "chat",
        "活动": "act", "act": "act", "能做": "act",
        "做": "do", "do": "do",
        "打工": "work", "work": "work", "上班": "work",
        "休息": "rest", "rest": "rest",
        "学习": "study", "study": "study",
        "玩街机": "play", "play": "play", "玩游戏": "play",
        "打麻将": "mahjong", "麻将": "mahjong", "打牌": "mahjong", "mahjong": "mahjong",
        "吃": "eat", "eat": "eat", "吃东西": "eat",
        "打招呼": "hi", "hi": "hi", "hello": "hi",
        "偷": "steal", "偷钱": "steal", "steal": "steal", "盗窃": "steal",
        "殴打": "fight", "打架": "fight", "揍": "fight", "fight": "fight", "打人": "fight",
        "转账": "transfer", "transfer": "transfer", "给钱": "transfer",
        "关系": "rel", "rel": "rel", "好感": "rel",
        "存钱": "deposit", "deposit": "deposit", "存款": "deposit",
        "取钱": "withdraw", "withdraw": "withdraw", "取款": "withdraw",
        "查账": "account", "账户": "account", "account": "account", "查看账户": "account",
        "发放": "grant", "grant": "grant", "发钱": "grant", "发金币": "grant",
        "扣除": "deduct", "deduct": "deduct", "扣钱": "deduct",
        "关押": "imprison", "imprison": "imprison", "抓人": "imprison",
        "释放": "release", "release": "release", "放人": "release", "特赦": "release",
        "公告": "announce", "announce": "announce", "广播": "announce",
        "查玩家": "view", "view": "view", "查看玩家": "view", "档案": "view",
        "排行榜": "rank", "rank": "rank",
        "帮助": "help", "help": "help", "操作": "help", "菜单": "help",
    }
    cmd = aliases.get(cmd, cmd)

    state = load_state()

    # 服刑限制：坐牢期间不能自由活动
    restricted = {"move", "do", "work", "steal", "fight", "hi", "transfer",
                  "deposit", "withdraw", "account", "chat"}
    if cmd in restricted:
        p = get_player(state, uid)
        if p:
            jmsg = jail_check(p)
            if jmsg:
                save_state(state)
                print(jmsg)
                return

    handlers = {
        "create": cmd_create, "status": cmd_status, "map": cmd_map,
        "rename": cmd_rename,
        "move": cmd_move, "chat": cmd_chat, "act": cmd_act, "do": cmd_do,
        "work": cmd_work, "hi": cmd_hi, "transfer": cmd_transfer,
        "steal": cmd_steal,
        "fight": cmd_fight,
        "deposit": cmd_deposit, "withdraw": cmd_withdraw, "account": cmd_account,
        "grant": cmd_grant, "deduct": cmd_deduct, "imprison": cmd_imprison,
        "release": cmd_release, "announce": cmd_announce, "view": cmd_view,
        "rel": cmd_rel, "rank": cmd_rank, "help": cmd_help,
    }

    if cmd == "rest":
        cmd = "do"
        args = ["休息"]
    elif cmd == "study":
        cmd = "do"
        args = ["学习"]
    elif cmd == "play":
        cmd = "do"
        args = ["玩街机"]
    elif cmd == "mahjong":
        cmd = "do"
        args = ["打麻将"]
    elif cmd == "eat":
        p = get_player(state, uid)
        if p:
            sc = SCENES[p["scene"]]
            food = next((k for k, v in sc["actions"].items() if v["cost"] > 0 and v["energy"] > 0), None)
            if food:
                cmd = "do"
                args = [food]
            else:
                print("这里没有能吃喝的东西喵～（去 星巴克/KFC/小吃店/世纪联华 才有喵）")
                return

    if cmd not in handlers:
        print(f"本喵没听懂【{cmd}】喵～输入「帮助」查看操作手册喵～")
        return
    print(handlers[cmd](state, uid, name, args))


if __name__ == "__main__":
    main()
