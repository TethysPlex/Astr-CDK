
# 插件开发

少行代码，高效开发！

> [!TIP]
> * 推荐使用 VSCode。
> * 需具备 Python、Git 基础。
> 欢迎加群 `975206796` 讨论！

## 开发环境

### 获取插件模板

1.  AstrBot 插件模板: [helloworld](https://github.com/Soulter/helloworld)
2.  点击 `Use this template` -> `Create new repository`。
3.  `Repository name` 填插件名：
    *   推荐 `astrbot_plugin_` 前缀。
    *   无空格。
    *   全小写。
    *   尽量简短。
4.  点击 `Create repository`。

### Clone 项目与插件

```bash
git clone https://github.com/AstrBotDevs/AstrBot
mkdir -p AstrBot/data/plugins
cd AstrBot/data/plugins
git clone <插件仓库地址>
```

用 VSCode 打开 `AstrBot` 项目，进入 `data/plugins/<你的插件名字>`。
更新 `metadata.yaml` 填写插件元数据（用于市场展示）。

### 调试

AstrBot 运行时注入插件。调试需启动 AstrBot 本体。
插件代码修改后，在 WebUI 插件管理处，点击 `管理` -> `重载插件`。

### 插件依赖

使用 `requirements.txt` 管理依赖。插件目录下创建 `requirements.txt`，列出所需第三方库，防 `Module Not Found`。
(`requirements.txt` 格式: [pip 官方文档](https://pip.pypa.io/en/stable/reference/requirements-file-format/))

## 提要

### 最小实例

`main.py` 是最小插件实例：

```python
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger # 使用 astrbot logger

@register("helloworld", "author", "一个简单的 Hello World 插件", "1.0.0", "repo url")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("helloworld") # 指令: /helloworld
    async def helloworld(self, event: AstrMessageEvent):
        '''这是一个 hello world 指令''' # handler 描述，建议填写
        user_name = event.get_sender_name()
        message_str = event.message_str # 消息纯文本
        logger.info("触发hello world指令!")
        yield event.plain_result(f"Hello, {user_name}!") # 发送纯文本消息

    async def terminate(self):
        '''可选实现。插件卸载/停用时调用。'''
```

**说明**:
*   插件类继承 `Star`。
*   `@register` 装饰器注册插件，提供元数据 (优先级低于 `metadata.yaml`)。
*   `__init__` 接收 `Context` 对象，包含 AstrBot 组件。
*   `Handler` 在插件类中定义 (如 `helloworld` 函数)。
*   日志使用 `from astrbot.api import logger`。
*   `Handler` 必须在插件类中，前两个参数为 `self`, `event`。
*   插件类文件名为 `main.py`。

### API 文件结构

`astrbot/api` 目录包含所有 API。

```
api
├── __init__.py
├── all.py # 导入所有结构
├── event
│   └── filter # 过滤器，事件钩子
├── message_components.py # 消息段类型
├── platform # 平台相关结构
├── provider # 大语言模型提供商相关结构
└── star
```

### AstrMessageEvent

`AstrMessageEvent` 是 AstrBot 消息事件对象，用于获取发送者、消息内容等。

### AstrBotMessage

`AstrBotMessage` 是 AstrBot 消息对象 (`event.message_obj` 获取)，包含适配器下发消息详情。

```py
class AstrBotMessage:
    type: MessageType  # 消息类型
    self_id: str  # 机器人ID
    session_id: str  # 会话ID
    message_id: str  # 消息ID
    group_id: str = "" # 群组ID，私聊为空
    sender: MessageMember  # 发送者
    message: List[BaseMessageComponent]  # 消息链: [Plain("Hello"), At(qq=123456)]
    message_str: str  # 纯文本消息字符串
    raw_message: object # 平台适配器原始消息对象
    timestamp: int  # 消息时间戳
```

### 消息链

消息链是消息结构的有序列表，每项为`消息段`。
`import astrbot.api.message_components as Comp`

**示例**: `[Comp.Plain(text="Hello"), Comp.At(qq=123456), Comp.Image(file="https://example.com/image.jpg")]`
(QQ为平台用户ID)

**消息类型 (基于 `nakuru-project`)**:
```py
ComponentTypes = {
    "plain": Plain,     # 文本
    "text": Plain,      # 文本
    "face": Face,       # QQ表情
    "record": Record,   # 语音
    "video": Video,     # 视频
    "at": At,           # @消息发送者
    "music": Music,     # 音乐
    "image": Image,     # 图片
    "reply": Reply,     # 回复消息
    "forward": Forward, # 转发消息
    "node": Node,       # 转发消息节点
    "nodes": Nodes,     # Node列表
    "poke": Poke,       # 戳一戳
}
```
**调试消息结构**:
```python
@event_message_type(EventMessageType.ALL)
async def on_message(self, event: AstrMessageEvent):
    print(event.message_obj.raw_message) # 原始消息
    print(event.message_obj.message)     # 解析后消息链
```

### 平台适配矩阵

支持平台与消息类型对应关系：

| 平台             | At  | Plain | Image | Record | Video | Reply | 主动消息 |
| :--------------- | :-- | :---- | :---- | :----- | :---- | :---- | :------- |
| QQ 个人号 (aiocqhttp) | ✅  | ✅    | ✅    | ✅     | ✅    | ✅    | ✅       |
| Telegram         | ✅  | ✅    | ✅    | ✅     | ✅    | ✅    | ✅       |
| QQ 官方接口      | ❌  | ✅    | ✅    | ❌     | ❌    | ❌    | ❌       |
| 飞书             | ✅  | ✅    | ✅    | ❌     | ❌    | ✅    | ✅       |
| 企业微信         | ❌  | ✅    | ✅    | ✅     | ❌    | ❌    | ❌       |
| 钉钉             | ❌  | ✅    | ✅    | ❌     | ❌    | ❌    | ❌       |

*   **QQ 个人号**: 支持 `Poke`, `Node(s)` (合并转发)。
*   **QQ 官方接口/钉钉**: 发送消息强制带 `At`。
*   **钉钉图片**: 仅支持 HTTP 链接。
*   **主动消息**: 机器人主动发送的消息。([发送消息](#发送消息))

## 插件开发原则

良好贡献与习惯：
1.  **功能测试**: 确保功能经过测试。
2.  **注释完备**: 代码包含良好注释。
3.  **数据持久化**: 数据存 `data` 目录，防更新/重装覆盖。
4.  **错误处理**: 良好错误处理，防崩溃。
5.  **代码格式**: 提交前使用 [ruff](https://docs.astral.sh/ruff/) 格式化代码。
6.  **异步网络**: 使用 `aiohttp`, `httpx` 等异步库，勿用 `requests`。
7.  **功能扩增**: 优先向原插件提交 PR，除非原作者停更。

## 开发指南

> [!CAUTION]
> 所有处理函数都必须写在插件类中。

### 事件监听器

接收平台消息，实现指令、指令组、事件监听。
注册器在 `astrbot.api.event.filter` 下，务必导入。
`from astrbot.api.event import filter, AstrMessageEvent`

#### 注册指令

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("helloworld", "Soulter", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        '''这是 hello world 指令'''
        user_name = event.get_sender_name()
        message_str = event.message_str
        yield event.plain_result(f"Hello, {user_name}!")
```
**注意**: 指令不能带空格。

#### 注册带参数指令

AstrBot 自动解析指令参数。
```python
@filter.command("echo")
def echo(self, event: AstrMessageEvent, message: str):
    yield event.plain_result(f"你发了: {message}")

@filter.command("add")
def add(self, event: AstrMessageEvent, a: int, b: int):
    # /add 1 2 -> 结果是: 3
    yield event.plain_result(f"结果是: {a + b}")
```

#### 注册指令组

组织指令。
```python
@filter.command_group("math")
def math(self):
    pass # 组函数体可为空或注释

@math.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    # /math add 1 2 -> 结果是: 3
    yield event.plain_result(f"结果是: {a + b}")

@math.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    # /math sub 1 2 -> 结果是: -1
    yield event.plain_result(f"结果是: {a - b}")
```
子指令使用 `指令组名.command` 注册。用户未输入子指令时，报错并展示组结构。
指令组可无限嵌套：
```py
'''
math
├── calc
│   ├── add (a(int),b(int),)
│   ├── sub (a(int),b(int),)
│   ├── help (无参数指令)
'''

@filter.command_group("math")
def math(): pass

@math.group("calc") # 注意: group 非 command_group
def calc(): pass

@calc.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")

@calc.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a - b}")

@calc.command("help")
def calc_help(self, event: AstrMessageEvent):
    # /math calc help
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

#### 指令/指令组别名 (v3.4.28+)
```python
@filter.command("help", alias={'帮助', 'helpme'})
def help(self, event: AstrMessageEvent):
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

#### 群/私聊事件监听器

```python
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def on_private_message(self, event: AstrMessageEvent):
    message_str = event.message_str
    yield event.plain_result("收到了一条私聊消息。")
```
`EventMessageType`: `Enum` 类型，包含 `PRIVATE_MESSAGE`, `GROUP_MESSAGE`。

#### 接收所有消息事件
```python
@filter.event_message_type(filter.EventMessageType.ALL)
async def on_all_message(self, event: AstrMessageEvent):
    yield event.plain_result("收到了一条消息。")
```

#### 只接收特定消息平台事件
```python
@filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP | filter.PlatformAdapterType.QQOFFICIAL)
async def on_aiocqhttp(self, event: AstrMessageEvent):
    '''只接收 AIOCQHTTP 和 QQOFFICIAL 的消息'''
    yield event.plain_result("收到了一条信息")
```
`PlatformAdapterType`: `AIOCQHTTP`, `QQOFFICIAL`, `GEWECHAT`, `ALL`。

### 限制管理员使用指令
```python
@filter.permission_type(filter.PermissionType.ADMIN)
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    pass
```
仅管理员可使用 `test`。

#### 多个过滤器
支持多过滤器，`AND` 逻辑 (所有过滤器通过才执行)。
```python
@filter.command("helloworld")
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("你好！")
```

### 事件钩子 [New]
> [!TIP]
> 事件钩子不与 `@filter.command`, `@filter.command_group`, `@filter.event_message_type`, `@filter.platform_adapter_type`, `@filter.permission_type` 同时使用。

#### AstrBot 初始化完成时 (v3.4.34+)
```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_astrbot_loaded()
async def on_astrbot_loaded(self):
    print("AstrBot 初始化完成")
```

#### 收到 LLM 请求时
调用 LLM 前触发 `on_llm_request`，可修改 `ProviderRequest` 对象。
```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import ProviderRequest

@filter.on_llm_request()
async def my_custom_hook_1(self, event: AstrMessageEvent, req: ProviderRequest): # 三参数
    print(req) # 打印请求文本
    req.system_prompt += "自定义 system_prompt"
```
*不可 `yield` 发送消息，请用 `event.send()`*。

#### LLM 请求完成时
LLM 请求后触发 `on_llm_response`，可修改 `ProviderResponse` 对象。
```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import LLMResponse

@filter.on_llm_response()
async def on_llm_resp(self, event: AstrMessageEvent, resp: LLMResponse): # 三参数
    print(resp)
```
*不可 `yield` 发送消息，请用 `event.send()`*。

#### 发送消息给适配器前
发送消息前触发 `on_decorating_result`，可实现消息装饰 (转语音、图片、加前缀等)。
```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_decorating_result()
async def on_decorating_result(self, event: AstrMessageEvent):
    result = event.get_result()
    chain = result.chain
    print(chain) # 打印消息链
    chain.append(Plain("!")) # 消息链末尾加感叹号
```
*不可 `yield` 发送消息，仅装饰 `event.get_result().chain`。如需发送，请用 `event.send()`*。

#### 发送消息给适配器后
消息发送给平台后触发 `after_message_sent`。
```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.after_message_sent()
async def after_message_sent(self, event: AstrMessageEvent):
    pass
```
*不可 `yield` 发送消息，请用 `event.send()`*。

### 优先级 (v3.4.21+)
指令、监听器、钩子可设置优先级。默认 `0`。
```python
@filter.command("helloworld", priority=1)
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
```

### 会话控制 [NEW] (v3.4.36+)
用于多轮对话 (如成语接龙)。
**导入**:
```py
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionController,
)
```
**Handler 示例**:
```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("成语接龙")
async def handle_empty_mention(self, event: AstrMessageEvent):
    """成语接龙具体实现"""
    try:
        yield event.plain_result("请发送一个成语~")

        @session_waiter(timeout=60, record_history_chains=False)
        async def empty_mention_waiter(controller: SessionController, event: AstrMessageEvent):
            idiom = event.message_str

            if idiom == "退出":
                await event.send(event.plain_result("已退出成语接龙~"))
                controller.stop()
                return

            if len(idiom) != 4:
                await event.send(event.plain_result("成语必须是四个字的呢~"))
                return

            message_result = event.make_result()
            message_result.chain = [Comp.Plain("先见之明")]
            await event.send(message_result)

            controller.keep(timeout=60, reset_timeout=True)

        try:
            await empty_mention_waiter(event)
        except TimeoutError:
            yield event.plain_result("你超时了！")
        except Exception as e:
            yield event.plain_result("发生错误: " + str(e))
        finally:
            event.stop_event()
    except Exception as e:
        logger.error("handle_empty_mention error: " + str(e))
```
激活会话控制器后，该发送人后续消息优先由 `empty_mention_waiter` 处理，直到会话停止或超时。

#### SessionController
控制会话结束与获取历史消息链。
*   `keep(timeout: float, reset_timeout: bool)`: 保持会话。
    *   `timeout`: 会话超时时间 (秒)。
    *   `reset_timeout`: `True` 重置超时 (timeout > 0)，`False` 延续原超时。
*   `stop()`: 立即结束会话。
*   `get_history_chains() -> List[List[Comp.BaseMessageComponent]]`: 获取历史消息链。

#### 自定义会话 ID 算子
默认以 `sender_id` 区分会话。如需以群组为会话，自定义 `SessionFilter`。
```py
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionFilter,
    SessionController,
)

class CustomFilter(SessionFilter):
    def filter(self, event: AstrMessageEvent) -> str:
        return event.get_group_id() if event.get_group_id() else event.unified_msg_origin

await empty_mention_waiter(event, session_filter=CustomFilter())
```
群内消息将被视为同一会话。

### 发送消息

基于 `yield` 的异步生成器可在函数中多次发送消息。
```python
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
    yield event.plain_result("你好！")
    yield event.image_result("path/to/image.jpg") # 发送图片
    yield event.image_result("https://example.com/image.jpg") # URL图片 (http/https 开头)
```

**主动消息**:
定时任务或非即时发送，用 `event.unified_msg_origin` 获取会话ID，存储后用 `self.context.send_message(umo, chains)` 发送。
```python
from astrbot.api.event import MessageChain

@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    umo = event.unified_msg_origin
    message_chain = MessageChain().message("Hello!").file_image("path/to/image.jpg")
    await self.context.send_message(umo, message_chain)
```
`unified_msg_origin` 是会话唯一ID，AstrBot 据此发送消息到正确会话。

### 发送图文等富媒体消息

用 `MessageChain` 构建消息。
```python
import astrbot.api.message_components as Comp

@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    chain = [
        Comp.At(qq=event.get_sender_id()),
        Comp.Plain("来看这个图："),
        Comp.Image.fromURL("https://example.com/image.jpg"),
        Comp.Image.fromFileSystem("path/to/image.jpg"),
        Comp.Plain("这是一个图片。")
    ]
    yield event.chain_result(chain)
```
构建消息链，发送包含图片和文字的有序消息。

**其他组件**:
*   **File**: `Comp.File(file="path/to/file.txt", name="file.txt")` (部分平台不支持)
*   **Record**: `Comp.Record(file="path/to/record.wav", url="path/to/record.wav")` (目前只支持 `.wav`)
*   **Video**: `Comp.Video.fromFileSystem(path="path/to/video.mp4")`, `Comp.Video.fromURL(url="https://example.com/video.mp4")`

### 发送群合并转发消息 (aiocqhttp)
```py
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Node, Plain, Image

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    node = Node(
        uin=905617992,
        name="Soulter",
        content=[Plain("hi"), Image.fromFileSystem("test.jpg")]
    )
    yield event.chain_result([node])
```

### 发送视频消息 (aiocqhttp)
```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Video

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    video_fs = Video.fromFileSystem(path="test.mp4") # requires bot and protocol in same system
    video_url = Video.fromURL(url="https://example.com/video.mp4") # more universal
    yield event.chain_result([video_url])
```

### 发送 QQ 表情 (仅 aiocqhttp)
QQ 表情 ID: [https://bot.q.qq.com/wiki/develop/api-v2/openapi/emoji/model.html#EmojiType](https://bot.q.qq.com/wiki/develop/api-v2/openapi/emoji/model.html#EmojiType)
```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Face, Plain

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    yield event.chain_result([Face(id=21), Plain("你好呀")])
```

### 获取平台适配器/客户端 (v3.4.34+)
```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.platform import AiocqhttpAdapter # Other platforms similar

@filter.command("test")
async def test_(self, event: AstrMessageEvent):
    platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
    assert isinstance(platform, AiocqhttpAdapter)
    # platform.get_client().api.call_action()
```

### [aiocqhttp] 调用协议端 API
```py
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    if event.get_platform_name() == "aiocqhttp":
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        assert isinstance(event, AiocqhttpMessageEvent)
        client = event.bot
        payloads = {"message_id": event.message_obj.message_id}
        ret = await client.api.call_action('delete_msg', **payloads)
        logger.info(f"delete_msg: {ret}")
```
CQHTTP API 参考: [Napcat](https://napcat.apifox.cn/), [Lagrange](https://lagrange-onebot.apifox.cn/)。

### [gewechat] 平台发送消息
```py
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    if event.get_platform_name() == "gewechat":
        from astrbot.core.platform.sources.gewechat.gewechat_platform_adapter import GewechatPlatformAdapter
        assert isinstance(event, GewechatPlatformEvent)
        client = event.client
        to_wxid = self.message_obj.raw_message.get('to_wxid', None)
        # await client.post_text()
        # await client.post_image()
        # await client.post_voice()
```

### 控制事件传播
```python
@filter.command("check_ok")
async def check_ok(self, event: AstrMessageEvent):
    ok = self.check()
    if not ok:
        yield event.plain_result("检查失败")
        event.stop_event() # 停止事件传播
```
`event.stop_event()` 阻止后续步骤 (其他插件 handler、LLM 请求等) 执行。

### 注册插件配置 (beta) (v3.4.15+)
允许用户通过管理面板配置插件，无需修改代码。

**Schema 介绍**:
在插件目录下添加 `_conf_schema.json`。内容为 `Schema` (JSON 格式)，例如：
```json
{
  "token": {
    "description": "Bot Token",
    "type": "string",
    "hint": "测试醒目提醒",
    "obvious_hint": true
  },
  "sub_config": {
    "description": "测试嵌套配置",
    "type": "object",
    "hint": "xxxx",
    "items": {
      "name": {
        "description": "testsub",
        "type": "string",
        "hint": "xxxx"
      },
      "id": {
        "description": "testsub",
        "type": "int",
        "hint": "xxxx"
      },
      "time": {
        "description": "testsub",
        "type": "int",
        "hint": "xxxx",
        "default": 123
      }
    }
  }
}
```
**字段说明**:
*   `type` (必填): `string`, `text`, `int`, `float`, `bool`, `object`, `list`。`text` 为大文本框。
*   `description` (可选): 配置描述。
*   `hint` (可选): 提示信息 (问号按钮悬浮显示)。
*   `obvious_hint` (可选): `hint` 是否醒目显示。
*   `default` (可选): 默认值 (int=0, float=0.0, bool=False, string="", object={}, list=[])。
*   `items` (可选): `object` 类型时需加此字段，为子 Schema。
*   `invisible` (可选): 是否隐藏，默认 `false`。
*   `options` (可选): 下拉列表可选项，如 `["chat", "agent"]`。
*   `editor_mode` (可选): `True` 启用代码编辑器模式 (v3.5.10+)。默认 `false`。
*   `editor_language` (可选): 代码语言，默认 `json`。
*   `editor_theme` (可选): 编辑器主题，`vs-light` (默认), `vs-dark`。

**使用配置**:
AstrBot 检测 `_conf_schema.json`，自动解析并保存到 `data/config/<plugin_name>_config.json`。实例化插件类时传入 `__init__()`。
```py
from astrbot.api import AstrBotConfig

@register("config", "Soulter", "一个配置示例", "1.0.0")
class ConfigPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig): # AstrBotConfig 继承自 Dict
        super().__init__(context)
        self.config = config
        print(self.config)
        # self.config.save_config() # 支持保存配置
```

**配置版本管理**:
Schema 更新时，AstrBot 自动为缺失项添加默认值。但不会删除配置文件中多余的配置项。

### 文字渲染成图片
```python
@filter.command("image")
async def on_aiocqhttp(self, event: AstrMessageEvent, text: str):
    url = await self.text_to_image(text) # text_to_image() is a Star method
    # path = await self.text_to_image(text, return_url = False) # save locally
    yield event.image_result(url)
```

### 自定义 HTML 渲染成图片
使用 `HTML + Jinja2` 模板渲染。
```py
# Custom Jinja2 template, supports CSS
TMPL = '''
<div style="font-size: 32px;">
<h1 style="color: black">Todo List</h1>

<ul>
{% for item in items %}
    <li>{{ item }}</li>
{% endfor %}
</div>
'''

@filter.command("todo")
async def custom_t2i_tmpl(self, event: AstrMessageEvent):
    url = await self.html_render(TMPL, {"items": ["吃饭", "睡觉", "玩原神"]}) # Second param: Jinja2 data
    yield event.image_result(url)
```
返回结果为图片。支持复杂设计，Jinja2 支持循环、条件等语法。

### 调用 LLM
通过 `self.context.get_using_provider()` 获取当前 LLM 提供商 (需启用)。
```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    func_tools_mgr = self.context.get_llm_tool_manager()
    curr_cid = await self.context.conversation_manager.get_curr_conversation_id(event.unified_msg_origin)
    conversation = None
    context = []
    if curr_cid:
        conversation = await self.context.conversation_manager.get_conversation(event.unified_msg_origin, curr_cid)
        context = json.loads(conversation.history)
    # curr_cid = await self.context.conversation_manager.new_conversation(event.unified_msg_origin) # New convo

    # Method 1: Low-level LLM call. No side effects (no func call, convo mgr)
    llm_response = await self.context.get_using_provider().text_chat(
        prompt="你好",
        session_id=None, # Deprecated
        contexts=[], # Can use 'context' from user's current conversation
        image_urls=[], # Image URLs (paths/network)
        func_tool=func_tools_mgr, # Enabled func tools. Optional.
        system_prompt=""  # Optional
    )
    # 'contexts' uses OpenAI format (auto-converted if using Gemini)
    # contexts = [ { "role": "system", "content": "你是一个助手。"}, { "role": "user", "content": "你好"} ]
    if llm_response.role == "assistant":
        print(llm_response.completion_text)
    elif llm_response.role == "tool":
        print(llm_response.tools_call_name, llm_response.tools_call_args)
    print(llm_response.raw_completion) # Raw LLM response (OpenAI format, includes tokens. Can be None)

    # Method 2: Through AstrBot's internal LLM processing. Auto-executes func tools, results sent to user.
    yield event.request_llm(
        prompt="你好",
        func_tool_manager=func_tools_mgr,
        session_id=curr_cid, # If specified, logs convo to DB
        contexts=context, # If not empty, uses this context for LLM
        system_prompt="",
        image_urls=[],
        conversation=conversation # If specified, logs convo
    )
```

### 注册 LLM 函数工具
为 LLM 提供 `function-calling` 能力。
**格式**:
```py
@filter.llm_tool(name="get_weather") # If name not provided, uses function name
async def get_weather(self, event: AstrMessageEvent, location: str) -> MessageEventResult:
    '''获取天气信息。

    Args:
        location(string): 地点
    '''
    resp = self.get_weather_from_api(location)
    yield event.plain_result("天气信息: " + resp)
```
`Args:` 格式: `param_name(type): description`。
支持类型: `string`, `number`, `object`, `array`, `boolean`。
> [!WARNING]
> 注释格式务必正确！

### 获取 AstrBot 配置
```py
config = self.context.get_config() # Dict-like. config['provider']
# config.save_config() # Save config
```

### 获取当前载入的所有提供商
```py
providers = self.context.get_all_providers()
providers_stt = self.context.get_all_stt_providers()
providers_tts = self.context.get_all_tts_providers()
```

### 获取当前使用提供商
```py
provider = self.context.get_using_provider() # None if not in use
provider_stt = self.context.get_using_stt_provider()
provider_tts = self.context.get_using_tts_provider()
```

### 通过提供商 ID 获取提供商
`self.context.get_provider_by_id(id_str)`

### 获取当前载入的所有插件
`plugins = self.context.get_all_stars()` (`StarMetadata` 包含实例、配置等)

### 获取函数调用管理器
`self.context.get_llm_tool_manager()` (返回 `FuncCall`)

### 注册异步任务
在 `__init__()` 中使用 `asyncio.create_task()`。
```py
import asyncio

@register("task", "Soulter", "一个异步任务示例", "1.0.0")
class TaskPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        asyncio.create_task(self.my_task())

    async def my_task(self):
        await asyncio.sleep(1)
        print("Hello")
```

### 获取载入的所有人格 (Persona)
`from astrbot.api.provider import Personality`
`personas = self.context.provider_manager.personas # List[Personality]`

### 获取默认人格
`self.context.provider_manager.selected_default_persona["name"]`

### 获取会话正在使用的对话
```py
from astrbot.core.conversation_mgr import Conversation
uid = event.unified_msg_origin
curr_cid = await self.context.conversation_manager.get_curr_conversation_id(uid)
conversation = await self.context.conversation_manager.get_conversation(uid, curr_cid) # Conversation
# context = json.loads(conversation.history)
# persona_id = conversation.persona_id
```
**注意**: 新对话 `persona_id` 为 `None`。`/persona unset` 设为 `[%None]` (防止与 `None` 默认人格冲突)。
获取默认人格 ID:
```py
if not conversation.persona_id and not conversation.persona_id == "[%None]":
    curr_persona_name = self.context.provider_manager.selected_default_persona["name"]
```

### 获取会话的所有对话
`from astrbot.core.conversation_mgr import Conversation`
`uid = event.unified_msg_origin`
`conversations = await self.context.conversation_manager.get_conversations(uid) # List[Conversation]`

### 获取加载的所有平台
`from astrbot.api.platform import Platform`
`platforms = self.context.platform_manager.get_insts() # List[Platform]`

---

下面讲解一些插件开发中使用到的 AstrBot 核心提供的类与数据资源, 文档中不会介绍类的所有的属性, 部分属性和方法不建议在插件中使用, 这部分内容不会在这里介绍。 文档中默认 self 是指该类的实例, 你可以在对应类内部的任何方法中使用这些资源, 注意文档中的所有方法都省略了 self 参数, 你需要使用self.属性名或self.方法名()进行调用。

---

## AstrMessageEvent

AstrBot 事件：运行核心，事件驱动。插件 Handler (async def) 是异步协程 (无 yield) 或异步生成器 (有 yield)，在消息管道中被调度器触发。大部分 Handler 需传入 `event: AstrMessageEvent`。

```Python
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    pass
```
此示例用于处理 `helloworld` 指令，需定义在插件类下。

### 属性

#### 消息
1.  `message_str(str)`: 纯文本消息。
2.  `message_obj(AstrBotMessage)`: 消息对象。
3.  `is_at_or_wake_command(bool)`: 是否 @机器人/带唤醒词/私聊。

#### 消息来源
4.  `role(str)`: 用户角色: `"member"` 或 `"admin"`。
5.  `platform_meta(PlatformMetadata)`: 消息平台信息。
6.  `session_id(str)`: 不含平台会话ID (QQ号/群号)。建议用 `unified_msg_origin`。
7.  `session(MessageSession)`: 会话对象，`unified_msg_origin` 为其字符串表示。
8.  `unified_msg_origin(str)`: 会话ID，格式: `platform_name:message_type:session_id`。

#### 事件控制
9.  `is_wake(bool)`: 机器人是否唤醒 (通过 WakingStage)。未唤醒不触发后续阶段。
10. `call_llm(bool)`: 是否禁止此消息事件的默认 LLM 请求。

### 方法

#### 消息相关
1.  `get_message_str() -> str`: 获取事件文本消息。等同于 `self.message_str`。
2.  `get_message_outline() -> str`: 获取消息概要，将其他消息类型转换为占位符 (如 `"[图片]"`)。
3.  `get_messages() -> List[BaseMessageComponent]`: 返回所有消息组件列表 (文本、图片等)。
4.  `get_message_type() -> MessageType`: 获取消息类型。
5.  `is_private_chat() -> bool`: 判断是否私聊触发。
6.  `is_admin() -> bool`: 判断是否管理员发出。等同于 `self.role == "admin"`。

#### 消息平台相关
7.  `get_platform_name() -> str`: 获取事件平台名称 (如 `"aiocqhttp"`)。等同于 `self.platform_meta.name`。

#### ID 相关
8.  `get_self_id() -> str`: 获取机器人自身ID。
9.  `get_sender_id() -> str`: 获取消息发送者ID。
10. `get_sender_name() -> str`: 获取消息发送者昵称 (可能为空)。
11. `get_group_id() -> str`: 获取群组ID (群号)，非群消息返回 `None`。

#### 会话控制相关
12. `get_session_id() -> str`: 获取当前会话ID (`platform_name:message_type:session_id`)。等同于 `self.session_id` 或 `self.session.session_id`。
13. `get_group(group_id: str = None, **kwargs) -> Optional[Group]`: 获取群聊数据。不填 `group_id` 默认返回当前群聊消息。私聊中不填返回 `None`。仅适配 `gewechat` 和 `aiocqhttp`。

#### 事件状态
14. `is_wake_up() -> bool`: 判断事件是否唤醒Bot。等同于 `self.is_wake`。
15. `stop_event()`: 终止事件传播，后续处理停止。
16. `continue_event()`: 继续事件传播。
17. `is_stopped() -> bool`: 判断事件是否已停止传播。

#### 事件结果
18. `set_result(result: Union[MessageEventResult, str])`: 设置消息事件结果 (Bot发送内容)。参数: `MessageEventResult` 或字符串。
19. `get_result() -> MessageEventResult`: 获取消息事件结果。
20. `clear_result()`: 清除消息事件结果。

#### LLM 相关
21. `should_call_llm(call_llm: bool)`: 设置是否禁止此消息事件的默认 LLM 请求 (不阻止插件内的 LLM 请求)。
22. `request_llm(prompt: str, func_tool_manager=None, session_id: str = None, image_urls: List[str] = [], contexts: List = [], system_prompt: str = "", conversation: Conversation = None) -> ProviderRequest`: 创建 LLM 请求。
    *   `prompt (str)`: 提示词。
    *   `func_tool_manager (FuncCall)`: 函数工具管理器。
    *   `session_id (str)`: 已过时，留空。
    *   `image_urls (List[str])`: 发送给 LLM 的图片 (base64/URL/本地路径)。
    *   `contexts (List)`: 使用此内容作为本次请求上下文 (非聊天记录)。
    *   `system_prompt (str)`: 系统提示词。
    *   `conversation (Conversation)`: 可选，在指定对话中进行 LLM 请求，使用该对话设置 (包括人格)，结果保存到对应对话。

#### 发送消息相关 (通常 `yield` 返回)
23. `make_result() -> MessageEventResult`: 创建空消息事件结果。
24. `plain_result(text: str) -> MessageEventResult`: 创建含文本消息的结果。
25. `image_result(url_or_path: str) -> MessageEventResult`: 创建含图片消息的结果 (URL或本地路径)。
26. `chain_result(chain: List[BaseMessageComponent]) -> MessageEventResult`: 创建含消息链的结果。
27. `send(message: MessageChain)`: 发送消息到当前对话。**直接调用 `await event.send(message)`，不使用 `yield`**。返回布尔值，表示是否找到对应平台。
    *   `message (MessageChain)`: 消息链对象。
    *   **注意**: 不支持 `qq_official` 平台。

#### 其他
28. `set_extra(key, value)`: 设置事件额外信息，用于多阶段事件处理。
29. `get_extra(key=None) -> any`: 获取额外信息 (不提供键名返回所有字典)。
30. `clear_extra()`: 清除所有额外信息。

---
outline: deep
---

# AstrBotMessage

AstrBot 消息对象：消息容器。所有平台消息接收后均转换为此类型，实现统一处理。
每个事件均由一个 AstrBotMessage 对象驱动。

`平台发来的消息 --> AstrBotMessage --> AstrBot 事件`

### 属性
1.  `type (MessageType)`: 消息类型。
2.  `self_id (str)`: 机器人自身ID (如QQ号)。
3.  `session_id (str)`: 不含平台会话ID (如QQ号/群号)。
4.  `message_id (str)`: 消息唯一ID，用于引用。
5.  `group_id (str)`: 群组ID，私聊为空。
6.  `sender (MessageMember)`: 消息发送者。
7.  `message (List[BaseMessageComponent])`: 消息链 (Nakuru 格式)。
8.  `message_str (str)`: 纯文本消息字符串 (丢失消息链信息)。
9.  `raw_message (object)`: 原始消息对象 (平台适配器提供)。
10. `timestamp (int)`: 消息时间戳 (自动初始化)。

---
outline: deep
---

## Context

向插件暴露的上下文：提供接口与数据。

### 属性
1.  `provider_manager`: 供应商管理器。
2.  `platform_manager`: 平台管理器。

### 方法

#### 插件相关
1.  `get_registered_star(star_name: str) -> StarMetadata`: 根据插件名获取插件元数据。可获取其他插件元数据。
2.  `get_all_stars() -> List[StarMetadata]`: 获取所有已注册插件的元数据列表。

#### 函数工具相关
3.  `get_llm_tool_manager() -> FuncCall`: 获取 FuncCall 对象，管理所有函数调用工具。
4.  `activate_llm_tool(name: str) -> bool`: 激活已注册的函数调用工具。默认激活。未找到返回 `False`。
5.  `deactivate_llm_tool(name: str) -> bool`: 停用已注册的函数调用工具。未找到返回 `False`。

#### 供应商相关
6.  `register_provider(provider: Provider)`: 注册新的**文本生成**供应商对象 (Provider 类，Chat_Completion 类型)。
7.  `get_provider_by_id(provider_id: str) -> Provider`: 根据供应商ID获取供应商对象。
8.  `get_all_providers() -> List[Provider]`: 获取所有已注册的**文本生成**供应商列表。
9.  `get_all_tts_providers() -> List[TTSProvider]`: 获取所有已注册的**文本到语音**供应商列表。
10. `get_all_stt_providers() -> List[STTProvider]`: 获取所有已注册的**语音到文本**供应商列表。
11. `get_using_provider() -> Provider`: 获取当前使用的**文本生成**供应商对象。
12. `get_using_tts_provider() -> TTSProvider`: 获取当前使用的**文本到语音**供应商对象。
13. `get_using_stt_provider() -> STTProvider`: 获取当前使用的**语音到文本**供应商对象。

#### 其他
14. `get_config() -> AstrBotConfig`: 获取当前 AstrBot 配置对象 (包含插件及Core配置，谨慎修改)。
15. `get_db() -> BaseDatabase`: 获取 AstrBot 数据库对象。
16. `get_event_queue() -> Queue`: 获取 AstrBot 异步事件队列 (每项为 AstrMessageEvent)。
17. `get_platform(platform_type: Union[PlatformAdapterType, str]) -> Platform`: 获取指定类型的平台适配器对象。
18. `send_message(session: Union[str, MessageSesion], message_chain: MessageChain) -> bool`: 根据会话唯一标识符主动发送消息。
    *   `session`: 会话唯一标识符 (`unified_msg_origin` 或 `MessageSession` 对象)。
    *   `message_chain`: 消息链对象。
    *   返回 `bool`，表示是否找到对应消息平台。
    *   **注意**: 不支持 `qq_official` 平台。

---
outline: deep
---

# MessageMember

消息发送者对象：标记消息发送者的基本信息。

### 属性
1.  `user_id (str)`: 消息发送者唯一ID (如QQ号)。
2.  `nickname (str)`: 昵称 (如QQ昵称，自动初始化)。

---
outline: deep
---

# MessageType

消息类型：区分私聊/群聊，继承自 `Enum`。

**用法**: `from astrbot.api import MessageType; print(MessageType.GROUP_MESSAGE)`

### 内容
1.  `GROUP_MESSAGE`: 群聊消息。
2.  `FRIEND_MESSAGE`: 私聊消息。
3.  `OTHER_MESSAGE`: 其他消息 (如系统消息)。

---
outline: deep
---

# PlatformMetadata

平台元数据：包含平台基本信息 (名称、类型等)。

### 属性
1.  `name (str)`: 平台名称。
2.  `description (str)`: 平台描述。
3.  `id (str)`: 平台唯一标识符。
4.  `default_config_tmpl (dict)`: 平台默认配置模板。
5.  `adapter_display_name (str)`: WebUI 显示名称 (默认为 `name`)。

---
outline: deep
---

## Star

插件基类：所有插件继承自此，拥有其所有属性和方法。

### 属性
1.  `context`: 暴露给插件的上下文。

### 方法

#### 文转图
1.  `text_to_image(text: str, return_url=True) -> str`: 将文本转换为图片。
    *   `text`: 待转文本，推荐多行字符串。
    *   `return_url`: 返回图片URL (`True`) 或文件路径 (`False`)。

#### HTML 渲染
2.  `html_render(self, tmpl: str, data: dict, return_url: bool = True, options: dict = None) -> str`: 将 Jinja2 模板渲染为图片。
    *   `tmpl (str)` (必选): HTML Jinja2 模板路径。
    *   `data (dict)` (必选): 渲染模板数据。
    *   `return_url (bool)` (可选, 默认 `True`): 返回图片URL (`True`) 或本地文件路径 (`False`)。
    *   `options (dict)` (可选): 截图详细选项。
        *   `timeout (float)`: 截图超时 (秒)。
        *   `type (str)`: 图片类型 (`"jpeg"` 或 `"png"`)。
        *   `quality (int)`: 图片质量 (0-100, 仅 jpeg)。
        *   `omit_background (bool)`: 是否透明背景 (仅 png)。
        *   `full_page (bool)`: 是否截取整个页面 (默认 `True`)。
        *   `clip (dict)`: 裁剪区域 (`x`, `y`, `width`, `height`)。
        *   `animations (str)`: CSS 动画 (`"allow"` 或 `"disabled"`)。
        *   `caret (str)`: 文本光标 (`"hide"` 或 `"initial"`)。
        *   `scale (str)`: 页面缩放 (`"css"` 或 `"device"`)。
        *   `mask (list)`: 需遮盖的 Playwright Locator 列表。
    *   Jinja2 知识可查阅 [Jinja2 文档](https://docs.jinkan.org/docs/jinja2/)。
    *   此功能由 [CampuxUtility](https://github.com/idoknow/CampuxUtility) 提供。

#### 终止
3.  `terminate(Abstract)`: 抽象方法，需在插件中实现。插件禁用、重载或 AstrBot 关闭时触发。用于释放资源，回滚修改。若插件使用外部进程，强烈建议在此销毁。

    **实现示例**:
    ```Python
    async def terminate(self):
        """此处实现你的对应逻辑, 例如销毁, 释放某些资源, 回滚某些修改。"""
    ```

---
outline: deep
---

## StarMetadata

插件的元数据。

### 属性

#### 基础属性
1.  `name (str)`: 插件名称。
2.  `author (str)`: 插件作者。
3.  `desc (str)`: 插件简介。
4.  `version (str)`: 插件版本。
5.  `repo (str)`: 插件仓库地址。

#### 插件类/模块属性
6.  `star_cls_type (type)`: 插件类对象类型 (如 `<type 'HelloWorld'>`)。
7.  `star_cls (object)`: 插件类实例。
8.  `module_path (str)`: 插件模块路径。
9.  `module (ModuleType)`: 插件模块对象。
10. `root_dir_name (str)`: 插件目录名称。

#### 插件身份/状态属性
11. `reserved (bool)`: 是否为 AstrBot 保留插件。
12. `activated (bool)`: 是否被激活。

#### 插件配置
13. `config (AstrBotConfig)`: 插件配置对象。

#### 注册的 Handler 全名列表
14. `star_handler_full_names (List[str])`: 注册的 Handler 全名列表。

#### 其它
该类实现了 `__str__` 方法，可直接打印插件信息。
