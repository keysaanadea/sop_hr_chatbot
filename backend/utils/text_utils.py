"""
DENAI Text Utils
Text cleaning and processing utilities for TTS and chat
"""

import re
import logging

logger = logging.getLogger(__name__)

# TTS text cleaning constants
TTS_EMOJIS_TO_REMOVE = [
    '✅', '❌', '🔒', '⏰', '❓', '🌐', '📞', '💰', '🎯', 
    '🚀', '🤖', '📊', '📈', '📉', '💡', '🔥', '🎤', '🔊'
]

HTML_TAG_PATTERNS = [
    r'<h3>.*?</h3>',  # Remove section titles
    r'<[^>]*>',       # Remove all HTML tags
]

TEXT_CLEANUP_PATTERNS = [
    (r'\s+', ' '),                      # Multiple spaces to single space
    (r'\n+', '\n'),                     # Multiple newlines to single newline
    (r'[•\-\*]\s*', ''),               # Remove bullet points
    (r'Rujukan Dokumen.*', ''),         # Remove document references
    (r'Sumber:.*?(?=\n|$)', ''),       # Remove source lines
    (r'Bagian:.*?(?=\n|$)', ''),       # Remove section lines
]


class TextCleaner:
    """Text cleaning utilities for different use cases"""
    
    @staticmethod
    def clean_for_tts(html_text: str, preserve_structure: bool = False) -> str:
        """
        Clean HTML text for natural TTS speech
        
        Args:
            html_text: Input HTML text
            preserve_structure: Whether to preserve some structure
            
        Returns:
            str: Cleaned text suitable for TTS
        """
        if not html_text:
            return html_text
        
        logger.debug("🧹 Cleaning text for natural TTS")
        
        text = html_text
        
        # Remove section titles and HTML tags
        for pattern in HTML_TAG_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        
        # Apply text cleanup patterns
        for pattern, replacement in TEXT_CLEANUP_PATTERNS:
            text = re.sub(pattern, replacement, text)
        
        # Remove problematic emojis
        for emoji in TTS_EMOJIS_TO_REMOVE:
            text = text.replace(emoji, '')
        
        # Final cleanup
        text = text.strip()
        
        logger.debug(f"Text cleaned: {len(html_text)} → {len(text)} chars")
        
        return text
    
    @staticmethod
    def clean_for_display(text: str) -> str:
        """
        Clean text for display purposes (minimal cleaning)
        
        Args:
            text: Input text
            
        Returns:
            str: Lightly cleaned text
        """
        if not text:
            return text
        
        # Basic cleanup only
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        text = text.strip()
        
        return text
    
    @staticmethod
    def truncate_for_mode(text: str, mode: str = "chat", max_length: int = None) -> str:
        """
        Truncate text based on conversation mode
        
        Args:
            text: Input text
            mode: Conversation mode ("chat" or "call")
            max_length: Custom max length
            
        Returns:
            str: Truncated text
        """
        if not text:
            return text
        
        # Default lengths by mode
        if max_length is None:
            max_length = 150 if mode == "call" else 2000
        
        if len(text) <= max_length:
            return text
        
        # Truncate with ellipsis
        if mode == "call":
            return text[:max_length-15] + "... Butuh detail?"
        else:
            return text[:max_length-3] + "..."
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> list[str]:
        """
        Extract keywords from text for search/indexing
        
        Args:
            text: Input text
            min_length: Minimum word length
            
        Returns:
            list[str]: List of keywords
        """
        if not text:
            return []
        
        # Remove HTML and special characters
        clean_text = re.sub(r'<[^>]*>', ' ', text)
        clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
        
        # Extract words
        words = clean_text.lower().split()
        
        # Filter by length and common stop words
        stop_words = {
            'dan', 'atau', 'yang', 'untuk', 'pada', 'dalam', 'dengan', 'dari',
            'adalah', 'akan', 'dapat', 'harus', 'bisa', 'ada', 'tidak', 'ini',
            'itu', 'the', 'and', 'or', 'for', 'in', 'with', 'from', 'is', 'will'
        }
        
        keywords = [
            word for word in words 
            if len(word) >= min_length and word not in stop_words
        ]
        
        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for word in keywords:
            if word not in seen:
                unique_keywords.append(word)
                seen.add(word)
        
        return unique_keywords[:20]  # Limit to top 20 keywords
    
    @staticmethod
    def format_for_search_display(text: str, query: str = None, max_length: int = 200) -> str:
        """
        Format text for search result display with query highlighting
        
        Args:
            text: Source text
            query: Search query to highlight
            max_length: Maximum display length
            
        Returns:
            str: Formatted text for display
        """
        if not text:
            return ""
        
        # Clean HTML
        clean_text = re.sub(r'<[^>]*>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Find best excerpt around query
        if query and len(clean_text) > max_length:
            query_lower = query.lower()
            text_lower = clean_text.lower()
            
            # Find query position
            query_pos = text_lower.find(query_lower)
            
            if query_pos != -1:
                # Extract around query
                start = max(0, query_pos - max_length // 3)
                end = min(len(clean_text), start + max_length)
                
                excerpt = clean_text[start:end]
                
                # Add ellipsis if truncated
                if start > 0:
                    excerpt = "..." + excerpt
                if end < len(clean_text):
                    excerpt = excerpt + "..."
                
                return excerpt
        
        # Default truncation
        if len(clean_text) <= max_length:
            return clean_text
        
        return clean_text[:max_length-3] + "..."
    
    @staticmethod
    def validate_text_length(text: str, max_chars: int = 5000) -> tuple[bool, str]:
        """
        Validate text length for processing
        
        Args:
            text: Text to validate
            max_chars: Maximum allowed characters
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Text is empty"
        
        if len(text) > max_chars:
            return False, f"Text too long: {len(text)} chars (max {max_chars})"
        
        return True, ""


# Convenience functions
def clean_text_for_tts(text: str) -> str:
    """Convenience function for TTS text cleaning"""
    return TextCleaner.clean_for_tts(text)


def clean_text_for_display(text: str) -> str:
    """Convenience function for display text cleaning"""
    return TextCleaner.clean_for_display(text)


def truncate_for_call_mode(text: str) -> str:
    """Convenience function for call mode truncation"""
    return TextCleaner.truncate_for_mode(text, mode="call")