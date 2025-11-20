"""
Validation utilities for training content.

This module provides validation functions for training data, slide structures,
and HTML content sanitization with French error messages.
"""

import re
import html


def validate_training_data(data):
    """
    Validate training creation or update data.
    
    Args:
        data: Dictionary containing training data
        
    Returns:
        tuple: (is_valid: bool, errors: list of error messages)
    """
    errors = []
    
    # Check required fields
    if not data.get('title') or not data['title'].strip():
        errors.append("Le titre est requis.")
    elif len(data['title'].strip()) < 3:
        errors.append("Le titre doit contenir au moins 3 caractères.")
    elif len(data['title']) > 200:
        errors.append("Le titre ne peut pas dépasser 200 caractères.")
    
    # Check slides
    if 'slides' in data:
        if not isinstance(data['slides'], list):
            errors.append("Les diapositives doivent être une liste.")
        elif len(data['slides']) == 0:
            errors.append("Au moins une diapositive est requise.")
        else:
            # Validate each slide
            for idx, slide in enumerate(data['slides']):
                slide_errors = validate_slide_structure(slide)
                if slide_errors:
                    for err in slide_errors:
                        errors.append(f"Diapositive {idx + 1}: {err}")
    
    # Validate targeting arrays
    if 'target_roles' in data and data['target_roles']:
        if not isinstance(data['target_roles'], list):
            errors.append("Les rôles ciblés doivent être une liste.")
    
    if 'target_teams' in data and data['target_teams']:
        if not isinstance(data['target_teams'], list):
            errors.append("Les équipes ciblées doivent être une liste.")
    
    if 'target_locations' in data and data['target_locations']:
        if not isinstance(data['target_locations'], list):
            errors.append("Les localisations ciblées doivent être une liste.")
    
    # Validate boolean fields
    if 'is_mandatory' in data and not isinstance(data['is_mandatory'], bool):
        errors.append("Le champ 'obligatoire' doit être un booléen.")
    
    if 'is_published' in data and not isinstance(data['is_published'], bool):
        errors.append("Le champ 'publié' doit être un booléen.")
    
    return len(errors) == 0, errors


def validate_slide_structure(slide):
    """
    Validate an individual slide structure.
    
    Args:
        slide: Dictionary containing slide data
        
    Returns:
        list: List of error messages (empty if valid)
    """
    errors = []
    
    # Check if slide is a dictionary
    if not isinstance(slide, dict):
        errors.append("La diapositive doit être un objet.")
        return errors
    
    # Check slide type
    valid_types = ['title', 'content', 'video', 'image', 'quiz']
    slide_type = slide.get('type')
    
    if not slide_type:
        errors.append("Le type de diapositive est requis.")
    elif slide_type not in valid_types:
        errors.append(f"Type de diapositive invalide. Types valides: {', '.join(valid_types)}")
    
    # Validate based on type
    if slide_type == 'title':
        if not slide.get('title') or not slide['title'].strip():
            errors.append("Le titre est requis pour une diapositive de titre.")
    
    elif slide_type == 'content':
        if not slide.get('content') or not slide['content'].strip():
            errors.append("Le contenu est requis pour une diapositive de contenu.")
    
    elif slide_type == 'video':
        if not slide.get('video_url') or not slide['video_url'].strip():
            errors.append("L'URL de la vidéo est requise pour une diapositive vidéo.")
        elif not _is_valid_url(slide['video_url']):
            errors.append("L'URL de la vidéo n'est pas valide.")
    
    elif slide_type == 'image':
        if not slide.get('image_url') or not slide['image_url'].strip():
            errors.append("L'URL de l'image est requise pour une diapositive image.")
        elif not _is_valid_url(slide['image_url']):
            errors.append("L'URL de l'image n'est pas valide.")
    
    elif slide_type == 'quiz':
        if not slide.get('quiz_id'):
            errors.append("L'ID du quiz est requis pour une diapositive quiz.")
        elif not isinstance(slide['quiz_id'], int):
            errors.append("L'ID du quiz doit être un nombre entier.")
    
    # Validate duration if present
    if 'duration' in slide:
        if not isinstance(slide['duration'], (int, float)):
            errors.append("La durée doit être un nombre.")
        elif slide['duration'] < 0:
            errors.append("La durée ne peut pas être négative.")
    
    return errors


def sanitize_html_content(content):
    """
    Sanitize HTML content to prevent XSS attacks.
    
    This function allows a limited set of safe HTML tags and removes
    potentially dangerous attributes and JavaScript.
    
    Args:
        content: String containing HTML content
        
    Returns:
        str: Sanitized HTML content
    """
    if not content:
        return ""
    
    # Allowed HTML tags
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span', 'div'
    ]
    
    # Allowed attributes per tag
    allowed_attributes = {
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'span': ['class'],
        'div': ['class'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan']
    }
    
    # Remove script tags and their content
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove style tags and their content
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove on* event handlers
    content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\s*on\w+\s*=\s*[^\s>]+', '', content, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
    
    # Remove data: protocol (can be used for XSS)
    content = re.sub(r'data:', '', content, flags=re.IGNORECASE)
    
    # Basic tag validation (simple approach - for production consider using bleach or html5lib)
    # Remove any tags not in allowed_tags
    def clean_tag(match):
        tag_name = match.group(1).lower()
        if tag_name in allowed_tags:
            return match.group(0)
        return ''
    
    content = re.sub(r'<(/?)(\w+)[^>]*>', clean_tag, content)
    
    return content


def _is_valid_url(url):
    """
    Check if a URL is valid.
    
    Args:
        url: String URL to validate
        
    Returns:
        bool: True if URL is valid
    """
    # Simple URL validation pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None
