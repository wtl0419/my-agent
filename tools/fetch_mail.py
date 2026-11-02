import os
import json
import email
from email.header import decode_header
import imaplib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_AUTH_CODE = os.getenv("EMAIL_AUTH_CODE")

STATE_FILE = Path("state/processed_emails.json")
INBOX_DIR = Path("vault/inbox")

def clean_filename(s: str) -> str:
    return "".join(c for c in s if c.isalnum() or c in (' ', '_', '-')).rstrip()

def decode_str(header_val: str) -> str:
    if not header_val:
        return ""
    dh = decode_header(header_val)
    default_charset = 'utf-8'
    res = []
    for bytes_or_str, charset in dh:
        if isinstance(bytes_or_str, bytes):
            try:
                res.append(bytes_or_str.decode(charset or default_charset, errors='replace'))
            except Exception:
                res.append(bytes_or_str.decode('utf-8', errors='replace'))
        else:
            res.append(bytes_or_str)
    return "".join(res)

def load_processed_ids() -> set:
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_processed_ids(ids: set):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, ensure_ascii=False, indent=2)

def fetch_emails():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    processed_ids = load_processed_ids()

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, EMAIL_AUTH_CODE)
    mail.select("INBOX")

    # 搜索所有邮件或近期的未读邮件
    status, messages = mail.search(None, "UNSEEN")
    if status != "OK" or not messages[0]:
        print("没有新未读邮件。")
        mail.logout()
        return

    email_ids = messages[0].split()
    for eid in email_ids:
        res, data = mail.fetch(eid, "(RFC822)")
        if res != "OK":
            continue

        msg = email.message_from_bytes(data[0][1])
        msg_id = msg.get("Message-ID", eid.decode())

        if msg_id in processed_ids:
            continue

        subject = decode_str(msg.get("Subject", "无标题"))
        sender = decode_str(msg.get("From", "未知发件人"))
        date = msg.get("Date", "")

        # 提取纯文本正文
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    break
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")

        # 写入 Markdown
        safe_name = clean_filename(subject)[:40] or "email"
        out_path = INBOX_DIR / f"{safe_name}.md"
        md_content = f"""# {subject}

- **发件人**: {sender}
- **时间**: {date}
- **Message-ID**: {msg_id}

---

{body}
"""
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        processed_ids.add(msg_id)
        print(f"已拉取并保存邮件: {subject}")

    save_processed_ids(processed_ids)
    mail.logout()

if __name__ == "__main__":
    fetch_emails()