"""
Validators
Input validation utilities
"""

import re
import validators as val


def is_valid_tiktok_url(url):
    """
    Validate TikTok URL
    
    Args:
        url: URL to validate
    
    Returns:
        bool: True if valid TikTok URL
    """
    if not url:
        return False
    
    # Check if it's a valid URL
    if not val.url(url):
        return False
    
    # TikTok URL patterns
    patterns = [
        r'https?://(www\.)?tiktok\.com/@[\w.-]+/video/\d+',
        r'https?://(www\.)?tiktok\.com/@[\w.-]+',
        r'https?://vm\.tiktok\.com/[\w]+',
        r'https?://vt\.tiktok\.com/[\w]+',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False


def is_valid_profile_url(url):
    """
    Validate TikTok profile URL
    
    Args:
        url: URL to validate
    
    Returns:
        bool: True if valid profile URL
    """
    if not url:
        return False
    
    # Profile URL pattern
    pattern = r'https?://(www\.)?tiktok\.com/@[\w.-]+'
    
    return bool(re.match(pattern, url))


def is_valid_video_url(url):
    """
    Validate TikTok video URL
    
    Args:
        url: URL to validate
    
    Returns:
        bool: True if valid video URL
    """
    if not url:
        return False
    
    # Video URL patterns
    patterns = [
        r'https?://(www\.)?tiktok\.com/@[\w.-]+/video/\d+',
        r'https?://vm\.tiktok\.com/[\w]+',
        r'https?://vt\.tiktok\.com/[\w]+',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False


def sanitize_path(path):
    """
    Sanitize file path
    
    Args:
        path: Path to sanitize
    
    Returns:
        str: Sanitized path
    """
    # Remove invalid characters
    path = re.sub(r'[<>:"|?*]', '', path)
    return path.strip()


def validate_limit(limit, max_limit=None):
    """
    Validate download limit
    
    Args:
        limit: Limit to validate
        max_limit: Maximum allowed limit
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        limit = int(limit)
        
        if limit < 0:
            return False, "Limit cannot be negative"
        
        if max_limit and limit > max_limit:
            return False, f"Limit cannot exceed {max_limit}"
        
        return True, None
        
    except ValueError:
        return False, "Limit must be a number"
