def _clean_text(self, text):
    """Clean text for TTS - LESS AGGRESSIVE"""
    if not text:
        return ""
    
    # Remove markdown headers but keep text
    clean_text = text.replace('###', '')
    
    # Replace markdown symbols with spaces
    clean_text = clean_text.replace('#', ' ')
    clean_text = clean_text.replace('*', ' ')
    clean_text = clean_text.replace('`', ' ')
    
    # Keep only basic emojis or remove all if causing issues
    # Let's remove all emojis for now
    import re
    
    # Remove emoji ranges
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+", flags=re.UNICODE)
    
    clean_text = emoji_pattern.sub('', clean_text)
    
    # Remove specific problematic characters but keep text
    clean_text = clean_text.replace('🎵', '')
    clean_text = clean_text.replace('🚀', '')
    clean_text = clean_text.replace('📸', '')
    clean_text = clean_text.replace('🔒', '')
    clean_text = clean_text.replace('🧮', '')
    clean_text = clean_text.replace('💫', '')
    clean_text = clean_text.replace('🌟', '')
    
    # Fix common markdown issues
    clean_text = clean_text.replace('[MANUAL]', '')
    clean_text = clean_text.replace('[manual]', '')
    
    # Remove extra spaces and newlines
    clean_text = re.sub(r'\n+', ' ', clean_text)  # Replace newlines with space
    clean_text = re.sub(r'\s+', ' ', clean_text)  # Collapse multiple spaces
    clean_text = clean_text.strip()
    
    # Ensure minimum length
    if len(clean_text) < 3:
        # Try a simpler cleaning
        clean_text = text[:500]  # Just take first 500 chars
        clean_text = re.sub(r'[^\w\s.,!?\-]', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    print(f"[TTS Clean] Original: {text[:50]}...")
    print(f"[TTS Clean] Cleaned: {clean_text[:50]}...")
    print(f"[TTS Clean] Length: {len(clean_text)}")
    
    return clean_text