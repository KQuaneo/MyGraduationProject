#!/usr/bin/env python3
"""
robot_helper.py - 机器人联网助手
在当前 Agent 会话中运行，处理需要联网的查询

这个脚本由主 Agent 会话运行，监听 NEED_HELP_FILE 并处理联网查询
"""
import os
import sys
import json
import time
import subprocess

# === 文件路径 ===
NEED_HELP_FILE = "/tmp/robot_need_help.txt"
OUTPUT_FILE = "/tmp/robot_output.json"

def read_and_delete_file(filepath):
    """读取文件内容并删除"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        os.remove(filepath)
        return content
    except:
        return None

def write_file(filepath, content):
    """写入文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except:
        return False

def wait_for_file(filepath, timeout=None, check_interval=0.1):
    """等待文件出现"""
    start_time = time.time()
    while True:
        if os.path.exists(filepath):
            return True
        if timeout and time.time() - start_time > timeout:
            return False
        time.sleep(check_interval)

def main():
    print("[Helper] 联网助手已启动，等待查询...")
    
    while True:
        if wait_for_file(NEED_HELP_FILE, timeout=None, check_interval=0.2):
            data = read_and_delete_file(NEED_HELP_FILE)
            if data:
                try:
                    request = json.loads(data)
                    query = request.get("original_query", "")
                    print(f"[Helper] 收到查询: {query}")
                    
                    # 这里需要外部 Agent 处理并写入 OUTPUT_FILE
                    # 这个脚本只是占位，实际处理由主 Agent 完成
                    
                except:
                    pass
        time.sleep(0.1)

if __name__ == "__main__":
    main()
