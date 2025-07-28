import json
import random
import asyncio
from pathlib import Path
from datetime import datetime
import aiohttp

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("cdk_distributor", "YourName", "CDK 分发系统 (CDKDistributor) 插件", "1.0.0", "")
class CdkDistributor(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.plugin_dir = Path(__file__).parent
        self.data_dir = self.plugin_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / "cdk_data.json"
        self._lock = asyncio.Lock()
        self.data = self._load_data()

    def _load_data(self):
        if not self.data_file.exists():
            return {}
        try:
            return json.loads(self.data_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"加载CDK数据失败: {e}")
            return {}

    def _save_data(self):
        try:
            self.data_file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"保存CDK数据失败: {e}")

    @filter.command("cdk")
    async def cdk(self, event: AstrMessageEvent):
        parts = event.message_str.strip().split()
        if len(parts) < 2:
            yield event.plain_result("用法: /cdk <new|add|config|details|claim|help> ...")
            return
        sub = parts[1]
        if sub == "help":
            yield event.plain_result(
                "CDK命令用法:\n"
                "/cdk new <cdk_id> <raw_url> [allow_duplicate] [shuffle] [overwrite] [max_per_user] [name]\n"
                "/cdk add <cdk_id> <raw_url> [shuffle] [overwrite]\n"
                "/cdk config <cdk_id> [allow_duplicate] [max_per_user] [name]\n"
                "/cdk details <cdk_id>\n"
                "/cdk claim <cdk_id> [num]"
            )
            return
        if sub == "claim":
            async for res in self.claim(event):
                yield res
            return
        if not event.is_private_chat() or not event.is_admin():
            yield event.plain_result("此指令仅限管理员私聊使用。")
            return
        async with self._lock:
            if sub == "new":
                async for res in self._cmd_new(event, parts[2:]):
                    yield res
            elif sub == "add":
                async for res in self._cmd_add(event, parts[2:]):
                    yield res
            elif sub == "config":
                async for res in self._cmd_config(event, parts[2:]):
                    yield res
            elif sub == "details":
                async for res in self._cmd_details(event, parts[2:]):
                    yield res
            else:
                yield event.plain_result(f"未知子指令: {sub}")
            self._save_data()

    async def _fetch_cdk_list(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return None
                    text = await resp.text()
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    return lines
        except Exception as e:
            logger.error(f"获取CDK列表失败: {e}")
            return None

    async def _cmd_new(self, event, args):
        if len(args) < 2:
            yield event.plain_result("用法: /cdk new <cdk_id> <raw_url> [allow_duplicate] [shuffle] [overwrite] [max_per_user] [name]")
            return
        cdk_id, url = args[0], args[1]
        allow_duplicate = args[2].lower() == "true" if len(args) > 2 else False
        shuffle = args[3].lower() == "true" if len(args) > 3 else False
        overwrite = args[4].lower() == "true" if len(args) > 4 else False
        max_per_user = int(args[5]) if len(args) > 5 else 1
        name = args[6] if len(args) > 6 else cdk_id

        if cdk_id in self.data and not overwrite:
            yield event.plain_result("CDK ID已存在。如需覆盖请使用 overwrite=true。")
            return
        lines = await self._fetch_cdk_list(url)
        if lines is None:
            yield event.plain_result("获取CDK列表失败，请检查URL。")
            return
        if shuffle:
            random.shuffle(lines)
        items = [{"code": code, "used": False, "user": "", "time": ""} for code in lines]
        self.data[cdk_id] = {
            "name": name,
            "allow_duplicate": allow_duplicate,
            "max_per_user": max_per_user,
            "items": items,
            "user_records": {}
        }
        yield event.plain_result(f"已创建CDK分发 {cdk_id}，总数: {len(items)}。")

    async def _cmd_add(self, event, args):
        if len(args) < 2:
            yield event.plain_result("用法: /cdk add <cdk_id> <raw_url> [shuffle] [overwrite]")
            return
        cdk_id, url = args[0], args[1]
        shuffle = args[2].lower() == "true" if len(args) > 2 else False
        overwrite = args[3].lower() == "true" if len(args) > 3 else False

        if cdk_id not in self.data:
            yield event.plain_result("CDK ID不存在。")
            return
        lines = await self._fetch_cdk_list(url)
        if lines is None:
            yield event.plain_result("获取CDK列表失败，请检查URL。")
            return
        if shuffle:
            random.shuffle(lines)
        new_items = [{"code": code, "used": False, "user": "", "time": ""} for code in lines]
        if overwrite:
            self.data[cdk_id]["items"] = new_items
        else:
            self.data[cdk_id]["items"].extend(new_items)
        yield event.plain_result(f"CDK {cdk_id} 更新完成，总数: {len(self.data[cdk_id]['items'])}。")

    async def _cmd_config(self, event, args):
        if len(args) < 1:
            yield event.plain_result("用法: /cdk config <cdk_id> [allow_duplicate] [max_per_user] [name]")
            return
        cdk_id = args[0]
        if cdk_id not in self.data:
            yield event.plain_result("CDK ID不存在。")
            return
        if len(args) > 1:
            self.data[cdk_id]["allow_duplicate"] = args[1].lower() == "true"
        if len(args) > 2:
            self.data[cdk_id]["max_per_user"] = int(args[2])
        if len(args) > 3:
            self.data[cdk_id]["name"] = args[3]
        yield event.plain_result(f"CDK {cdk_id} 配置已更新。")

    async def _cmd_details(self, event, args):
        if len(args) < 1:
            yield event.plain_result("用法: /cdk details <cdk_id>")
            return
        cdk_id = args[0]
        if cdk_id not in self.data:
            yield event.plain_result("CDK ID不存在。")
            return
        info = self.data[cdk_id]
        total = len(info["items"])
        used = sum(1 for i in info["items"] if i["used"])
        unused = total - used
        claimed = used
        yield event.plain_result(
            f"名称: {info['name']}\nID: {cdk_id}\n总数: {total}\n剩余: {unused}\n已领取: {claimed}\n每人上限: {info['max_per_user']}\n允许重复: {info['allow_duplicate']}"
        )

    @filter.command("claim")
    async def claim(self, event: AstrMessageEvent):
        parts = event.message_str.strip().split()
        if len(parts) < 2:
            yield event.plain_result("用法: /claim <cdk_id> [num]")
            return
        cdk_id = parts[1]
        num = int(parts[2]) if len(parts) > 2 else 1
        async with self._lock:
            if cdk_id not in self.data:
                yield event.plain_result("CDK不存在。")
                return
            info = self.data[cdk_id]
            items = info["items"]
            unused_items = [i for i in items if not i["used"]]
            if not unused_items:
                yield event.plain_result("CDK已领完。")
                return
            user = event.get_sender_id()
            record = info["user_records"].get(user, 0)
            if record >= info["max_per_user"] and not info["allow_duplicate"]:
                yield event.plain_result("您已达到领取上限。")
                return
            allow = info["max_per_user"] - record if not info["allow_duplicate"] else num
            take = min(num, allow)
            selected = unused_items[:take]
            codes = [i["code"] for i in selected]
            for item in selected:
                item["used"] = True
                item["user"] = user
                item["time"] = datetime.utcnow().isoformat()
            info["user_records"][user] = record + take
            self._save_data()
        for code in codes:
            yield event.plain_result(f"您的CDK: {code}")
