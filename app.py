import datetime
import logging
import os
import random
import socket
import ssl
import string
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from openai import APIConnectionError, APITimeoutError, OpenAI
from streamlit.errors import StreamlitSecretNotFoundError
from zoneinfo import ZoneInfo


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
        value = value.replace("\r", "").replace("\n", "")
        os.environ[key] = value


_load_env_file()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

st.set_page_config(
    page_title="私人实验室视频中枢",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧪",
)


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


def get_room_id():
    if "room_id" not in st.session_state:
        random_str = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        st.session_state.room_id = f"Lab_Session_{random_str}"
    return st.session_state.room_id


with st.sidebar:
    st.title("🛠 实验室控制台")
    st.markdown("---")
    st.subheader("视频传输协议")
    selected_mode = st.selectbox(
        "切换显示模式：",
        options=["普通通话模式 (Jitsi)", "高清制图模式 (VDO.ninja)"],
        index=0,
        help="如果需要观察微小零件的尺寸，请选择高清模式。",
    )
    st.markdown("---")
    st.info(f"当前房间 ID: \n`{get_room_id()}`")
    if st.button("🔄 刷新视频流"):
        st.rerun()

st.title("🧪 私人实验室：专家协作系统")

room_id = get_room_id()

if selected_mode == "普通通话模式 (Jitsi)":
    base_url = "https://meet.jit.si/"
    video_url = (
        f"{base_url}{room_id}"
        "#config.prejoinPageEnabled=false&interfaceConfig.SHOW_JITSI_WATERMARK=false"
    )
    st.success("✅ 当前模式：Jitsi (多功能学术讨论模式)")
    st.caption("特点：连接快速、支持多人讨论、功能全面。")
else:
    base_url = "https://vdo.ninja/?"
    video_url = (
        f"{base_url}view={room_id}&label=Professor_Monitor"
        "&bitrate=5000&scale=100&autostart&darkmode=1"
    )
    st.warning("🚀 当前模式：VDO.ninja (4K 高清制图模式)")
    st.caption("特点：超低延迟、极高清晰度。建议在稳定 Wi-Fi 环境下使用。")

video_container = st.container()
with video_container:
    st.caption("若嵌入区域为空白，多半是目标站点禁止 iframe；请用浏览器直接打开会议链接。")
    components.iframe(src=video_url, height=720, scrolling=True)

st.markdown("---")
st.header("📐 阚教授的空间投影站 (Web-AR)")
# 3D 模型（公开示例；可换成自己的 .glb；iOS AR 常用 .usdz）
model_url = "https://modelviewer.dev/shared-assets/models/Astronaut.glb"
ios_src = "https://modelviewer.dev/shared-assets/models/Astronaut.usdz"
ar_html = f"""
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
<model-viewer
    src="{model_url}"
    ios-src="{ios_src}"
    ar
    ar-modes="webxr scene-viewer quick-look"
    camera-controls
    shadow-intensity="1"
    auto-rotate
    style="width: 100%; height: 500px; background-color: #f0f2f6; border-radius: 15px;">
    <button slot="ar-button" style="background-color: white; border-radius: 4px; border: none; position: absolute; top: 16px; right: 16px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.25);">
        👋 在您的桌面上放置零件
    </button>
</model-viewer>
"""
components.html(ar_html, height=550, scrolling=False)
st.caption(
    "📖 **操作指引**：阚教授可以用手指旋转模型。点击右上角按钮，即可通过 iPad 摄像头将零件投影到真实书桌上。"
)

st.markdown("---")
st.subheader("🎨 祖孙联合工程绘图室 (实时协同)")
st.caption(f"白板与上方视频共用同一房间号：`{room_id}`（与侧边栏显示一致）。")
excalidraw_url = f"https://excalidraw.com/#room={room_id}"
st.write("📖 **操作指南**：")
st.caption("1. 您在这里画的内容，外婆在那边刷新页面后也能实时看到并修改。")
st.caption("2. 点击左上角的『菜单』图标，可以保存图片到本地电脑。")
st.caption("3. 为保证在 Streamlit Cloud 稳定可用，请点击下方按钮在新标签页打开白板。")
st.link_button("🚀 打开实时协同白板", excalidraw_url, use_container_width=True)
st.markdown(f"备用链接：[{excalidraw_url}]({excalidraw_url})")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.text_input("给教授发送即时笔记：", placeholder="例如：现在的尺寸读数是 2.54mm")
with col2:
    st.button("📸 截取当前高清画面并保存")

st.markdown("---")

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
    user_input = st.text_input("请输入检索关键词或指令：")
    if st.button("开始检索 (Execute)"):
        if user_input:
            ny_time = datetime.datetime.now(ZoneInfo("America/New_York")).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            logging.info(f"[{ny_time} NY Time] 阚教授发起检索: {user_input}")
            with st.spinner("系统正在从内部学术数据库中检索，请稍候..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_input},
                        ],
                        temperature=0.7,
                    )
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
