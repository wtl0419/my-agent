import time
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入刚才写好的邮件抓取函数
from tools.fetch_mail import fetch_emails

INBOX_DIR = Path("vault/inbox")
DRAFTS_DIR = Path("vault/drafts")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))  # 轮询间隔，默认 60 秒

def process_pending_inbox():
    """扫描 inbox 中未处理的邮件，准备处理流程"""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    if not INBOX_DIR.exists():
        return

    for email_file in INBOX_DIR.glob("*.md"):
        draft_file = DRAFTS_DIR / f"draft_{email_file.name}"
        
        # 如果草稿还没生成，说明需要处理
        if not draft_file.exists():
            print(f"[Agent] 发现新邮件需要处理: {email_file.name}")
            # 这里先生成占位草稿，后续串接 LLM / dsh 自动生成
            content = email_file.read_text(encoding="utf-8")
            draft_content = f"""# 待审回复草稿

对应原邮件: {email_file.name}
生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

---
您好，已收到您的来信。
（本草稿由本地 Agent 自动拟定，待人工确认后发送）
"""
            draft_file.write_text(draft_content, encoding="utf-8")
            print(f"[Agent] 已拟定初版草稿至: {draft_file}")

def run_loop():
    print("[Agent] 个人助手常驻后台已启动...")
    while True:
        try:
            # 1. 抓取新邮件
            fetch_emails()
            # 2. 处理抓取到的邮件
            process_pending_inbox()
        except Exception as e:
            print(f"[Agent 运行异常]: {e}")
        
        # 3. 等待下一次轮询
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_loop()