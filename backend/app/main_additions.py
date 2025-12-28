"""
KOMAS Trading Server - Main.py Additions
=========================================
Add this import and router registration to main.py

Chat #48: Preset Optimizer Heatmap
"""

# ============================================================================
# ADD TO IMPORTS SECTION (around line 20-30)
# ============================================================================

from app.api.heatmap_routes import router as heatmap_router

# ============================================================================
# ADD TO ROUTER REGISTRATION SECTION (around line 80-100)
# ============================================================================

# Optimizer Heatmap routes (Chat #48)
app.include_router(heatmap_router)
