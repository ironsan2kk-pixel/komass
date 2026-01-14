"""
Apply patch for Dominant optimization support
"""
import os

def apply_patch():
    filepath = os.path.join(os.path.dirname(__file__), 'backend', 'app', 'api', 'indicator_routes.py')
    
    if not os.path.exists(filepath):
        # Try alternative path
        filepath = 'indicator_routes.py'
    
    if not os.path.exists(filepath):
        print(f"ERROR: Cannot find indicator_routes.py")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if patch already applied
    if 'Dominant indicator - optimization not yet supported' in content:
        print("Patch already applied!")
        return True
    
    # Find the insertion point
    old_code = '''    settings = request.settings
    mode = request.mode
    metric = request.metric
    
    async def generate():'''
    
    new_code = '''    settings = request.settings
    mode = request.mode
    metric = request.metric
    
    # Check if Dominant indicator - optimization not yet supported
    if settings.indicator_type == "dominant":
        async def generate_dominant_error():
            yield f"data: {json_lib.dumps({'type': 'error', 'message': 'Оптимизация для Dominant индикатора пока не реализована. Используйте пресеты из библиотеки (125 готовых конфигураций).'})}" + "\\n\\n"
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            generate_dominant_error(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    async def generate():'''
    
    if old_code not in content:
        print("ERROR: Could not find insertion point. File may have been modified.")
        return False
    
    content = content.replace(old_code, new_code)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Patch applied successfully!")
    return True

if __name__ == '__main__':
    import sys
    if not apply_patch():
        sys.exit(1)
