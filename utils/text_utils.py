import re

def remove_accents_and_lowercase(input_str: str) -> str:
    """
    Removes Vietnamese accents from a string and converts it to lowercase.
    """
    if not isinstance(input_str, str):
        return ""
        
    s = input_str.lower()
    
    # Vietnamese accents mapping
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[đ]', 'd', s)
    
    return s.strip()
