import json
import sys
import os

# 🚀 通用时间戳查找工具
# 用法: python3 find_timestamps_pro.py <transcript.txt> <timestamp_map.json> <quotes.json>

def find_closest_timestamp(word_index, ts_map):
    closest_time = ts_map[0]["time"]
    for entry in ts_map:
        if entry["word_index"] <= word_index:
            closest_time = entry["time"]
        else:
            break
    return closest_time

def find_word_index(quote, transcript_words):
    quote_words = quote.split()
    if not quote_words:
        return -1
    
    # 使用前 5 个词进行匹配以提高稳健性
    search_len = min(5, len(quote_words))
    search_phrase = quote_words[:search_len]
    
    for i in range(len(transcript_words) - search_len + 1):
        if [w.lower().strip('.,!?()') for w in transcript_words[i:i+search_len]] == [w.lower().strip('.,!?()') for w in search_phrase]:
            return i
    return -1

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python3 find_timestamps_pro.py <transcript.txt> <timestamp_map.json> <quotes.json>")
        sys.exit(1)

    transcript_file = sys.argv[1]
    map_file = sys.argv[2]
    quotes_file = sys.argv[3]
    
    if not os.path.exists(transcript_file) or not os.path.exists(map_file) or not os.path.exists(quotes_file):
        print("❌ 错误: 输入文件不存在")
        sys.exit(1)

    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    transcript_words = transcript_text.split()
    
    with open(map_file, 'r', encoding='utf-8') as f:
        ts_map = json.load(f)
        
    with open(quotes_file, 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)
        # 支持列表或带 quotes 键的字典
        quotes = quotes_data if isinstance(quotes_data, list) else quotes_data.get("quotes", [])
    
    results = []
    for q_entry in quotes:
        # 支持字符串或字典对象
        q_text = q_entry if isinstance(q_entry, str) else q_entry.get("en") or q_entry.get("text")
        if not q_text:
            continue
            
        idx = find_word_index(q_text, transcript_words)
        if idx != -1:
            time = find_closest_timestamp(idx, ts_map)
            results.append({
                "quote": q_text, 
                "time": time, 
                "zh": q_entry.get("zh") if isinstance(q_entry, dict) else ""
            })
        else:
            results.append({"quote": q_text, "error": "not found"})
            
    print(json.dumps(results, ensure_ascii=False, indent=2))
