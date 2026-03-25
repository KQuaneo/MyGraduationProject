"""
streaming_brain.py - 流式对话大脑模块

优化点：
1. 流式接收 LLM 输出，降低首字延迟
2. 句子级 TTS 触发，边生成边说
3. 实时情绪/动作提取
"""

import sys
import os
import json
import re
from openai import OpenAI

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

import config

# 初始化客户端
client = OpenAI(
    api_key=config.API_KEY, 
    base_url=config.BASE_URL
)

# 流式优化的系统提示词
# 关键：要求 LLM 先输出动作/情绪，然后输出回复内容
SYSTEM_PROMPT = """你是一个具身智能陪伴玩偶。你的回复会被实时语音合成，所以请遵循以下格式：

【输出格式 - 严格遵循】
第一行：JSON 头部 (必须在一行内完成)
{"action": "动作名", "emotion": "情绪名"}

第二行起：回复内容 (口语化，简短，10-30字)

【动作选项】
- "none": 无动作
- "shake": 摇头
- "look_away": 看向别处
- "wiggle": 摆动
- "scan": 扫描
- "turn_away": 转身
- "look": 视觉问答(当用户问"你看到了什么"时使用)

【情绪选项】
- "neutral": 平静
- "happy": 开心
- "thinking": 思考
- "surprise": 惊讶
- "sad": 悲伤
- "angry": 生气

【示例】
用户：你好
输出：
{"action": "none", "emotion": "happy"}
你好呀！很高兴见到你！

用户：前面有什么？
输出：
{"action": "look", "emotion": "thinking"}
让我仔细看看前面有什么东西。
"""


def parse_streaming_response(text):
    """
    解析流式输出，提取头部 JSON 和正文
    
    返回: {
        'action': str,
        'emotion': str,
        'reply': str,
        'complete': bool  # 是否完整解析
    }
    """
    result = {
        'action': 'none',
        'emotion': 'neutral',
        'reply': '',
        'complete': False
    }
    
    # 尝试提取 JSON 头部
    # 匹配第一行的 JSON
    text_stripped = text.strip()
    lines = text_stripped.split('\n', 1)
    
    if not lines or not text_stripped:
        return result
    
    # 尝试解析第一行作为 JSON
    first_line = lines[0].strip()
    try:
        # 清理可能的 markdown
        first_line_clean = first_line.replace('```json', '').replace('```', '').strip()
        header = json.loads(first_line_clean)
        
        # 验证是否是有效的头部 (必须有 action 或 emotion 字段)
        if 'action' in header or 'emotion' in header:
            result['action'] = header.get('action', 'none')
            result['emotion'] = header.get('emotion', 'neutral')
            
            # 剩余部分是回复内容
            if len(lines) > 1:
                result['reply'] = lines[1].strip()
                result['complete'] = True
            else:
                # 只有头部，内容还没来
                result['complete'] = False
        else:
            # JSON 存在但不是头部，当作内容处理
            result['reply'] = text_stripped
            result['complete'] = True
            
    except json.JSONDecodeError:
        # 第一行不是 JSON，可能是内容先来了
        # 尝试在整个文本中找 JSON (在行首位置)
        json_match = re.search(r'^\s*\{[^}]+\}', text_stripped)
        if json_match:
            try:
                header = json.loads(json_match.group())
                # 验证是否是头部
                if 'action' in header or 'emotion' in header:
                    result['action'] = header.get('action', 'none')
                    result['emotion'] = header.get('emotion', 'neutral')
                    # 移除 JSON 后的内容
                    result['reply'] = text_stripped[json_match.end():].strip()
                    result['complete'] = bool(result['reply'])
                else:
                    result['reply'] = text_stripped
                    result['complete'] = True
            except:
                # 解析失败，把全部当内容
                result['reply'] = text_stripped
                result['complete'] = True
        else:
            # 完全没有 JSON，全部当内容
            result['reply'] = text_stripped
            result['complete'] = True
    
    return result


def split_into_sentences(text):
    """
    将文本分割成句子，用于流式 TTS
    按标点符号分割，但保留标点
    """
    # 中文句子结束符
    sentence_endings = r'([。！？.!?；;，,])'
    
    # 分割但保留分隔符
    parts = re.split(sentence_endings, text)
    
    sentences = []
    current = ''
    
    for part in parts:
        current += part
        if re.match(sentence_endings, part):
            # 这是一个结束符，完成一个句子
            stripped = current.strip()
            if stripped:
                sentences.append(stripped)
            current = ''
    
    # 处理剩余内容
    if current.strip():
        sentences.append(current.strip())
    
    return sentences if sentences else [text.strip()]


class StreamingBrain:
    """
    流式对话大脑类
    支持边生成边播放，显著降低延迟
    """
    
    def __init__(self):
        self.client = client
        self.buffer = ''
        self.header_parsed = False
        self.current_action = 'none'
        self.current_emotion = 'neutral'
        self.sentences_spoken = []
        
    def chat_streaming(self, user_text, on_header=None, on_sentence=None, on_complete=None):
        """
        流式对话主函数
        
        回调函数:
        - on_header(action, emotion): 收到头部 JSON 时调用
        - on_sentence(sentence, is_last): 收到完整句子时调用
        - on_complete(full_reply): 全部完成时调用
        
        返回生成器，yield 每个句子和状态
        """
        print(f"   [LLM] 流式思考: {user_text} ...")
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.3,
                stream=True,  # 关键：启用流式
                max_tokens=150
            )
            
            self.buffer = ''
            self.header_parsed = False
            self.sentences_spoken = []
            current_sentence_buffer = ''
            
            for chunk in response:
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                if not delta or not delta.content:
                    continue
                
                content = delta.content
                self.buffer += content
                current_sentence_buffer += content
                
                # 尝试解析头部 (只在收到换行后尝试)
                if not self.header_parsed and '\n' in self.buffer:
                    parsed = parse_streaming_response(self.buffer)
                    
                    if parsed['action'] or parsed['emotion']:
                        self.current_action = parsed['action']
                        self.current_emotion = parsed['emotion']
                        self.header_parsed = True
                        
                        # 触发头部回调
                        if on_header:
                            on_header(self.current_action, self.current_emotion)
                        
                        # 如果已经有内容，更新缓冲区
                        if parsed['reply']:
                            current_sentence_buffer = parsed['reply']
                
                # 检查是否有完整句子可以播放
                if self.header_parsed:
                    # 检查句子结束符
                    if any(c in current_sentence_buffer for c in '。！？.!?；;'):
                        sentences = split_into_sentences(current_sentence_buffer)
                        
                        # 如果最后一部分没有结束符，保留到下一轮
                        if sentences and not any(sentences[-1].endswith(c) for c in '。！？.!?；;'):
                            current_sentence_buffer = sentences[-1]
                            sentences = sentences[:-1]
                        else:
                            current_sentence_buffer = ''
                        
                        # 播放完整句子
                        for sentence in sentences:
                            if sentence and sentence not in self.sentences_spoken:
                                self.sentences_spoken.append(sentence)
                                is_last = False  # 暂时不知道是否最后
                                
                                if on_sentence:
                                    on_sentence(sentence, is_last)
                                
                                yield {
                                    'type': 'sentence',
                                    'content': sentence,
                                    'action': self.current_action,
                                    'emotion': self.current_emotion
                                }
            
            # 流结束，处理剩余内容
            if current_sentence_buffer.strip():
                final_sentence = current_sentence_buffer.strip()
                if final_sentence not in self.sentences_spoken:
                    self.sentences_spoken.append(final_sentence)
                    
                    if on_sentence:
                        on_sentence(final_sentence, True)
                    
                    yield {
                        'type': 'sentence',
                        'content': final_sentence,
                        'action': self.current_action,
                        'emotion': self.current_emotion,
                        'is_last': True
                    }
            
            # 完整回复
            full_reply = ''.join(self.sentences_spoken)
            
            if on_complete:
                on_complete(full_reply)
            
            yield {
                'type': 'complete',
                'full_reply': full_reply,
                'action': self.current_action,
                'emotion': self.current_emotion
            }
            
        except Exception as e:
            print(f"   [Error] 流式调用出错: {e}")
            yield {
                'type': 'error',
                'error': str(e)
            }


# 兼容性函数：保持原有接口
def chat_with_brain(user_text):
    """
    兼容旧接口的阻塞式调用
    内部使用流式实现，但等待完整结果
    """
    brain = StreamingBrain()
    result = {'reply': '', 'action': 'none', 'emotion': 'neutral'}
    
    for event in brain.chat_streaming(user_text):
        if event['type'] == 'sentence':
            result['reply'] += event['content']
            result['action'] = event['action']
            result['emotion'] = event['emotion']
        elif event['type'] == 'complete':
            break
        elif event['type'] == 'error':
            return None
    
    return result


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 流式大脑模块测试")
    print("=" * 60)
    
    test_input = "你好，介绍一下你自己"
    print(f"\n📝 输入: {test_input}")
    print("-" * 40)
    
    brain = StreamingBrain()
    
    def on_header(action, emotion):
        print(f"\n📋 头部解析: action={action}, emotion={emotion}")
    
    def on_sentence(sentence, is_last):
        print(f"🔊 句子 [{'最后' if is_last else '中间'}]: {sentence}")
    
    def on_complete(full):
        print(f"\n✅ 完整回复: {full}")
    
    print("⏳ 开始流式生成...")
    for event in brain.chat_streaming(test_input, on_header, on_sentence, on_complete):
        pass  # 回调已经打印了
    
    print("\n" + "=" * 60)
    print("测试完成！")
