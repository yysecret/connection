import streamlit as st
import datetime
from zoneinfo import ZoneInfo

US_EASTERN = ZoneInfo("America/New_York")

# 设置网页的标题和图标
st.set_page_config(page_title="桥梁系统测试", page_icon="⚙️")

# 网页上显示的文字
st.title("婆婆的在线实验室")
st.write("婆婆您好，Jayden的系统正在测试中。如果您看到了这条消息，请点击确认。")

# 按钮逻辑
if st.button("确认 (Confirm)"):
    # 外婆在屏幕上会看到的反馈
    st.success("收到！确认信息已成功发送给Jayden。")
    
    # 核心逻辑：这一行文字只会打印在服务器后台，外婆看不到
    current_time = datetime.datetime.now(US_EASTERN).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"=================================================")
    print(f"[{current_time}] 🔔 ！！！婆婆已成功点击确认！！！")
    print(f"=================================================")