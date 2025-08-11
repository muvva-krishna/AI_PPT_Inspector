import base64

def image_to_base64(img_bytes):
    """Convert raw image bytes to base64 string."""
    return base64.b64encode(img_bytes).decode('utf-8')
