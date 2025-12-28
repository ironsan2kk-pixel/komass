"""
KOMAS Trading Server - Optimizer UI Tests
==========================================
Unit tests for the Optimizer page functionality.

Chat #49: Optimizer UI
"""

import pytest
import json
from pathlib import Path


class TestOptimizerUIStructure:
    """Test Optimizer.jsx structure and components"""
    
    def test_optimizer_file_exists(self):
        """Verify Optimizer.jsx file exists"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        assert optimizer_path.exists(), "Optimizer.jsx should exist"
    
    def test_optimizer_imports(self):
        """Verify all required imports are present"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        required_imports = [
            'ModeSelector',
            'ResultsPanel',
            'HeatmapPanel',
            'HistoryPanel',
            'optimizerApi'
        ]
        
        for imp in required_imports:
            assert imp in content, f"Missing import: {imp}"
    
    def test_optimizer_tabs(self):
        """Verify all tabs are defined"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        required_tabs = ['optimize', 'results', 'heatmap', 'history']
        
        for tab in required_tabs:
            assert f"id: '{tab}'" in content, f"Missing tab: {tab}"
    
    def test_optimizer_timeframes(self):
        """Verify timeframe options"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        timeframes = ['5m', '15m', '30m', '1h', '2h', '4h', '1d']
        
        for tf in timeframes:
            assert f"value: '{tf}'" in content, f"Missing timeframe: {tf}"


class TestOptimizerUIFeatures:
    """Test Optimizer.jsx features"""
    
    def test_preset_selector_component(self):
        """Verify PresetSelector component exists"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'PresetSelector' in content
        assert 'selectedPresets' in content
        assert 'setSelectedPresets' in content
    
    def test_pair_selector_component(self):
        """Verify PairSelector component exists"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'PairSelector' in content
        assert 'selectedPairs' in content
        assert 'setSelectedPairs' in content
    
    def test_progress_bar_component(self):
        """Verify ProgressBar component exists"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'ProgressBar' in content
        assert 'progress' in content
        assert 'elapsed' in content
    
    def test_quick_select_buttons(self):
        """Verify quick select buttons for pairs"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        quick_selects = ['majors', 'top10', 'top20']
        
        for qs in quick_selects:
            assert qs in content, f"Missing quick select: {qs}"
    
    def test_start_optimization_function(self):
        """Verify start optimization function"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'startOptimization' in content
        assert '/api/optimizer/presets/stream' in content
    
    def test_cancel_optimization_function(self):
        """Verify cancel optimization function"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'cancelOptimization' in content
    
    def test_sse_streaming_handling(self):
        """Verify SSE streaming handling"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert "data.event === 'progress'" in content
        assert "data.event === 'complete'" in content
        assert "data.event === 'error'" in content


class TestAppNavigation:
    """Test App.jsx navigation"""
    
    def test_app_file_exists(self):
        """Verify App.jsx file exists"""
        app_path = Path('frontend/src/App.jsx')
        assert app_path.exists(), "App.jsx should exist"
    
    def test_optimizer_import(self):
        """Verify Optimizer is imported in App.jsx"""
        app_path = Path('frontend/src/App.jsx')
        content = app_path.read_text(encoding='utf-8')
        
        assert "import Optimizer from './pages/Optimizer'" in content
    
    def test_optimizer_route(self):
        """Verify Optimizer route is defined"""
        app_path = Path('frontend/src/App.jsx')
        content = app_path.read_text(encoding='utf-8')
        
        assert "/optimizer" in content
        assert "Оптимизация" in content
    
    def test_all_pages_imported(self):
        """Verify all pages are imported"""
        app_path = Path('frontend/src/App.jsx')
        content = app_path.read_text(encoding='utf-8')
        
        pages = ['Indicator', 'Data', 'Presets', 'Optimizer', 'Settings', 'Signals', 'Bots']
        
        for page in pages:
            assert f"import {page}" in content, f"Missing page import: {page}"


class TestOptimizerComponentIntegration:
    """Test Optimizer component integration"""
    
    def test_mode_selector_props(self):
        """Verify ModeSelector receives correct props"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'modes={modes}' in content
        assert 'selected={selectedMode}' in content
        assert 'onChange={setSelectedMode}' in content
    
    def test_results_panel_props(self):
        """Verify ResultsPanel receives correct props"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'result={results}' in content
        assert 'onClose=' in content
    
    def test_heatmap_panel_props(self):
        """Verify HeatmapPanel receives correct props"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'runId={currentRunId}' in content
    
    def test_history_panel_props(self):
        """Verify HistoryPanel receives correct props"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'onLoad={loadResults}' in content
        assert 'currentRunId={currentRunId}' in content


class TestOptimizerStateManagement:
    """Test Optimizer state management"""
    
    def test_required_state_variables(self):
        """Verify all required state variables exist"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        state_vars = [
            'activeTab',
            'presets',
            'pairs',
            'modes',
            'loadingData',
            'selectedPresets',
            'selectedPairs',
            'selectedMode',
            'timeframe',
            'startDate',
            'endDate',
            'isOptimizing',
            'progress',
            'elapsed',
            'estimate',
            'error',
            'currentRunId',
            'results'
        ]
        
        for var in state_vars:
            assert var in content, f"Missing state variable: {var}"
    
    def test_useeffect_hooks(self):
        """Verify useEffect hooks are present"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        # Count useEffect occurrences
        count = content.count('useEffect(')
        assert count >= 3, "Should have at least 3 useEffect hooks"
    
    def test_refs(self):
        """Verify refs are properly used"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'useRef' in content
        assert 'eventSourceRef' in content
        assert 'elapsedTimerRef' in content


class TestOptimizerUIResponsiveness:
    """Test Optimizer UI responsiveness"""
    
    def test_responsive_grid_classes(self):
        """Verify responsive grid classes are used"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        responsive_patterns = [
            'grid-cols-1',
            'md:grid-cols-',
            'lg:grid-cols-'
        ]
        
        for pattern in responsive_patterns:
            assert pattern in content, f"Missing responsive pattern: {pattern}"
    
    def test_tailwind_utility_classes(self):
        """Verify TailwindCSS utility classes are used"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        utilities = [
            'bg-gray-',
            'text-white',
            'rounded-lg',
            'border-gray-',
            'transition-',
            'hover:'
        ]
        
        for util in utilities:
            assert util in content, f"Missing utility class: {util}"


class TestOptimizerErrorHandling:
    """Test Optimizer error handling"""
    
    def test_error_state(self):
        """Verify error state handling"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert "setError(" in content
        assert "error &&" in content or "{error &&" in content
    
    def test_try_catch_blocks(self):
        """Verify try-catch error handling"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'try {' in content
        assert 'catch' in content
    
    def test_loading_states(self):
        """Verify loading states are handled"""
        optimizer_path = Path('frontend/src/pages/Optimizer.jsx')
        content = optimizer_path.read_text(encoding='utf-8')
        
        assert 'loading' in content.lower()
        assert 'Загрузка' in content or 'Loading' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
