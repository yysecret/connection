import streamlit as st
import datetime
import logging # 引入专业的日志模块

# 告诉服务器：立刻打印所有 INFO 级别以上的信息
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

st.set_page_config(page_title="桥梁系统测试", page_icon="⚙️")

st.title("婆婆的在线实验室(v2)")
st.write("婆婆您好，Jayden的系统正在测试中。如果您看到了这条消息，请点击确认。")

if st.button("确认 (Confirm)"):
    # 给外婆看的前端反馈
    st.success("收到！确认信息已成功发送给孙子。")
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 方法 1：强制刷新 print 的缓存 (加上 flush=True)
    print(f"[{current_time}] 🔔 (Print) ！！！婆婆已成功点击确认！！！", flush=True)
    
    # 方法 2：使用工业级的 logging 模块 (云端最稳妥的方式)
    logging.info("🚀 🚀 🚀 收到最高指令：婆婆已点击确认！")