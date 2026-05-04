import os
import datetime
import logging
from pathlib import Path

import streamlit as st
from zoneinfo import ZoneInfo
from openai import OpenAI
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
        os.environ[key] = value


_load_env_file()

# 1. 基础设置与日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
st.set_page_config(page_title="婆婆的在线实验室", page_icon="⚙️")


def _openai_api_key():
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        return st.secrets["OPENAI_API_KEY"]
    except (StreamlitSecretNotFoundError, KeyError, FileNotFoundError):
        return None


# 2. 初始化 OpenAI 客户端：本地用 .env / 环境变量，云端用 Streamlit Secrets
_api_key = _openai_api_key()
if not _api_key:
    st.error(
        "未找到 OPENAI_API_KEY。请在项目根目录 `.env` 中设置，"
        "或创建 `.streamlit/secrets.toml`，或在 Streamlit Cloud 的 Secrets 中配置。"
    )
    st.stop()

client = OpenAI(api_key=_api_key)

# 3. 界面 UI 设计 (保持学术感，去除花哨的元素)
st.title("⚙️ 婆婆的专属数字实验室")
st.markdown("---")
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
                    temperature=0.7 # 让回答适度灵活但不过于发散
                )
                
                # 展示 AI 的回答
                assistant_reply = response.choices[0].message.content
                st.info("💡 助理简报 (Assistant Briefing):")
                st.write(assistant_reply)
                
                logging.info(f"[{ny_time} NY Time] AI 已成功回复。")
                
            except Exception as e:
                st.error("网络连接出现波动，请稍后再试。")
                logging.error(f"API 调用出错: {e}")
    else:
        st.warning("阚教授，请输入检索内容后再点击执行。")