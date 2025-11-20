"""
Slide type handlers for rendering and validation.

This module provides functions for rendering different slide types
and validating slide completion based on user interactions.
"""

from app.utils.validators import sanitize_html_content


def render_slide(slide_data):
    """
    Render HTML for a slide based on its type.
    
    Args:
        slide_data: Dictionary containing slide data with 'type' key
        
    Returns:
        str: HTML content for the slide
    """
    slide_type = slide_data.get('type')
    
    if slide_type == 'title':
        return render_title_slide(slide_data)
    elif slide_type == 'content':
        return render_content_slide(slide_data)
    elif slide_type == 'video':
        return render_video_slide(slide_data)
    elif slide_type == 'image':
        return render_image_slide(slide_data)
    elif slide_type == 'quiz':
        return render_quiz_slide(slide_data)
    else:
        return '<div class="alert alert-warning">Type de diapositive inconnu</div>'


def render_title_slide(slide_data):
    """
    Render a title slide.
    
    Args:
        slide_data: Dictionary with 'title' and optional 'subtitle'
        
    Returns:
        str: HTML for title slide
    """
    title = sanitize_html_content(slide_data.get('title', ''))
    subtitle = sanitize_html_content(slide_data.get('subtitle', ''))
    
    html = '<div class="slide slide-title text-center">'
    html += f'<h1 class="slide-title">{title}</h1>'
    
    if subtitle:
        html += f'<p class="slide-subtitle lead">{subtitle}</p>'
    
    html += '</div>'
    
    return html


def render_content_slide(slide_data):
    """
    Render a content slide with text and optional media.
    
    Args:
        slide_data: Dictionary with 'content', optional 'title'
        
    Returns:
        str: HTML for content slide
    """
    title = sanitize_html_content(slide_data.get('title', ''))
    content = sanitize_html_content(slide_data.get('content', ''))
    
    html = '<div class="slide slide-content">'
    
    if title:
        html += f'<h2 class="slide-heading">{title}</h2>'
    
    html += f'<div class="slide-body">{content}</div>'
    html += '</div>'
    
    return html


def render_video_slide(slide_data):
    """
    Render a video slide with embedded video player.
    
    Args:
        slide_data: Dictionary with 'video_url', optional 'title', 'description'
        
    Returns:
        str: HTML for video slide
    """
    title = sanitize_html_content(slide_data.get('title', ''))
    description = sanitize_html_content(slide_data.get('description', ''))
    video_url = slide_data.get('video_url', '')
    
    # Convert common video URLs to embed format
    embed_url = _convert_to_embed_url(video_url)
    
    html = '<div class="slide slide-video">'
    
    if title:
        html += f'<h2 class="slide-heading">{title}</h2>'
    
    if description:
        html += f'<p class="slide-description">{description}</p>'
    
    html += '<div class="video-container ratio ratio-16x9">'
    html += f'<iframe src="{embed_url}" '
    html += 'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
    html += 'encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
    html += '</div>'
    html += '</div>'
    
    return html


def render_image_slide(slide_data):
    """
    Render an image slide.
    
    Args:
        slide_data: Dictionary with 'image_url', optional 'title', 'caption'
        
    Returns:
        str: HTML for image slide
    """
    title = sanitize_html_content(slide_data.get('title', ''))
    caption = sanitize_html_content(slide_data.get('caption', ''))
    image_url = slide_data.get('image_url', '')
    alt_text = slide_data.get('alt_text', 'Image')
    
    html = '<div class="slide slide-image">'
    
    if title:
        html += f'<h2 class="slide-heading">{title}</h2>'
    
    html += '<div class="image-container text-center">'
    html += f'<img src="{image_url}" alt="{alt_text}" class="img-fluid">'
    html += '</div>'
    
    if caption:
        html += f'<p class="slide-caption text-center mt-3">{caption}</p>'
    
    html += '</div>'
    
    return html


def render_quiz_slide(slide_data):
    """
    Render a quiz slide placeholder (actual quiz is loaded separately).
    
    Args:
        slide_data: Dictionary with 'quiz_id'
        
    Returns:
        str: HTML for quiz slide placeholder
    """
    quiz_id = slide_data.get('quiz_id', 0)
    title = sanitize_html_content(slide_data.get('title', 'Quiz'))
    
    html = '<div class="slide slide-quiz">'
    html += f'<h2 class="slide-heading">{title}</h2>'
    html += '<div class="alert alert-info">'
    html += '<i class="bi bi-question-circle"></i> '
    html += 'Vous devez compléter le quiz pour continuer.'
    html += '</div>'
    html += f'<div id="quiz-container" data-quiz-id="{quiz_id}">'
    html += '<!-- Quiz sera chargé ici -->'
    html += '</div>'
    html += '</div>'
    
    return html


def validate_slide_completion(slide_type, user_interaction=None):
    """
    Validate if a user can proceed from a slide based on required interactions.
    
    Args:
        slide_type: Type of the slide ('title', 'content', 'video', 'image', 'quiz')
        user_interaction: Optional dictionary with interaction data
                         For quiz slides: {'quiz_passed': True/False}
                         For video slides: {'watched': True/False}
        
    Returns:
        tuple: (can_proceed: bool, reason: str)
    """
    # Title and content slides can always be completed
    if slide_type in ['title', 'content', 'image']:
        return True, None
    
    # Video slides require watching (in basic implementation, auto-proceed)
    if slide_type == 'video':
        if user_interaction and user_interaction.get('watched'):
            return True, None
        # For now, allow proceeding without validation
        return True, None
    
    # Quiz slides require passing the quiz
    if slide_type == 'quiz':
        if not user_interaction:
            return False, "Vous devez compléter le quiz pour continuer."
        
        if not user_interaction.get('quiz_passed'):
            return False, "Vous devez réussir le quiz pour continuer."
        
        return True, None
    
    # Unknown slide type
    return True, None


def _convert_to_embed_url(video_url):
    """
    Convert common video URLs to embeddable format.
    
    Args:
        video_url: Original video URL
        
    Returns:
        str: Embed-ready URL
    """
    # YouTube URLs
    if 'youtube.com/watch' in video_url:
        # Extract video ID from URL like https://www.youtube.com/watch?v=VIDEO_ID
        video_id = video_url.split('v=')[1].split('&')[0] if 'v=' in video_url else None
        if video_id:
            return f'https://www.youtube.com/embed/{video_id}'
    
    elif 'youtu.be/' in video_url:
        # Extract video ID from short URL like https://youtu.be/VIDEO_ID
        video_id = video_url.split('youtu.be/')[1].split('?')[0] if 'youtu.be/' in video_url else None
        if video_id:
            return f'https://www.youtube.com/embed/{video_id}'
    
    # Vimeo URLs
    elif 'vimeo.com/' in video_url:
        # Extract video ID from URL like https://vimeo.com/VIDEO_ID
        video_id = video_url.split('vimeo.com/')[1].split('?')[0] if 'vimeo.com/' in video_url else None
        if video_id:
            return f'https://player.vimeo.com/video/{video_id}'
    
    # If already an embed URL or unknown format, return as-is
    return video_url
