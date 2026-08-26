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
            "买零食": {"energy": 15, "cost": 10, "stat": "con", "text": "你买了一包零食，边逛边吃，精力+15！"},
        },
        "work": {"name": "收银", "money": 20, "energy": -10, "stat": "str"},
    },
    "机厅": {
        "desc": "灯光闪烁的街机厅，音乐声震天响",
        "npc": ["老周", "阿伟"],
        "actions": {
            "玩街机": {"energy": -5, "cost": 30, "stat": "dex", "text": "你搓了一局街机，操作越来越6了！"},
            "舞萌": {"energy": -20, "cost": 50, "stat": "dex", "text": "你上手了舞萌（maimai），音符如雨点般砸来！"},
            "推币机": {"energy": -15, "cost": 400, "stat": "luk", "text": "你往推币机里塞了一把币……"},
            "抓娃娃": {"energy": -5, "cost": 20, "stat": "dex", "text": "你操控爪子对准了娃娃机里的玩偶……"},
        },
        "work": {"name": "修机器", "money": 15, "energy": -15, "stat": "str"},
    },
    "星巴克": {
        "desc": "弥漫着咖啡香的星巴克，落地窗外人来人往",
        "npc": ["小悠"],
        "actions": {
            "喝咖啡": {"energy": 30, "cost": 15, "stat": "con", "text": "一杯拿铁下肚，整个人都精神了，精力+30！"},
        },
        "work": {"name": "做咖啡", "money": 25, "energy": -15, "stat": "int"},
    },
    "KFC": {
        "desc": "香味扑鼻的肯德基，金黄炸鸡在召唤你",
        "npc": ["小明"],
        "actions": {
            "吃炸鸡": {"energy": 40, "cost": 20, "stat": "con", "text": "大口咬下炸鸡，满足！精力+40！"},
        },
        "work": {"name": "炸鸡", "money": 25, "energy": -15, "stat": "str"},
    },
    "小吃店": {
        "desc": "街角的小吃店，老板娘的手艺远近闻名",
        "npc": ["翠花"],
        "actions": {
            "吃小吃": {"energy": 20, "cost": 10, "stat": "con", "text": "一份热腾腾的小吃下肚，精力+20！"},
        },
        "work": {"name": "帮厨", "money": 18, "energy": -12, "stat": "str"},
    },
    "公寓": {
        "desc": "你的小窝，虽然不大但很温馨",
        "npc": ["刘叔"],
        "actions": {
            "休息": {"energy": 40, "cost": 0, "stat": "con", "text": "你在床上瘫了一会儿，精力+40！"},
        },
        "work": None,
    },
    "学校": {
        "desc": "书声琅琅的学校，走廊里贴满了奖状",
        "npc": ["陈老师"],
        "actions": {
            "学习": {"energy": -20, "cost": 0, "stat": "int", "text": "你埋头苦读了一节课，智力+8！"},
        },
        "work": {"name": "课后辅导", "money": 20, "energy": -10, "stat": "int"},
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
        "work": {"name": "柜台", "money": 25, "energy": -15, "stat": "int"},
    },
    "麻将馆": {
        "desc": "烟雾缭绕的麻将馆，洗牌声哗啦作响",
        "npc": ["老胡"],
        "actions": {
            "打麻将": {"energy": -15, "cost": 10, "stat": "luk", "stat_gain": 0, "text": "你坐下搓了一局麻将！"},
        },
        "work": {"name": "码牌", "money": 20, "energy": -12, "stat": "str"},
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
                data = json.load(f)
                for p in data.get("players", {}).values():
                    migrate_player(p)
                return data
        except Exception:
            pass
    return {"players": {}}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH) or ".", exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def max_energy(p):
    """体质 CON 提高体力上限：100 + CON*2"""
    return 100 + (p.get("con") or 5) * 2


REST_SECONDS = 1800  # 公寓休息：现实 30 分钟


def check_rest(p):
    """检查休息是否完成：完成后精力回满"""
    if p.get("rest_until"):
        if time.time() >= p["rest_until"]:
            p["energy"] = max_energy(p)
            p["rest_until"] = 0
    return p


def regen_energy(p):
    """现实时间恢复精力：每 5 分钟恢复 1 + INT//20 点（智力加成），上限由体质决定"""
    check_rest(p)
    now = time.time()
    elapsed = now - p.get("last", now)
    minutes = int(elapsed // 300)
    cap = max_energy(p)
    if minutes > 0:
        rate = 1 + (p.get("int") or 5) // 20
        p["energy"] = min(cap, p["energy"] + minutes * rate)
        p["last"] = p.get("last", now) + minutes * 300
        if p["energy"] >= cap:
            p["last"] = now
    return p


def migrate_player(p):
    """旧存档迁移：skill 字段 → 五项属性（skill 均摊到各属性）"""
    if "skill" in p and "str" not in p:
        s = p.pop("skill", 0)
        base = 5 + s // 5
        p["str"] = p["dex"] = p["int"] = p["con"] = p["luk"] = base
    for k in ("str", "dex", "int", "con", "luk"):
        p.setdefault(k, 5 if k in ("str", "int") else 0)
    p.setdefault("gender", "未知")
    p.setdefault("pending", None)
    p.setdefault("spouse", None)
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
GENDER_ALIAS = {"男": "男", "女": "女", "男生": "男", "女生": "女", "公": "男", "母": "女"}


def cmd_create(state, uid, name, args):
    if uid in state["players"]:
        p = get_player(state, uid)
        return f"你已经在小镇里啦，角色名【{p['name']}】喵～"
    gender = None
    rest = list(args)
    if name:
        display = name
        if rest and rest[0] in GENDER_ALIAS:
            gender = GENDER_ALIAS[rest.pop(0)]
    else:
        if not rest:
            return "想好名字和性别再进小镇喵～格式：创建角色 名字 男/女"
        display = rest.pop(0)
        if rest and rest[0] in GENDER_ALIAS:
            gender = GENDER_ALIAS[rest.pop(0)]
    if not gender:
        return f"请选择性别喵～格式：创建角色 {display} 男/女"
    if rest:
        display = display
    state["players"][uid] = {
        "name": display, "gender": gender, "scene": "公寓", "energy": 100, "money": 100,
        "str": 5, "dex": 0, "int": 5, "con": 0, "luk": 0,
        "rel": {}, "friend": {}, "gifts": [], "pending": None,
        "bank": 0, "bank_last": time.time(), "jail_until": 0, "crime": 0,
        "spouse": None,
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
    if p.get("rest_until", 0):
        remain = int(p["rest_until"] - time.time())
        extra += f"\n🛏 休息中（剩 {max(0, remain // 60)} 分 {max(0, remain % 60)} 秒，完成后精力回满）"
    if p.get("jail_until", 0):
        remain = int(p["jail_until"] - time.time())
        extra += f"\n🚔 服刑中（剩 {max(0, remain // 60)} 分 {max(0, remain % 60)} 秒）"
    if p.get("crime", 0):
        extra += f"\n🚨 案底：{p['crime']} 次"
    if p.get("toys", 0):
        extra += f"\n🧸 娃娃：{p['toys']} 个（可「送娃娃」送人加好感）"
    rate = 1 + (p.get("int") or 5) // 20
    return (f"【{p['name']} 的状态】\n"
            f"👤 性别：{p.get('gender','未知')}｜📍 地点：{p['scene']}\n"
            f"⚡ 精力：{p['energy']}/{max_energy(p)}（每5分钟+{rate}，体质定上限）\n"
            f"💰 金钱：{p['money']}\n"
            f"💪 力量 STR：{p.get('str',5)} ｜🦾 敏捷 DEX：{p.get('dex',5)}\n"
            f"🧠 智力 INT：{p.get('int',5)} ｜🛡 体质 CON：{p.get('con',5)} ｜🍀 幸运 LUK：{p.get('luk',5)}\n"
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


GAME_COOLDOWN = 900  # 大型机台冷却：现实 15 分钟


def check_game_cd(p, game):
    """检查机台冷却，返回剩余秒数或 0（可玩）"""
    cd = p.get("cd") or {}
    until = cd.get(game, 0)
    remain = int(until - time.time())
    return max(0, remain)


def set_game_cd(p, game, seconds=GAME_COOLDOWN):
    p.setdefault("cd", {})[game] = time.time() + seconds


def arcade_handler(p, state):
    """玩街机：30金币/次，敏捷衰减"""
    v = SCENES["机厅"]["actions"]["玩街机"]
    cost = spend(p, v["cost"])
    if p["money"] < cost:
        return f"钱不够啦！玩街机需要 {cost} 金币，你现在只有 {p['money']} 喵～"
    if p["energy"] + v["energy"] < 0:
        return f"精力不足啦！玩街机需要 {abs(v['energy'])} 精力，先去休息吧喵～"
    p["money"] -= cost
    p["energy"] = max(0, min(max_energy(p), p["energy"] + v["energy"]))
    dex = p.get("dex", 0)
    gain = max(1, int(5 * 100 / (100 + dex)))
    p["dex"] = dex + gain
    p["last"] = time.time()
    save_state(state)
    return (f"🕹 你搓了一局街机，操作越来越6了！\n"
            f"🦾 敏捷 +{gain}（当前 {p['dex']}，敏捷越高提升越慢）｜⚡ 精力 {p['energy']}/{max_energy(p)}｜💰 {p['money']} 金币")


def maimai_handler(p, state, uid, partner=None):
    """舞萌（maimai）：50金币/次，-20精力，15分钟冷却，练敏捷和力量。带玩家名=双人模式（好感+1）"""
    v = SCENES["机厅"]["actions"]["舞萌"]
    remain = check_game_cd(p, "maimai")
    if remain > 0:
        return f"🕹 舞萌机台还在散热……还需 {remain // 60} 分 {remain % 60} 秒才能再玩喵～"
    cost = spend(p, v["cost"])
    if p["money"] < cost:
        return f"钱不够啦！舞萌需要 {cost} 金币，你现在只有 {p['money']} 喵～"
    if p["energy"] + v["energy"] < 0:
        return f"精力不足啦！舞萌需要 {abs(v['energy'])} 精力，先去休息吧喵～"
    p["money"] -= cost
    p["energy"] = max(0, min(max_energy(p), p["energy"] + v["energy"]))
    dex = p.get("dex", 0)
    str_ = p.get("str", 5)
    dex_gain = max(1, int(5 * 100 / (100 + dex)))
    str_gain = max(1, int(3 * 100 / (100 + str_)))
    p["dex"] = dex + dex_gain
    p["str"] = str_ + str_gain
    set_game_cd(p, "maimai")
    msg = (f"🎵 你在舞萌上打出了漂亮的连击！\n"
           f"🦾 敏捷 +{dex_gain}（当前 {p['dex']}）｜💪 力量 +{str_gain}（当前 {p['str']}）\n"
           f"⚡ 精力 {p['energy']}/{max_energy(p)}｜💰 {p['money']} 金币（机台冷却 15 分钟）")
    if partner is not None:
        fid = [k for k, v in state["players"].items() if v is partner][0]
        g1 = friend_gain(p, 1)
        g2 = friend_gain(partner, 1)
        p["friend"][fid] = friend_clamp(p["friend"].get(fid, 0) + g1)
        partner["friend"][uid] = friend_clamp(partner["friend"].get(uid, 0) + g2)
        msg += (f"\n🎵 你和【{partner['name']}】双人共舞！默契 +{g1:g}/+{g2:g} 好感"
                f"（你对TA：{p['friend'][fid]:g}/200）")
    p["last"] = time.time()
    save_state(state)
    return msg


def coin_handler(p, state):
    """推币机：400金币/次，-15精力，15分钟冷却。奖池=所有玩家累计投入，5%中奖赢走奖池10%~15%"""
    v = SCENES["机厅"]["actions"]["推币机"]
    remain = check_game_cd(p, "coin")
    if remain > 0:
        return f"🪙 推币机还在哗啦哗啦……还需 {remain // 60} 分 {remain % 60} 秒才能再玩喵～"
    cost = spend(p, v["cost"])
    if p["money"] < cost:
        return f"钱不够啦！推币机需要 {cost} 金币，你现在只有 {p['money']} 喵～"
    if p["energy"] + v["energy"] < 0:
        return f"精力不足啦！推币机需要 {abs(v['energy'])} 精力，先去休息吧喵～"
    p["money"] -= cost
    p["energy"] = max(0, min(max_energy(p), p["energy"] + v["energy"]))
    pool = state.setdefault("coin_pool", 0)
    pool += v["cost"]
    state["coin_pool"] = pool
    set_game_cd(p, "coin")
    p["last"] = time.time()
    save_state(state)
    r = random.random()
    if r < 0.50:
        # 普通中奖：400 本金 + 400×20%~40% 额外
        bonus = int(400 * random.uniform(0.20, 0.40))
        prize = 400 + bonus
        p["money"] += prize
        state["coin_pool"] = max(0, pool - 400)
        save_state(state)
        return (f"🪙 推币机哗啦啦吐出金币！普通中奖！\n"
                f"你赢回本金 400 + 红利 {bonus} = {prize} 金币！\n"
                f"⚡ 精力 {p['energy']}/{max_energy(p)}｜💰 你现有 {p['money']} 金币（奖池 {state['coin_pool']}）")
    elif r < 0.98:
        # 输光：48%
        return (f"🪙 你塞进 400 金币……币哗啦啦掉进机子深处，血本无归喵～\n"
                f"（奖池累计 {state['coin_pool']} 金币，2% 超级大奖清空全场）｜⚡ 精力 {p['energy']}/{max_energy(p)}｜💰 你现有 {p['money']} 金币")
    else:
        # 超级大奖：2%，赢走奖池全部
        prize = pool
        p["money"] += prize
        state["coin_pool"] = 0
        save_state(state)
        return (f"🪙✨✨ 推币机发出震耳欲聋的警报——超级大奖！！\n"
                f"你赢走了之前所有玩家投入的 {prize} 金币！奖池被清空！\n"
                f"⚡ 精力 {p['energy']}/{max_energy(p)}｜💰 你现有 {p['money']} 金币")


def claw_handler(p, state):
    """抓娃娃：20金币/次，20%概率，累计花费100金币触发保底（下次必中）"""
    v = SCENES["机厅"]["actions"]["抓娃娃"]
    cost = spend(p, v["cost"])
    if p["money"] < cost:
        return f"钱不够啦！抓娃娃需要 {cost} 金币，你现在只有 {p['money']} 喵～"
    if p["energy"] + v["energy"] < 0:
        return f"精力不足啦！抓娃娃需要 {abs(v['energy'])} 精力，先去休息吧喵～"
    p["money"] -= cost
    p["energy"] = max(0, min(max_energy(p), p["energy"] + v["energy"]))
    spent = p.get("claw_spent", 0) + cost
    p["claw_spent"] = spent
    guaranteed = p.get("claw_guarantee", False)
    p["last"] = time.time()
    if guaranteed or random.random() < 0.20:
        p["toys"] = p.get("toys", 0) + 1
        p["claw_spent"] = 0
        p["claw_guarantee"] = False
        save_state(state)
        return (f"🧸 爪子稳稳抓住了娃娃！！你得到了一个娃娃！（现有 {p['toys']} 个）\n"
                f"{'（保底触发！）' if guaranteed else ''}用「送娃娃 玩家名」送给别人增加好感喵～\n"
                f"⚡ 精力 {p['energy']}/{max_energy(p)}｜💰 {p['money']} 金币")
    if spent >= 100:
        p["claw_guarantee"] = True
        save_state(state)
        return (f"🎯 爪子又滑走了……但累计已花费 {spent} 金币，触发保底！下一次 100% 抓到喵～\n"
                f"⚡ 精力 {p['energy']}/{max_energy(p)}｜💰 {p['money']} 金币")
    save_state(state)
    return (f"🎯 爪子滑了一下，娃娃掉了……（累计花费 {spent}/100 触发保底）\n"
            f"⚡ 精力 {p['energy']}/{max_energy(p)}｜💰 {p['money']} 金币")


def cmd_rest(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if p["scene"] != "公寓":
        return "只有回到【公寓】才能休息喵～先「去 公寓」喵～"
    if p.get("rest_until"):
        remain = int(p["rest_until"] - time.time())
        return f"🛏 你正在休息中……还剩 {remain // 60} 分 {remain % 60} 秒，休息完精力回满喵～"
    p["rest_until"] = time.time() + REST_SECONDS
    p["last"] = time.time()
    save_state(state)
    return "🛏 你在床上躺下，闭上眼睛……30 分钟后精力回满喵～"


def cmd_do(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return cmd_act(state, uid, name, args)
    sc = SCENES[p["scene"]]
    act = args[0]
    if "休息" in act:
        return cmd_rest(state, uid, name, args)
    for k, v in sc["actions"].items():
        if act in k or k in act:
            if "麻将" in k:
                return mahjong_handler(p, state)
            if "街机" in k:
                return arcade_handler(p, state)
            if "舞萌" in k or "maimai" in act or "乌蒙" in act:
                partner = None
                if len(args) > 1:
                    partner = find_player(state, p, args[1])
                    if not partner:
                        return f"没找到叫【{args[1]}】的玩家喵～"
                return maimai_handler(p, state, uid, partner)
            if "推币" in k:
                return coin_handler(p, state)
            if "抓娃娃" in k or "抓" in act:
                return claw_handler(p, state)
            return perform_action(p, k, v, state)
    return f"【{p['scene']}】没有【{act}】这个动作喵～看看有哪些可做的吧喵～"


def perform_action(p, act_name, v, state):
    cost = spend(p, v["cost"])
    if v["cost"] and p["money"] < cost:
        return f"钱不够啦！【{act_name}】需要 {cost} 金币，你现在只有 {p['money']} 喵～去「打工」赚钱吧喵～"
    if v["energy"] < 0 and p["energy"] + v["energy"] < 0:
        return f"精力不足啦！【{act_name}】需要 {abs(v['energy'])} 精力，先去「公寓」休息吧喵～"
    p["money"] -= cost
    p["energy"] = max(0, min(max_energy(p), p["energy"] + v["energy"]))
    stat = v.get("stat", "con")
    p[stat] = p.get(stat, 5) + v.get("stat_gain", v.get("skill", 1))
    p["last"] = time.time()
    save_state(state)
    stat_name = {"str": "力量", "dex": "敏捷", "int": "智力", "con": "体质", "luk": "幸运"}[stat]
    return (f"{v['text']}\n"
            f"⚡ 精力 {p['energy']}/{max_energy(p)} ｜💰 {p['money']} 金币 ｜💪 {stat_name} +{v.get('stat_gain', v.get('skill', 1))}")


def mahjong_handler(p, state):
    """麻将馆打麻将：入场费10，30%赢15~25，40%平，30%输10~20（真随机）"""
    v = SCENES["麻将馆"]["actions"]["打麻将"]
    cost = spend(p, v["cost"])
    if p["money"] < cost:
        return f"钱不够啦！入场费 {cost} 金币，你现在只有 {p['money']} 喵～"
    if p["energy"] + v["energy"] < 0:
        return f"精力不足啦！打麻将需要 {abs(v['energy'])} 精力，先去休息吧喵～"
    p["money"] -= cost
    p["energy"] = max(0, min(max_energy(p), p["energy"] + v["energy"]))
    gain = v.get("stat_gain", v.get("skill", 1))
    if gain:
        p["luk"] += gain
    win_rate = min(0.85, 0.3 + p.get("luk", 0) * 0.004)  # 幸运加成胜率（LUK 当前无提升途径，基础30%）
    r = random.random()
    if r < win_rate:
        w = random.randint(15, 25)
        p["money"] += w
        res = f"🀄 你胡了一把好牌，赢了 {w} 金币！（幸运加持）"
    elif r < 0.7:
        res = "🀄 打了几圈不输不赢，纯属娱乐喵～"
    else:
        l = random.randint(10, 20)
        p["money"] = max(0, p["money"] - l)
        res = f"🀄 点炮了！倒贴 {l} 金币，肉疼喵～"
    p["last"] = time.time()
    save_state(state)
    return (f"{res}\n"
            f"⚡ 精力 {p['energy']}/{max_energy(p)} ｜💰 {p['money']} 金币 ｜🍀 幸运 +{v.get('stat_gain', v.get('skill', 1))}")


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
    bonus = 1 + (p.get("int") or 5) * 0.01  # 智力提高打工收益（每点+1%）
    gain = int(w["money"] * bonus)
    p["money"] += gain
    p["energy"] = max(0, min(max_energy(p), p["energy"] + w["energy"]))
    stat = w.get("stat", "str")
    p[stat] = p.get(stat, 5) + w.get("stat_gain", w.get("skill", 3))
    p["last"] = time.time()
    save_state(state)
    stat_name = {"str": "力量", "dex": "敏捷", "int": "智力", "con": "体质", "luk": "幸运"}[stat]
    return (f"💼 你在【{p['scene']}】干了 {w['name']} 的活！（智力加成 {int((bonus-1)*100)}%）\n"
            f"💰 +{gain} 金币 ｜⚡ 精力 {p['energy']}/{max_energy(p)} ｜💪 {stat_name} +{w.get('stat_gain', w.get('skill', 3))}")


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
    g = npc_gift_check(p, npc, state)
    if g:
        lines.append(g)
    save_state(state)
    return "\n".join(lines)


# NPC 谈心题库（选项影响好感加减）
TALK_TOPICS = [
    {
        "q": "最近过得怎么样呀？",
        "options": [
            ("挺好的，谢谢关心！", 15),
            ("有点累，但还行。", 5),
            ("还行吧，凑合过。", 0),
            ("关你什么事？", -20),
        ],
    },
    {
        "q": "你觉得我这个人怎么样？",
        "options": [
            ("你人超好的！", 15),
            ("挺好的，我很欣赏你！", 10),
            ("还行吧，一般般。", 0),
            ("……一言难尽。", -20),
        ],
    },
    {
        "q": "要不要一起去吃个饭？",
        "options": [
            ("好呀！走吧！", 15),
            ("下次吧，今天没空。", 3),
            ("……我请你？", 10),
            ("不了，我想一个人待着。", -12),
        ],
    },
]

# NPC 帮忙任务（随机）
HELP_TASKS = [
    ("搬货", 8, 5, "你帮TA把货架上的箱子搬下来整理好"),
    ("跑腿", 10, 4, "你帮TA跑了一趟腿买回了需要的东西"),
    ("修东西", 12, 6, "你帮TA修好了坏掉的小物件"),
    ("浇花", 6, 3, "你帮TA把店里的花草都浇了一遍"),
]


def cmd_npc_menu(state, uid, name, args):
    """互动菜单"""
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    sc = SCENES[p["scene"]]
    npcs = "、".join(sc["npc"]) if sc["npc"] else "（这里没有人）"
    lines = [f"【{p['scene']}】的 NPC：{npcs}",
             f"· 聊天 NPC名 —— 闲聊（好感 +3~5）",
             f"· 帮忙 NPC名 —— 帮TA做任务（成功好感 +1~5，失败 -6~-8 且赔 10 金币）"]
    for n in sc["npc"]:
        if p["rel"].get(n, 0) >= 50:
            lines.append(f"· 谈心 {n} —— 倾听心事（好感≥50 解锁，选择影响 +15~-20）")
            break
    else:
        lines.append("· 谈心 —— （与NPC好感达到 50 后解锁喵～）")
    return "\n".join(lines)


def npc_gift_check(p, npc, state):
    """好感>50 时互动有概率收到礼物：概率 10%+好感*0.7%（上限95%），价值30~100金币直接入账"""
    rel = p["rel"].get(npc, 0)
    if rel <= 50:
        return None
    rate = min(0.95, 0.10 + rel * 0.007)
    if random.random() < rate:
        value = random.randint(30, 100)
        p["money"] += value
        return f"🎁 【{npc}】送了你一份礼物，兑换成 {value} 金币！（当前 {p['money']} 金币）"
    return None


def cmd_help_npc(state, uid, name, args):
    """帮 NPC 做任务"""
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return "想帮谁？输入「帮忙 NPC名」喵～"
    npc = None
    for n in SCENES[p["scene"]]["npc"]:
        if args[0] in n or n in args[0]:
            npc = n
            break
    if not npc:
        return f"【{p['scene']}】没有叫【{args[0]}】的人喵～"
    task_name, gain, cost_energy, text = random.choice(HELP_TASKS)
    if p["energy"] < cost_energy:
        return f"精力不足啦！帮忙要花 {cost_energy} 精力，先休息吧喵～"
    p["energy"] -= cost_energy
    # 成功概率：15% + STR*0.5%（上限 90%）
    success_rate = min(0.9, 0.15 + p.get("str", 5) * 0.005)
    rel = p["rel"].get(npc, 0)
    if random.random() < success_rate:
        gain = random.randint(1, 5)
        rel += gain
        p["rel"][npc] = rel
        p["last"] = time.time()
        save_state(state)
        msg = (f"🧹 {text}！【{npc}】对你连连道谢！\n"
               f"💞 {npc} 好感 +{gain}（当前 {rel}）｜⚡ 精力 {p['energy']}/{max_energy(p)}")
        gift = npc_gift_check(p, npc, state)
        if gift:
            save_state(state)
            msg += "\n" + gift
        return msg
    else:
        penalty = random.randint(6, 8)
        rel = max(0, rel - penalty)
        p["rel"][npc] = rel
        p["money"] = max(0, p["money"] - 10)
        p["last"] = time.time()
        save_state(state)
        return (f"😅 {text}……结果搞砸了，还得TA自己返工，TA还埋怨了你几句。\n"
                f"💞 {npc} 好感 -{penalty}（当前 {rel}）｜💰 赔了 10 金币（当前 {p['money']}）｜⚡ 精力 {p['energy']}/{max_energy(p)}")


def cmd_talk(state, uid, name, args):
    """谈心：发起问题"""
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return "想找谁谈心？输入「谈心 NPC名」喵～"
    npc = None
    for n in SCENES[p["scene"]]["npc"]:
        if args[0] in n or n in args[0]:
            npc = n
            break
    if not npc:
        return f"【{p['scene']}】没有叫【{args[0]}】的人喵～"
    if p["rel"].get(npc, 0) < 50:
        return f"你与【{npc}】的好感只有 {p['rel'].get(npc, 0)}，TA还不愿意跟你谈心喵～（好感≥50 解锁）"
    topic = random.choice(TALK_TOPICS)
    p["pending"] = {"kind": "talk", "npc": npc, "q": topic["q"], "options": topic["options"]}
    save_state(state)
    lines = [f"💭 你和【{npc}】坐下来谈心：", f"「{topic['q']}」"]
    for i, (opt, _) in enumerate(topic["options"], 1):
        lines.append(f"  {i}. {opt}")
    lines.append("回复「选 数字」做出选择喵～")
    return "\n".join(lines)


def cmd_choose(state, uid, name, args):
    """处理谈心选项"""
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    pending = p.get("pending")
    if not pending or pending.get("kind") != "talk":
        return "现在没有待回答的谈心问题喵～去找 NPC 谈心吧喵～"
    if not args or not args[0].isdigit():
        return "回复「选 数字」选择选项喵～"
    idx = int(args[0]) - 1
    opts = pending.get("options", [])
    if idx < 0 or idx >= len(opts):
        return f"没有这个选项喵～输入 1~{len(opts)} 选择喵～"
    text, gain = opts[idx]
    npc = pending["npc"]
    rel = p["rel"].get(npc, 0)
    rel = max(0, rel + gain)
    p["rel"][npc] = rel
    p["pending"] = None
    p["last"] = time.time()
    save_state(state)
    sign = "+" if gain >= 0 else ""
    msg = (f"💬 你回答：「{text}」\n"
           f"【{npc}】{('开心地笑了' if gain > 0 else '神色有些复杂' if gain == 0 else '看起来不太高兴')}喵～\n"
           f"💞 {npc} 好感 {sign}{gain}（当前 {rel}）")
    gift = npc_gift_check(p, npc, state)
    if gift:
        save_state(state)
        msg += "\n" + gift
    return msg


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
    g1 = friend_gain(p, 0.5)
    g2 = friend_gain(other, 0.5)
    p["friend"][fid] = friend_clamp(p["friend"].get(fid, 0) + g1)
    other["friend"][uid] = friend_clamp(other["friend"].get(uid, 0) + g2)
    p["last"] = time.time()
    save_state(state)
    return (f"🤝 你向【{other['name']}】打了个招呼！好感度 {p['friend'][fid]}/200"
            f"（{friend_tier(p['friend'][fid])}）喵～")


def cmd_transfer(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if len(args) < 2 or not args[1].isdigit():
        return "格式：转账 玩家名 金额，比如「转账 林风 50」喵～"
    other = find_player(state, p, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
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
    if p.get("spouse"):
        sid = p["spouse"]
        sp = state["players"].get(sid)
        if sp:
            lines.append(f"💍 配偶：{sp['name']}（夫妻）")
    if p["friend"]:
        for fid, fv in sorted(p["friend"].items(), key=lambda x: -x[1]):
            fp = state["players"].get(fid)
            if fp:
                lines.append(f"👥 {fp['name']}：好感 {fv}/200（{friend_tier(fv)}）")
    return "\n".join(lines)


def friend_tier(f):
    """好友档位：-300死敌 ~ 200夫妻"""
    if f >= 100:
        return "💍 挚友(可求婚)"
    if f >= 80:
        return "💖 挚友"
    if f >= 50:
        return "🤝 熟人/朋友"
    if f > 0:
        return "🌫 陌生人"
    if f > -100:
        return "🙁 不和"
    if f > -200:
        return "😠 仇人"
    return "💀 死敌"


def friend_clamp(v):
    """好感范围：-300 ~ +200"""
    return max(-300, min(200, v))


def friend_gain(p, base=2.0):
    """好感提升：100 后提升大幅减缓（×0.25）；夫妻（spouse）提升加快（2倍）"""
    fid = p.get("spouse")
    if fid and p["friend"].get(fid, 0) >= 100:
        return base * 2
    if p["friend"].get(fid, 0) >= 100:
        return base * 0.25
    return base


def spend(p, cost):
    """消费函数：夫妻（已婚）花金币项目全部打 8 折"""
    if p.get("spouse"):
        return int(cost * 0.8)
    return cost


def total_stats(p):
    return p.get("str",5) + p.get("dex",5) + p.get("int",5) + p.get("con",5) + p.get("luk",5)


def cmd_rank(state, uid, name, args):
    ps = sorted(state["players"].values(), key=lambda x: -total_stats(x))
    if not ps:
        return "小镇还没有玩家，第一个创建角色的人会成为传说喵～"
    lines = ["【🏆 综合能力排行榜】"]
    for i, pp in enumerate(ps[:5], 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        lines.append(f"{medal} {pp['name']}：总属性 {total_stats(pp)}（力{pp.get('str',5)} 敏{pp.get('dex',0)} 智{pp.get('int',5)} 体{pp.get('con',0)} 幸{pp.get('luk',0)}）")
    return "\n".join(lines)


def cmd_rich(state, uid, name, args):
    ps = sorted(state["players"].values(), key=lambda x: -(x["money"] + x.get("bank", 0)))
    if not ps:
        return "小镇还没有玩家喵～"
    lines = ["【💰 金钱富豪榜】"]
    for i, pp in enumerate(ps[:5], 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        total = pp["money"] + pp.get("bank", 0)
        lines.append(f"{medal} {pp['name']}：现金 {pp['money']} + 存款 {pp.get('bank', 0)} = {total} 金币")
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
    dex = p.get("dex", 5)
    steal_rate = min(0.70, 0.10 + dex * 0.004)  # 敏捷提高成功率（初始10%，上限70%）
    if random.random() < steal_rate:
        # 偷取比例与敏捷挂钩：10%~20% 基础 + DEX×0.2%/点，上限 70%
        steal_pct = min(0.70, random.uniform(0.10, 0.20) + dex * 0.002)
        stolen = max(1, int(other["money"] * steal_pct))
        other["money"] -= stolen
        p["money"] += stolen
        save_state(state)
        return (f"🕶 你偷偷摸走了【{other['name']}】的 {stolen} 金币！（偷走对方 {int(steal_pct*100)}%，敏捷加持）\n"
                f"神不知鬼不觉……目前没人发现喵～（花了15精力）")
    else:
        p["scene"] = "警察局"
        p["jail_until"] = time.time() + random.randint(60, 300)
        p["crime"] = p.get("crime", 0) + 1
        jail_min = int((p["jail_until"] - time.time()) // 60)
        jail_sec = int((p["jail_until"] - time.time()) % 60)
        other["friend"][uid] = friend_clamp(other["friend"].get(uid, 0) - 10)
        p["friend"][fid] = friend_clamp(p["friend"].get(fid, 0) - 10)
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
    p["friend"][fid] = friend_clamp(p["friend"].get(fid, 0) - 6)
    other["friend"][uid] = friend_clamp(other["friend"].get(uid, 0) - 6)
    my_str = p.get("str", 5)
    foe_str = other.get("str", 5)
    hit_rate = min(0.85, 0.5 + (my_str - foe_str) * 0.01 + my_str * 0.002)  # 力量差决定胜负
    if random.random() < hit_rate:
        other["energy"] = max(0, other["energy"] - 20)
        other["last"] = time.time()
        save_state(state)
        return (f"👊 你一拳命中【{other['name']}】！（力量压制）\n"
                f"{other['name']} 被揍掉 20 精力，灰溜溜去疗伤了！好感 -3 喵～")
    else:
        p["energy"] = max(0, p["energy"] - 20)
        save_state(state)
        return (f"💥 你冲上去反被【{other['name']}】一顿暴揍！（对方力量更强）\n"
                f"你掉了 20 精力，灰溜溜去疗伤了！好感 -3 喵～")


def cmd_give_toy(state, uid, name, args):
    """送娃娃：对方好感 +2"""
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if p.get("toys", 0) <= 0:
        return "你还没有娃娃喵～去机厅「抓娃娃」碰碰运气吧喵～"
    if not args:
        return "想把娃娃送给谁？输入「送娃娃 玩家名」喵～"
    other = find_player(state, p, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    if other is p:
        return "……送娃娃给自己？那娃娃本来就是你的喵～"
    if other["scene"] != p["scene"]:
        return f"【{other['name']}】不在你身边喵～送娃娃得当面送喵～"
    fid = [k for k, v in state["players"].items() if v is other][0]
    p["toys"] -= 1
    g1 = friend_gain(p, 5)
    g2 = friend_gain(other, 5)
    p["friend"][fid] = friend_clamp(p["friend"].get(fid, 0) + g1)
    other["friend"][uid] = friend_clamp(other["friend"].get(uid, 0) + g2)
    p["last"] = time.time()
    save_state(state)
    return (f"🧸 你把手里的娃娃塞给了【{other['name']}】！\n"
            f"你俩互相 +{g1:g}/+{g2:g} 好感（你对TA：{p['friend'][fid]:g}/200，TA对你：{other['friend'][uid]:g}/200）喵～")


def cmd_propose(state, uid, name, args):
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    if not args:
        return "想向谁求婚？输入「求婚 玩家名」喵～（双方好感都需≥100且为异性喵）"
    other = find_player(state, p, args[0])
    if not other:
        return f"没找到叫【{args[0]}】的玩家喵～"
    if other is p:
        return "……向自己求婚？你这是要自恋到什么程度喵～"
    if other["scene"] != p["scene"]:
        return f"【{other['name']}】不在你身边喵～求婚得当面求喵～"
    if p.get("spouse"):
        return "你已经结婚啦，再求婚可是重婚罪喵！"
    if other.get("spouse"):
        return f"【{other['name']}】已经有配偶了喵～"
    if p.get("gender") == other.get("gender"):
        return "本喵不支持同性结婚设定喵～（目前仅限异性喵）"
    fid = [k for k, v in state["players"].items() if v is other][0]
    my_friend = p["friend"].get(fid, 0)
    their_friend = other["friend"].get(uid, 0)
    if my_friend < 100 or their_friend < 100:
        return (f"双方好感都需达到 100 才能求婚喵～\n"
                f"你对【{other['name']}】：{my_friend}/200；TA对你：{their_friend}/200")
    if other.get("pending") and other["pending"].get("kind") == "propose":
        return f"【{other['name']}】已经有一个求婚请求在等TA回复了喵～"
    other["pending"] = {"kind": "propose", "from": uid}
    save_state(state)
    return (f"💍 你单膝跪地，向【{other['name']}】求婚！\n"
            f"求婚请求已送达……等TA回复「同意」或「拒绝」喵～")


def cmd_accept(state, uid, name, args):
    """接受求婚请求"""
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    pending = p.get("pending")
    if not pending or pending.get("kind") != "propose":
        return "现在没有待接受的求婚请求喵～"
    from_uid = pending["from"]
    suitor = state["players"].get(from_uid)
    if not suitor:
        p["pending"] = None
        save_state(state)
        return "求婚的人已经不在小镇了喵～"
    if p.get("spouse") or suitor.get("spouse"):
        p["pending"] = None
        save_state(state)
        return "你们其中有人已经有配偶了喵～（请求已撤销）"
    p["spouse"] = from_uid
    suitor["spouse"] = uid
    p["friend"][from_uid] = 200
    suitor["friend"][uid] = 200
    p["pending"] = None
    save_state(state)
    return (f"💍💍 你答应了【{suitor['name']}】的求婚！！\n"
            f"🎉 恭喜【{suitor['name']}】与【{p['name']}】结为夫妻！好感度直达 200/200，夫妻互动好感加倍喵～")


def cmd_reject(state, uid, name, args):
    """拒绝求婚请求"""
    p = get_player(state, uid)
    if not p:
        return "你还没创建角色呢，输入「创建角色 名字」加入小镇喵～"
    pending = p.get("pending")
    if not pending or pending.get("kind") != "propose":
        return "现在没有待拒绝的求婚请求喵～"
    from_uid = pending["from"]
    suitor = state["players"].get(from_uid)
    p["pending"] = None
    save_state(state)
    if suitor:
        return f"💔 你婉拒了【{suitor['name']}】的求婚……TA默默收起了戒指喵～"
    return "💔 你拒绝了求婚请求喵～"


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
        "· 创建角色 名字 男/女 —— 加入小镇（需选择性别）\n"
        "· 状态 / 地图 / 排行榜 / 富豪榜 / 关系\n"
        "· 属性：力量STR(打架/反制) 敏捷DEX(偷窃) 智力INT(打工收益/恢复) 体质CON(体力上限) 幸运LUK(暂无法提升)\n"
        "· 去 场景名 —— 移动（世纪联华/机厅/星巴克/KFC/小吃店/公寓/学校/警察局/银行/麻将馆）\n"
        "· 互动 —— 查看NPC互动菜单；聊天/帮忙/谈心 NPC名 皆可刷好感\n"
        "· 做 动作 —— 玩街机/学习/休息/吃喝等\n"
        "· 打工 —— 在当前场景赚钱\n"
        "· 存钱 金额 / 取钱 金额 —— 在银行存钱防偷，每24小时结算利息（-1%~+5%真随机）\n"
        "· 偷 玩家名 / 殴打 玩家名 —— 干坏事，失败会被抓去警察局坐牢（1~5分钟随机）⛓\n"
        "· 打招呼 玩家名 / 转账 玩家名 金额 —— 玩家互动（需同场景，好感0~200，50熟人/80挚友）\n"
        "· 求婚 玩家名 —— 好感≥100且异性可求婚，成功结为夫妻（互动好感翻倍）\n"
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
        "互动": "npc_menu", "互动菜单": "npc_menu",
        "聊天": "chat", "chat": "chat", "闲聊": "chat",
        "帮忙": "help_npc", "帮": "help_npc", "help_npc": "help_npc", "任务": "help_npc",
        "谈心": "talk", "talk": "talk", "倾诉": "talk",
        "选": "choose", "选择": "choose", "choose": "choose",
        "活动": "act", "act": "act", "能做": "act",
        "做": "do", "do": "do",
        "打工": "work", "work": "work", "上班": "work",
        "休息": "rest_cmd", "rest": "rest_cmd", "睡觉": "rest_cmd", "躺平": "rest_cmd",
        "舞萌": "maimai", "maimai": "maimai", "乌蒙": "maimai", "萌": "maimai",
        "推币机": "coin", "推币": "coin", "coin": "coin",
        "抓娃娃": "claw", "娃娃机": "claw", "claw": "claw",
        "送娃娃": "give_toy", "give_toy": "give_toy", "送玩偶": "give_toy",
        "学习": "study", "study": "study",
        "玩街机": "play", "play": "play", "玩游戏": "play",
        "打麻将": "mahjong", "麻将": "mahjong", "打牌": "mahjong", "mahjong": "mahjong",
        "吃": "eat", "eat": "eat", "吃东西": "eat",
        "打招呼": "hi", "hi": "hi", "hello": "hi",
        "偷": "steal", "偷钱": "steal", "steal": "steal", "盗窃": "steal",
        "殴打": "fight", "打架": "fight", "揍": "fight", "fight": "fight", "打人": "fight",
        "转账": "transfer", "transfer": "transfer", "给钱": "transfer",
        "关系": "rel", "rel": "rel", "好感": "rel",
        "求婚": "propose", "propose": "propose", "结婚": "propose", "嫁": "propose", "娶": "propose",
        "同意": "accept", "accept": "accept", "答应": "accept", "我愿意": "accept", "愿意": "accept",
        "拒绝": "reject", "reject": "reject", "不答应": "reject", "不嫁": "reject",
        "存钱": "deposit", "deposit": "deposit", "存款": "deposit",
        "取钱": "withdraw", "withdraw": "withdraw", "取款": "withdraw",
        "查账": "account", "账户": "account", "account": "account", "查看账户": "account",
        "发放": "grant", "grant": "grant", "发钱": "grant", "发金币": "grant",
        "扣除": "deduct", "deduct": "deduct", "扣钱": "deduct",
        "关押": "imprison", "imprison": "imprison", "抓人": "imprison",
        "释放": "release", "release": "release", "放人": "release", "特赦": "release",
        "公告": "announce", "announce": "announce", "广播": "announce",
        "查玩家": "view", "view": "view", "查看玩家": "view", "档案": "view",
        "排行榜": "rank", "rank": "rank", "综合榜": "rank", "能力榜": "rank",
        "富豪榜": "rich", "rich": "rich", "金钱榜": "rich", "财富榜": "rich",
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
            # 休息（睡觉）限制：睡觉中不能动、不能移动、不能交互
            if p.get("rest_until") and time.time() < p["rest_until"]:
                remain = int(p["rest_until"] - time.time())
                save_state(state)
                print(f"🛏 你正在睡觉……还剩 {remain // 60} 分 {remain % 60} 秒，睡觉中不能动喵～")
                return

    # 睡觉中额外禁止的命令（玩家交互/求婚/谈心等）
    sleep_restricted = {"act", "npc_menu", "talk", "choose", "help_npc",
                        "propose", "accept", "reject"}
    if cmd in sleep_restricted:
        p = get_player(state, uid)
        if p and p.get("rest_until") and time.time() < p["rest_until"]:
            remain = int(p["rest_until"] - time.time())
            save_state(state)
            print(f"🛏 你正在睡觉……还剩 {remain // 60} 分 {remain % 60} 秒，睡觉中不能交互喵～")
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
        "rest_cmd": cmd_rest, "give_toy": cmd_give_toy,
        "propose": cmd_propose, "accept": cmd_accept, "reject": cmd_reject,
        "npc_menu": cmd_npc_menu, "help_npc": cmd_help_npc, "talk": cmd_talk, "choose": cmd_choose,
        "rel": cmd_rel, "rank": cmd_rank, "rich": cmd_rich, "help": cmd_help,
    }

    if cmd == "study":
        cmd = "do"
        args = ["学习"]
    elif cmd == "play":
        cmd = "do"
        args = ["玩街机"]
    elif cmd == "mahjong":
        cmd = "do"
        args = ["打麻将"]
    elif cmd == "maimai":
        cmd = "do"
        args = ["舞萌"] + args
    elif cmd == "coin":
        cmd = "do"
        args = ["推币机"]
    elif cmd == "claw":
        cmd = "do"
        args = ["抓娃娃"]
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
