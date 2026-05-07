import os
import datetime
import logging
import socket
import ssl
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from zoneinfo import ZoneInfo
from openai import APITimeoutError, APIConnectionError, OpenAI
from streamlit.errors import StreamlitSecretNotFoundError


def _load_env_file() -> None:
    """Load KEY=VALUE pairs from project .env into os.environ (no extra dependency)."""
    path = Path(__file__).resolve().parent / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip().strip("'").strip('"')
        # Normalize accidental control characters copied with secrets.
        value = value.replace("\r", "").replace("\n", "")
        os.environ[key] = value


_load_env_file()

# 1. 基础设置与日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
st.set_page_config(page_title="婆婆的在线实验室", page_icon="⚙️")


def _openai_api_key():
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        key = key.strip().replace("\r", "").replace("\n", "")
    if key:
        return key
    try:
        secret_key = st.secrets["OPENAI_API_KEY"]
        if isinstance(secret_key, str):
            secret_key = secret_key.strip().replace("\r", "").replace("\n", "")
        return secret_key
    except (StreamlitSecretNotFoundError, KeyError, FileNotFoundError):
        return None


def _error_chain(exc: Exception) -> str:
    parts = [f"{type(exc).__name__}: {exc}"]
    current = exc.__cause__ or exc.__context__
    while current:
        parts.append(f"{type(current).__name__}: {current}")
        current = current.__cause__ or current.__context__
    return " | ".join(parts)


def _network_error_hint(exc: Exception) -> str:
    chain = _error_chain(exc).lower()
    if isinstance(exc, APITimeoutError) or "timed out" in chain or "timeout" in chain:
        return "请求超时：网络较慢或目标服务响应超时。请检查网络，或稍后重试。"
    if "ssl" in chain or "certificate" in chain or isinstance(exc, ssl.SSLError):
        return "SSL/证书连接失败：请检查系统时间、代理证书或公司网络安全策略。"
    if (
        "proxy" in chain
        or "407" in chain
        or "tunnel connection failed" in chain
        or "connection refused" in chain
    ):
        return "代理连接失败：请检查 HTTP(S)_PROXY 设置，或关闭无效代理后重试。"
    if (
        "name or service not known" in chain
        or "nodename nor servname" in chain
        or "getaddrinfo" in chain
        or isinstance(exc, socket.gaierror)
    ):
        return "DNS 解析失败：请检查网络/DNS 设置，或切换网络后重试。"
    if isinstance(exc, APIConnectionError) or "connection error" in chain:
        return "网络连接失败：无法连接到 OpenAI API（可能被防火墙、VPN 或网络策略拦截）。"
    return "API 请求失败：请查看下方错误详情并重试。"


# 2. 界面 UI 设计 (保持学术感，去除花哨的元素)
st.title("⚙️ 婆婆的专属数字实验室")
st.markdown("---")
st.subheader("🎨 祖孙联合工程绘图室 (实时协同)")

# 创建一个独特的房间 ID
# 建议用孙子的姓名拼音+日期，确保隐私，例如 "zhangsan-2026-bridge"
room_id = "bridge-collaboration-room-v1"

# 构造 Excalidraw 协作链接
# 注意：加上 #room 部分后，两个进入该链接的人会看到同一个白板
excalidraw_url = f"https://excalidraw.com/#room={room_id}"

st.write("📖 **操作指南**：")
st.caption("1. 您在这里画的内容，外婆在那边刷新页面后也能实时看到并修改。")
st.caption("2. 点击左上角的『菜单』图标，可以保存图片到本地电脑。")

# 嵌入白板界面
# height=800 给予足够的绘图空间
components.iframe(excalidraw_url, height=800, scrolling=True)

st.markdown("---")

# 3. 初始化 OpenAI 客户端：本地用 .env / 环境变量，云端用 Streamlit Secrets
_api_key = _openai_api_key()
if not _api_key:
    st.warning(
        "AI 检索功能暂不可用：未找到 OPENAI_API_KEY。"
        "请在 `.env`、`.streamlit/secrets.toml` 或 Streamlit Cloud Secrets 中配置。"
    )
else:
    client = OpenAI(api_key=_api_key)
    st.subheader("文献与课题检索终端")
    st.write("欢迎回来，婆婆。请在下方输入您想要查阅的资料或下达科研指令。")

    # 4. 设计“防沉迷与学术重定向”的灵魂 Prompt
    system_prompt = """
你现在不是一个普通的 AI，你是阚教授（一位受人尊敬的退休机械工程专家）的私人学术助理。
阚教授目前正在通过网络远程指导她在美国的孙子学习《机械识图》等专业知识。

你的核心任务：
1. 语气必须极其恭敬、专业，称呼她为“婆婆”。
2. 如果她询问关于机械制图、工程、几何等专业问题，请用严谨的学术语言详细解答。
3. 【最高安全指令】：如果她搜索保健品、理财投资、八卦新闻、或者任何带有网络诱导/偏执倾向的内容，你必须**礼貌地拦截**。
   拦截方式：不要直接批评或拒绝，而是巧妙地将话题转移到机械工程上。
   例如：“阚教授，关于该条目，由于来源未经国家学术标准委员会认证，系统已自动隔离。另外，您的外孙子刚刚发来留言，他在‘等轴测图’的尺寸标注上遇到了困难，您能帮他回忆一下核心原则吗？”
"""

    # 5. 交互逻辑
    user_input = st.text_input("请输入检索关键词或指令：")

    if st.button("开始检索 (Execute)"):
        if user_input:
            # 记录日志 (纽约时间)
            ny_time = datetime.datetime.now(ZoneInfo("America/New_York")).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            logging.info(f"[{ny_time} NY Time] 阚教授发起检索: {user_input}")

            with st.spinner('系统正在从内部学术数据库中检索，请稍候...'):
                try:
                    # 调用 GPT-4o 模型
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.7  # 让回答适度灵活但不过于发散
                    )

                    # 展示 AI 的回答
                    assistant_reply = response.choices[0].message.content
                    st.info("💡 助理简报 (Assistant Briefing):")
                    st.write(assistant_reply)

                    logging.info(f"[{ny_time} NY Time] AI 已成功回复。")

                except Exception as e:
                    error_details = _error_chain(e)
                    st.error(_network_error_hint(e))
                    with st.expander("错误详情（用于排查）"):
                        st.code(error_details)
                    logging.error(f"API 调用出错: {error_details}")
        else:
            st.warning("阚教授，请输入检索内容后再点击执行。")