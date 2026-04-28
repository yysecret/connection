import streamlit as st
import datetime
import logging
import pytz  # 新增：引入专业时区处理库

# 告诉服务器：立刻打印所有 INFO 级别以上的信息
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

st.set_page_config(page_title="桥梁系统测试", page_icon="⚙️")

# 加上 V2.1 标志，方便肉眼确认云端已更新
st.title("婆婆的在线实验室 (V2.1 时间修正版)")
st.write("婆婆您好，Jayden的系统正在测试中。如果您看到了这条消息，请点击确认。")

if st.button("确认 (Confirm)"):
    # 给外婆看的前端反馈
    st.success("收到！确认信息已成功发送给Jayden。")
    
    # 核心修改：强制获取纽约/美东时间
    ny_timezone = pytz.timezone('America/New_York')
    ny_time = datetime.datetime.now(ny_timezone).strftime("%Y-%m-%d %H:%M:%S")
    
    # 打印带有时区标签的精准日志
    print(f"[{ny_time} NY Time] 🔔 (Print) ！！！婆婆已成功点击确认！！！", flush=True)
    logging.info(f"[{ny_time} NY Time] 🚀 🚀 🚀 收到最高指令：婆婆已点击确认！")