import re
import json
import sys
import os

def clean_vtt_text(text):
    # Remove HTML tags like <00:00:00.320><c> or <c>
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_vtt(vtt_path):
    if not os.path.exists(vtt_path):
        print(f"Error: {vtt_path} not found")
        return "", []

    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into cues
    cues = re.split(r'\n\s*\n', content)
    
    all_text_words = []
    timestamp_map = []
    
    for cue in cues:
        lines = [line.strip() for line in cue.strip().split('\n') if line.strip()]
        if len(lines) < 2:
            continue
        
        # Find timestamp line
        ts_line = ""
        text_lines = []
        for line in lines:
            if '-->' in line:
                ts_line = line
            elif ts_line:
                text_lines.append(line)
        
        if not ts_line:
            continue
            
        ts_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3})', ts_line)
        if not ts_match:
            continue
        
        start_time = ts_match.group(1)
        
        # Extract and clean text
        text = ' '.join(text_lines)
        text = clean_vtt_text(text)
        if not text:
            continue
        
        words = text.split()
        
        # Overlap-based deduplication
        overlap = 0
        # Increased lookback for better deduplication in long transcripts
        max_lookback = min(len(all_text_words), len(words), 50) 
        for i in range(max_lookback, 0, -1):
            if all_text_words[-i:] == words[:i]:
                overlap = i
                break
        
        new_words = words[overlap:]
        if new_words:
            # Record the timestamp for the first word of this new segment
            timestamp_map.append({
                "time": start_time,
                "word_index": len(all_text_words)
            })
            all_text_words.extend(new_words)
            
    return ' '.join(all_text_words), timestamp_map

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python clean_subs.py <input.vtt> <output.txt> <output.json>")
        sys.exit(1)
        
    vtt_file = sys.argv[1]
    txt_output = sys.argv[2]
    map_output = sys.argv[3]
    
    transcript, ts_map = parse_vtt(vtt_file)
    
    with open(txt_output, 'w', encoding='utf-8') as f:
        # Add line breaks for readability
        words = transcript.split()
        for i in range(0, len(words), 20):
            f.write(' '.join(words[i:i+20]) + '\n')
        
    with open(map_output, 'w', encoding='utf-8') as f:
        json.dump(ts_map, f, indent=2)
    
    print(f"Cleaned transcript saved to {txt_output}")
    print(f"Timestamp map saved to {map_output}")
