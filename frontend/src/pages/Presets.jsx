/**
 * Presets Page - Library of TRG and Dominant presets
 * 
 * Features:
 * - View all presets (TRG 200 + Dominant 125 + User custom)
 * - Search and filter by indicator, category, source
 * - Create, edit, clone, delete presets
 * - Import/Export presets
 * - Backup/Restore functionality
 * - Batch operations
 * 
 * Chat: #31-33 — Presets Full Module
 */
import { useState, useEffect, useCallback } from 'react';
import PresetCard from '../components/Presets/PresetCard';
import PresetModal from '../components/Presets/PresetModal';
import PresetOptimizerModal from '../components/Presets/PresetOptimizerModal';
import { Button, Card, Input, Select, Spinner, Alert } from '../components/ui';

// API base URL
const API_URL = 'http://localhost:8000';

// Categories with icons
const CATEGORIES = [
  { value: '', label: 'Все категории', icon: '📁' },
  { value: 'scalp', label: 'Скальп', icon: '⚡' },
  { value: 'short-term', label: 'Краткосрочные', icon: '🎯' },
  { value: 'mid-term', label: 'Среднесрочные', icon: '📊' },
  { value: 'swing', label: 'Свинг', icon: '🌊' },
  { value: 'long-term', label: 'Долгосрочные', icon: '📈' },
  { value: 'special', label: 'Специальные', icon: '⭐' },
];

// Indicators
const INDICATORS = [
  { value: '', label: 'Все индикаторы', icon: '📊' },
  { value: 'trg', label: 'TRG', icon: '📈' },
  { value: 'dominant', label: 'Dominant', icon: '🎯' },
];

// Sources
const SOURCES = [
  { value: '', label: 'Все источники', icon: '📁' },
  { value: 'system', label: 'Системные', icon: '🔧' },
  { value: 'pine_script', label: 'Pine Script', icon: '🌲' },
  { value: 'user', label: 'Пользовательские', icon: '👤' },
  { value: 'imported', label: 'Импортированные', icon: '📥' },
  { value: 'optimizer', label: 'Оптимизатор', icon: '🔬' },
];

export default function Presets() {
  // State
  const [presets, setPresets] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters
  const [search, setSearch] = useState('');
  const [indicator, setIndicator] = useState('');
  const [category, setCategory] = useState('');
  const [source, setSource] = useState('');
  const [showFavorites, setShowFavorites] = useState(false);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalPresets, setTotalPresets] = useState(0);
  const ITEMS_PER_PAGE = 24;
  
  // Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // create, edit, clone
  const [selectedPreset, setSelectedPreset] = useState(null);
  
  // Selection for batch operations
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [selectMode, setSelectMode] = useState(false);
  const [optimizerOpen, setOptimizerOpen] = useState(false);
  
  // Load presets
  const loadPresets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (indicator) params.append('indicator_type', indicator);
      if (category) params.append('category', category);
      if (source) params.append('source', source);
      if (showFavorites) params.append('is_favorite', 'true');
      params.append('limit', ITEMS_PER_PAGE.toString());
      params.append('offset', ((page - 1) * ITEMS_PER_PAGE).toString());
      
      const response = await fetch(`${API_URL}/api/presets/list?${params}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to load presets');
      }
      
      setPresets(data.presets || []);
      setTotalPresets(data.total || 0);
      setTotalPages(Math.ceil((data.total || 0) / ITEMS_PER_PAGE));
      
    } catch (err) {
      console.error('Error loading presets:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [search, indicator, category, source, showFavorites, page]);
  
  // Load stats
  const loadStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/presets/stats`);
      const data = await response.json();
      if (response.ok) {
        setStats(data);
      }
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };
  
  // Initial load
  useEffect(() => {
    loadPresets();
    loadStats();
  }, [loadPresets]);
  
  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [search, indicator, category, source, showFavorites]);
  
  // Handlers
  const handleCreate = () => {
    setSelectedPreset(null);
    setModalMode('create');
    setModalOpen(true);
  };
  
  const handleEdit = (preset) => {
    setSelectedPreset(preset);
    setModalMode('edit');
    setModalOpen(true);
  };
  
  const handleClone = (preset) => {
    setSelectedPreset(preset);
    setModalMode('clone');
    setModalOpen(true);
  };
  
  const handleDelete = async (preset) => {
    if (!confirm(`Удалить пресет "${preset.name}"?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/presets/${preset.id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete');
      }
      
      loadPresets();
      loadStats();
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    }
  };
  
  const handleToggleFavorite = async (preset) => {
    try {
      const response = await fetch(`${API_URL}/api/presets/${preset.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_favorite: !preset.is_favorite })
      });
      
      if (response.ok) {
        loadPresets();
      }
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  };
  
  const handleApplyToIndicator = (preset) => {
    // Store preset in localStorage and redirect to indicator page
    localStorage.setItem('komas_apply_preset', JSON.stringify(preset));
    window.location.href = '/';
  };
  
  const handleModalSave = async (presetData) => {
    try {
      let url = `${API_URL}/api/presets`;
      let method = 'POST';
      
      if (modalMode === 'edit') {
        url = `${API_URL}/api/presets/${selectedPreset.id}`;
        method = 'PUT';
      } else if (modalMode === 'clone') {
        url = `${API_URL}/api/presets/clone/${selectedPreset.id}?new_name=${encodeURIComponent(presetData.name)}`;
        method = 'POST';
      } else {
        url = `${API_URL}/api/presets/create`;
      }
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: modalMode === 'clone' ? undefined : JSON.stringify(presetData)
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Operation failed');
      }
      
      setModalOpen(false);
      loadPresets();
      loadStats();
      
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    }
  };
  
  // Export preset
  const handleExport = async (preset) => {
    try {
      const response = await fetch(`${API_URL}/api/presets/export/${preset.id}`);
      const data = await response.json();
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${preset.name.replace(/\s+/g, '_')}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Ошибка экспорта: ${err.message}`);
    }
  };
  
  // Import preset
  const handleImport = async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      try {
        const text = await file.text();
        const data = JSON.parse(text);
        
        const response = await fetch(`${API_URL}/api/presets/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
          throw new Error(result.detail || 'Import failed');
        }
        
        alert('Пресет успешно импортирован!');
        loadPresets();
        loadStats();
      } catch (err) {
        alert(`Ошибка импорта: ${err.message}`);
      }
    };
    input.click();
  };
  
  // Backup all presets
  const handleBackup = async () => {
    try {
      const params = new URLSearchParams();
      if (indicator) params.append('indicator_type', indicator);
      if (source) params.append('source', source);
      params.append('format', 'json');
      
      const response = await fetch(`${API_URL}/api/presets/backup?${params}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `komas_presets_backup_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      alert(`Создан бэкап ${data.total_presets} пресетов`);
    } catch (err) {
      alert(`Ошибка бэкапа: ${err.message}`);
    }
  };
  
  // Restore from backup
  const handleRestore = async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json,.zip';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      const mode = prompt('Режим восстановления:\n- skip: пропустить существующие\n- replace: заменить существующие\n- merge: обновить существующие, создать новые', 'skip');
      
      if (!mode || !['skip', 'replace', 'merge'].includes(mode)) {
        alert('Неверный режим');
        return;
      }
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_URL}/api/presets/restore?mode=${mode}`, {
          method: 'POST',
          body: formData
        });
        
        const result = await response.json();
        
        if (!response.ok) {
          throw new Error(result.detail || 'Restore failed');
        }
        
        alert(`Восстановление завершено!\nСоздано: ${result.created}\nОбновлено: ${result.updated}\nПропущено: ${result.skipped}\nОшибок: ${result.errors}`);
        loadPresets();
        loadStats();
      } catch (err) {
        alert(`Ошибка восстановления: ${err.message}`);
      }
    };
    input.click();
  };
  
  // Seed TRG presets (200 system presets)
  const [seedingTrg, setSeedingTrg] = useState(false);
  const handleSeedTrg = async () => {
    if (!confirm('Сгенерировать 200 системных TRG пресетов?\n\nGrid:\n- 8 × i1: [14, 25, 40, 60, 80, 110, 150, 200]\n- 5 × i2: [2.0, 3.0, 4.0, 5.5, 7.5]\n- 5 × filters: [N, T, M, S, F]')) {
      return;
    }
    
    try {
      setSeedingTrg(true);
      const response = await fetch(`${API_URL}/api/presets/trg/seed?force=false`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || 'TRG seed failed');
      }
      
      alert(`TRG пресеты сгенерированы!\n\nСоздано: ${result.saved}\nПропущено: ${result.skipped}\nОшибок: ${result.errors}\n\nВсего TRG: ${result.total_trg}`);
      loadPresets();
      loadStats();
    } catch (err) {
      alert(`Ошибка генерации TRG: ${err.message}`);
    } finally {
      setSeedingTrg(false);
    }
  };
  
  // Seed Dominant presets (125 system presets from GG Pine Script)
  const [seedingDominant, setSeedingDominant] = useState(false);
  const handleSeedDominant = async () => {
    if (!confirm('Сгенерировать 125 системных Dominant пресетов из GG Pine Script?')) {
      return;
    }
    
    try {
      setSeedingDominant(true);
      const response = await fetch(`${API_URL}/api/presets/dominant/seed?force=false`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || 'Dominant seed failed');
      }
      
      alert(`Dominant пресеты сгенерированы!\n\nСоздано: ${result.created}\nПропущено: ${result.skipped}\nОшибок: ${result.errors}\n\nВсего Dominant: ${result.total_dominant}`);
      loadPresets();
      loadStats();
    } catch (err) {
      alert(`Ошибка генерации Dominant: ${err.message}`);
    } finally {
      setSeedingDominant(false);
    }
  };
  
  // Batch delete
  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;
    
    if (!confirm(`Удалить ${selectedIds.size} выбранных пресетов?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/presets/batch/delete?confirm=true`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Array.from(selectedIds))
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || 'Batch delete failed');
      }
      
      alert(`Удалено: ${result.deleted} пресетов`);
      setSelectedIds(new Set());
      setSelectMode(false);
      loadPresets();
      loadStats();
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    }
  };
  
  // Toggle select
  const handleToggleSelect = (presetId) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(presetId)) {
      newSelected.delete(presetId);
    } else {
      newSelected.add(presetId);
    }
    setSelectedIds(newSelected);
  };
  
  // Select all on page
  const handleSelectAll = () => {
    const pageIds = presets.map(p => p.id);
    const allSelected = pageIds.every(id => selectedIds.has(id));
    
    const newSelected = new Set(selectedIds);
    if (allSelected) {
      pageIds.forEach(id => newSelected.delete(id));
    } else {
      pageIds.forEach(id => newSelected.add(id));
    }
    setSelectedIds(newSelected);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            🎛️ Библиотека пресетов
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {stats ? (
              <>
                Всего: {stats.total_presets} | 
                TRG: {stats.by_indicator?.trg || 0} | 
                Dominant: {stats.by_indicator?.dominant || 0} | 
                ⭐ Избранные: {stats.favorites || 0}
              </>
            ) : 'Загрузка статистики...'}
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="primary" onClick={handleCreate}>
            ➕ Создать
          </Button>
          <Button variant="success" onClick={handleImport}>
            📥 Импорт
          </Button>
          <Button
            variant="secondary"
            onClick={handleBackup}
            className="bg-purple-600 hover:bg-purple-700 border-purple-600"
          >
            💾 Бэкап
          </Button>
          <Button variant="warning" onClick={handleRestore}>
            📤 Восстановить
          </Button>
          <Button
            variant="warning"
            onClick={handleSeedTrg}
            disabled={seedingTrg}
            title="Сгенерировать 200 системных TRG пресетов"
            className="bg-yellow-600 hover:bg-yellow-700 border-yellow-600"
          >
            {seedingTrg ? '⏳' : '📈'} Seed TRG (200)
          </Button>
          <Button
            variant="secondary"
            onClick={handleSeedDominant}
            disabled={seedingDominant}
            title="Сгенерировать 125 системных Dominant пресетов из GG Pine Script"
            className="bg-teal-600 hover:bg-teal-700 border-teal-600"
          >
            {seedingDominant ? '⏳' : '🎯'} Seed Dominant (125)
          </Button>
          <Button
            variant="warning"
            onClick={() => setOptimizerOpen(true)}
            title="Оптимизация пресетов по нескольким парам"
          >
            🔥 Оптимизация
          </Button>
        </div>
      </div>
      
      {/* Filters */}
      <Card>
        <Card.Body className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <Input
                type="text"
                placeholder="🔍 Поиск по названию..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            {/* Indicator */}
            <Select
              value={indicator}
              onChange={(e) => setIndicator(e.target.value)}
            >
              {INDICATORS.map(ind => (
                <option key={ind.value} value={ind.value}>
                  {ind.icon} {ind.label}
                </option>
              ))}
            </Select>

            {/* Category */}
            <Select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {CATEGORIES.map(cat => (
                <option key={cat.value} value={cat.value}>
                  {cat.icon} {cat.label}
                </option>
              ))}
            </Select>

            {/* Source */}
            <Select
              value={source}
              onChange={(e) => setSource(e.target.value)}
            >
              {SOURCES.map(src => (
                <option key={src.value} value={src.value}>
                  {src.icon} {src.label}
                </option>
              ))}
            </Select>

            {/* Favorites toggle */}
            <Button
              variant={showFavorites ? 'warning' : 'secondary'}
              onClick={() => setShowFavorites(!showFavorites)}
              className={showFavorites ? 'bg-yellow-600 border-yellow-500' : ''}
            >
              ⭐ Избранные
            </Button>

            {/* Select mode */}
            <Button
              variant={selectMode ? 'danger' : 'secondary'}
              onClick={() => {
                setSelectMode(!selectMode);
                if (selectMode) setSelectedIds(new Set());
              }}
            >
              ✓ Выбор
            </Button>
          </div>
        
          {/* Batch actions */}
          {selectMode && selectedIds.size > 0 && (
            <div className="mt-4 flex items-center gap-4 p-3 bg-gray-700 rounded-lg">
              <span className="text-gray-300">
                Выбрано: <span className="text-white font-bold">{selectedIds.size}</span>
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSelectAll}
              >
                {presets.every(p => selectedIds.has(p.id)) ? 'Снять все' : 'Выбрать все'}
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleBatchDelete}
              >
                🗑️ Удалить выбранные
              </Button>
            </div>
          )}
        </Card.Body>
      </Card>
      
      {/* Error */}
      {error && (
        <Alert variant="danger" className="mb-6">
          ⚠️ {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
          <span className="ml-3 text-gray-400">Загрузка пресетов...</span>
        </div>
      )}
      
      {/* Empty state */}
      {!loading && presets.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <div className="text-6xl mb-4">📭</div>
          <p>Пресеты не найдены</p>
          <p className="text-sm mt-2">Попробуйте изменить фильтры или создать новый пресет</p>
        </div>
      )}
      
      {/* Presets grid */}
      {!loading && presets.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-6">
            {presets.map(preset => (
              <PresetCard
                key={preset.id}
                preset={preset}
                selectMode={selectMode}
                isSelected={selectedIds.has(preset.id)}
                onToggleSelect={() => handleToggleSelect(preset.id)}
                onEdit={() => handleEdit(preset)}
                onClone={() => handleClone(preset)}
                onDelete={() => handleDelete(preset)}
                onExport={() => handleExport(preset)}
                onToggleFavorite={() => handleToggleFavorite(preset)}
                onApply={() => handleApplyToIndicator(preset)}
              />
            ))}
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="secondary"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                ◀ Назад
              </Button>

              <span className="px-4 py-2 text-gray-400">
                Страница {page} из {totalPages} ({totalPresets} пресетов)
              </span>

              <Button
                variant="secondary"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Вперед ▶
              </Button>
            </div>
          )}
        </>
      )}
      
      {/* Modal */}
      {modalOpen && (
        <PresetModal
          mode={modalMode}
          preset={selectedPreset}
          onClose={() => setModalOpen(false)}
          onSave={handleModalSave}
        />
      )}
      
      {/* Optimizer Modal */}
      <PresetOptimizerModal
        isOpen={optimizerOpen}
        onClose={() => setOptimizerOpen(false)}
        indicatorType={indicator || 'all'}
      />
    </div>
  );
}
