"""
KOMAS Trading Server - Optimization Results Database
=====================================================
SQLite persistence for preset optimization results.

Models:
- PresetOptimizationRun: Complete optimization run metadata and results
- PresetOptimizationScore: Per-preset aggregated scores for a run

Endpoints supported:
- Store completed optimization results
- Query optimization history
- Delete old results
- Aggregation by preset/pair

Chat #47: Preset Optimizer Results
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, create_engine, event, desc, asc
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Database path
DB_DIR = Path(__file__).parent.parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "komas.db"
SQLITE_URL = f"sqlite:///{DB_PATH}"

# Get or create Base
try:
    from app.core.database import Base, DatabaseManager
except ImportError:
    Base = declarative_base()
    DatabaseManager = None


# ============================================================================
# MODELS
# ============================================================================

class PresetOptimizationRun(Base):
    """Complete preset optimization run with all results"""
    __tablename__ = "preset_optimization_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Run identification
    run_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)  # User-friendly name
    
    # Configuration
    mode = Column(String(20), nullable=False)  # quick/standard/smart/full
    timeframe = Column(String(10), nullable=False)
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    
    # Input counts
    original_preset_count = Column(Integer, default=0)
    original_pair_count = Column(Integer, default=0)
    effective_preset_count = Column(Integer, default=0)
    effective_pair_count = Column(Integer, default=0)
    
    # Lists stored as JSON
    preset_ids = Column(JSON, nullable=True)  # List of preset IDs used
    pairs = Column(JSON, nullable=True)  # List of pairs used
    
    # Execution info
    status = Column(String(20), nullable=False, default="pending")  # pending/running/completed/error/cancelled
    total_combinations = Column(Integer, default=0)
    completed_combinations = Column(Integer, default=0)
    num_workers = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    
    # Results summary
    best_preset_id = Column(String(100), nullable=True)
    best_preset_name = Column(String(100), nullable=True)
    best_overall_score = Column(Float, nullable=True)
    best_avg_pnl = Column(Float, nullable=True)
    
    # Full results (JSON)
    top_10_presets = Column(JSON, nullable=True)
    result_matrix = Column(JSON, nullable=True)  # preset_id -> pair -> metrics
    preset_scores = Column(JSON, nullable=True)  # List of PresetAggregateScore dicts
    errors = Column(JSON, nullable=True)  # List of error strings
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_preset_opt_runs_mode_created', 'mode', 'created_at'),
        Index('ix_preset_opt_runs_status', 'status'),
    )


# ============================================================================
# DATA CLASSES FOR RESULTS
# ============================================================================

@dataclass
class OptimizationRunSummary:
    """Summary of an optimization run for listing"""
    run_id: str
    name: Optional[str]
    mode: str
    status: str
    timeframe: str
    preset_count: int
    pair_count: int
    total_combinations: int
    duration_seconds: float
    best_preset_name: Optional[str]
    best_overall_score: Optional[float]
    best_avg_pnl: Optional[float]
    created_at: str
    completed_at: Optional[str]


@dataclass
class OptimizationRunDetail:
    """Full details of an optimization run"""
    run_id: str
    name: Optional[str]
    mode: str
    status: str
    timeframe: str
    start_date: Optional[str]
    end_date: Optional[str]
    original_preset_count: int
    original_pair_count: int
    effective_preset_count: int
    effective_pair_count: int
    preset_ids: List[str]
    pairs: List[str]
    total_combinations: int
    completed_combinations: int
    num_workers: int
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: float
    best_preset_id: Optional[str]
    best_preset_name: Optional[str]
    best_overall_score: Optional[float]
    best_avg_pnl: Optional[float]
    top_10_presets: List[Dict]
    preset_scores: List[Dict]
    result_matrix: Dict
    errors: List[str]
    created_at: str


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class OptimizationResultsManager:
    """CRUD operations for optimization results"""
    
    _engine = None
    _session_factory = None
    
    @classmethod
    def _get_engine(cls):
        """Get or create database engine"""
        if cls._engine is None:
            cls._engine = create_engine(
                SQLITE_URL,
                echo=False,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
            
            # Enable foreign keys
            @event.listens_for(cls._engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()
            
            # Create tables
            Base.metadata.create_all(cls._engine)
            logger.info("✓ Optimization results tables created")
        
        return cls._engine
    
    @classmethod
    def _get_session(cls):
        """Get database session"""
        if cls._session_factory is None:
            cls._session_factory = sessionmaker(
                bind=cls._get_engine(),
                autocommit=False,
                autoflush=False
            )
        return cls._session_factory()
    
    # ========== CREATE ==========
    
    @classmethod
    def save_run(cls, result_dict: Dict) -> str:
        """
        Save completed optimization run to database.
        
        Args:
            result_dict: Full optimization result dictionary
            
        Returns:
            run_id of saved result
        """
        session = cls._get_session()
        try:
            run_id = result_dict.get('run_id', '')
            
            # Check if exists
            existing = session.query(PresetOptimizationRun).filter_by(run_id=run_id).first()
            
            if existing:
                # Update existing
                existing.status = result_dict.get('status', 'completed')
                existing.completed_at = datetime.utcnow()
                existing.completed_combinations = result_dict.get('completed_combinations', 0)
                existing.duration_seconds = result_dict.get('duration_seconds', 0)
                existing.top_10_presets = result_dict.get('top_10_presets', [])
                existing.result_matrix = result_dict.get('result_matrix', {})
                existing.preset_scores = result_dict.get('preset_scores', [])
                existing.errors = result_dict.get('errors', [])
                
                # Extract best preset info
                preset_scores = result_dict.get('preset_scores', [])
                if preset_scores:
                    best = max(preset_scores, key=lambda x: x.get('overall_score', 0))
                    existing.best_preset_id = best.get('preset_id')
                    existing.best_preset_name = best.get('preset_name')
                    existing.best_overall_score = best.get('overall_score')
                    existing.best_avg_pnl = best.get('avg_pnl')
                
                run = existing
            else:
                # Create new
                # Extract best preset info
                preset_scores = result_dict.get('preset_scores', [])
                best_preset_id = None
                best_preset_name = None
                best_overall_score = None
                best_avg_pnl = None
                
                if preset_scores:
                    best = max(preset_scores, key=lambda x: x.get('overall_score', 0))
                    best_preset_id = best.get('preset_id')
                    best_preset_name = best.get('preset_name')
                    best_overall_score = best.get('overall_score')
                    best_avg_pnl = best.get('avg_pnl')
                
                run = PresetOptimizationRun(
                    run_id=run_id,
                    mode=result_dict.get('mode', 'standard'),
                    timeframe=result_dict.get('timeframe', '1h'),
                    start_date=result_dict.get('start_date'),
                    end_date=result_dict.get('end_date'),
                    original_preset_count=result_dict.get('original_preset_count', 0),
                    original_pair_count=result_dict.get('original_pair_count', 0),
                    effective_preset_count=result_dict.get('effective_preset_count', 0),
                    effective_pair_count=result_dict.get('effective_pair_count', 0),
                    preset_ids=result_dict.get('preset_ids', []),
                    pairs=result_dict.get('pairs', []),
                    status=result_dict.get('status', 'completed'),
                    total_combinations=result_dict.get('total_combinations', 0),
                    completed_combinations=result_dict.get('completed_combinations', 0),
                    num_workers=result_dict.get('num_workers', 0),
                    started_at=datetime.fromisoformat(result_dict['started_at']) if result_dict.get('started_at') else None,
                    completed_at=datetime.fromisoformat(result_dict['completed_at']) if result_dict.get('completed_at') else datetime.utcnow(),
                    duration_seconds=result_dict.get('duration_seconds', 0),
                    best_preset_id=best_preset_id,
                    best_preset_name=best_preset_name,
                    best_overall_score=best_overall_score,
                    best_avg_pnl=best_avg_pnl,
                    top_10_presets=result_dict.get('top_10_presets', []),
                    result_matrix=result_dict.get('result_matrix', {}),
                    preset_scores=result_dict.get('preset_scores', []),
                    errors=result_dict.get('errors', [])
                )
                session.add(run)
            
            session.commit()
            logger.info(f"✓ Saved optimization run: {run_id}")
            return run_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save optimization run: {e}")
            raise
        finally:
            session.close()
    
    @classmethod
    def create_pending_run(cls, run_id: str, config: Dict) -> str:
        """
        Create a pending optimization run record.
        
        Args:
            run_id: Unique run identifier
            config: Run configuration
            
        Returns:
            run_id
        """
        session = cls._get_session()
        try:
            run = PresetOptimizationRun(
                run_id=run_id,
                mode=config.get('mode', 'standard'),
                timeframe=config.get('timeframe', '1h'),
                start_date=config.get('start_date'),
                end_date=config.get('end_date'),
                original_preset_count=config.get('original_preset_count', 0),
                original_pair_count=config.get('original_pair_count', 0),
                effective_preset_count=config.get('effective_preset_count', 0),
                effective_pair_count=config.get('effective_pair_count', 0),
                preset_ids=config.get('preset_ids', []),
                pairs=config.get('pairs', []),
                status='pending',
                total_combinations=config.get('total_combinations', 0),
                num_workers=config.get('num_workers', 0),
                started_at=datetime.utcnow()
            )
            session.add(run)
            session.commit()
            return run_id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create pending run: {e}")
            raise
        finally:
            session.close()
    
    # ========== READ ==========
    
    @classmethod
    def get_run(cls, run_id: str) -> Optional[OptimizationRunDetail]:
        """
        Get full details of a specific run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            OptimizationRunDetail or None
        """
        session = cls._get_session()
        try:
            run = session.query(PresetOptimizationRun).filter_by(run_id=run_id).first()
            
            if not run:
                return None
            
            return OptimizationRunDetail(
                run_id=run.run_id,
                name=run.name,
                mode=run.mode,
                status=run.status,
                timeframe=run.timeframe,
                start_date=run.start_date,
                end_date=run.end_date,
                original_preset_count=run.original_preset_count,
                original_pair_count=run.original_pair_count,
                effective_preset_count=run.effective_preset_count,
                effective_pair_count=run.effective_pair_count,
                preset_ids=run.preset_ids or [],
                pairs=run.pairs or [],
                total_combinations=run.total_combinations,
                completed_combinations=run.completed_combinations,
                num_workers=run.num_workers,
                started_at=run.started_at.isoformat() if run.started_at else None,
                completed_at=run.completed_at.isoformat() if run.completed_at else None,
                duration_seconds=run.duration_seconds,
                best_preset_id=run.best_preset_id,
                best_preset_name=run.best_preset_name,
                best_overall_score=run.best_overall_score,
                best_avg_pnl=run.best_avg_pnl,
                top_10_presets=run.top_10_presets or [],
                preset_scores=run.preset_scores or [],
                result_matrix=run.result_matrix or {},
                errors=run.errors or [],
                created_at=run.created_at.isoformat()
            )
        finally:
            session.close()
    
    @classmethod
    def list_runs(
        cls,
        limit: int = 50,
        offset: int = 0,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[OptimizationRunSummary]:
        """
        List optimization runs with optional filtering.
        
        Args:
            limit: Max results
            offset: Skip first N results
            mode: Filter by mode
            status: Filter by status
            sort_by: Sort field
            sort_order: 'asc' or 'desc'
            
        Returns:
            List of OptimizationRunSummary
        """
        session = cls._get_session()
        try:
            query = session.query(PresetOptimizationRun)
            
            # Filters
            if mode:
                query = query.filter(PresetOptimizationRun.mode == mode)
            if status:
                query = query.filter(PresetOptimizationRun.status == status)
            
            # Sorting
            sort_col = getattr(PresetOptimizationRun, sort_by, PresetOptimizationRun.created_at)
            if sort_order == "asc":
                query = query.order_by(asc(sort_col))
            else:
                query = query.order_by(desc(sort_col))
            
            # Pagination
            query = query.offset(offset).limit(limit)
            
            runs = query.all()
            
            return [
                OptimizationRunSummary(
                    run_id=run.run_id,
                    name=run.name,
                    mode=run.mode,
                    status=run.status,
                    timeframe=run.timeframe,
                    preset_count=run.effective_preset_count,
                    pair_count=run.effective_pair_count,
                    total_combinations=run.total_combinations,
                    duration_seconds=run.duration_seconds,
                    best_preset_name=run.best_preset_name,
                    best_overall_score=run.best_overall_score,
                    best_avg_pnl=run.best_avg_pnl,
                    created_at=run.created_at.isoformat(),
                    completed_at=run.completed_at.isoformat() if run.completed_at else None
                )
                for run in runs
            ]
        finally:
            session.close()
    
    @classmethod
    def get_preset_scores(
        cls,
        run_id: str,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "overall_score",
        sort_order: str = "desc",
        min_score: Optional[float] = None,
        indicator_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict:
        """
        Get preset scores from a run with filtering and sorting.
        
        Args:
            run_id: Run identifier
            limit: Max results
            offset: Skip first N
            sort_by: Sort field
            sort_order: 'asc' or 'desc'
            min_score: Minimum overall score
            indicator_type: Filter by indicator
            search: Search in preset name
            
        Returns:
            Dict with scores and pagination info
        """
        session = cls._get_session()
        try:
            run = session.query(PresetOptimizationRun).filter_by(run_id=run_id).first()
            
            if not run or not run.preset_scores:
                return {"scores": [], "total": 0, "filtered": 0}
            
            scores = run.preset_scores.copy()
            total = len(scores)
            
            # Apply filters
            if min_score is not None:
                scores = [s for s in scores if s.get('overall_score', 0) >= min_score]
            
            if indicator_type:
                scores = [s for s in scores if s.get('indicator_type', '').lower() == indicator_type.lower()]
            
            if search:
                search_lower = search.lower()
                scores = [s for s in scores if search_lower in s.get('preset_name', '').lower() or
                         search_lower in s.get('preset_id', '').lower()]
            
            filtered = len(scores)
            
            # Sort
            reverse = sort_order == "desc"
            scores.sort(key=lambda x: x.get(sort_by, 0) or 0, reverse=reverse)
            
            # Paginate
            scores = scores[offset:offset + limit]
            
            return {
                "scores": scores,
                "total": total,
                "filtered": filtered,
                "offset": offset,
                "limit": limit
            }
        finally:
            session.close()
    
    @classmethod
    def get_result_matrix(cls, run_id: str) -> Optional[Dict]:
        """Get result matrix for a run"""
        session = cls._get_session()
        try:
            run = session.query(PresetOptimizationRun).filter_by(run_id=run_id).first()
            if not run:
                return None
            return run.result_matrix or {}
        finally:
            session.close()
    
    @classmethod
    def count_runs(cls, mode: Optional[str] = None, status: Optional[str] = None) -> int:
        """Count total runs with optional filtering"""
        session = cls._get_session()
        try:
            query = session.query(PresetOptimizationRun)
            if mode:
                query = query.filter(PresetOptimizationRun.mode == mode)
            if status:
                query = query.filter(PresetOptimizationRun.status == status)
            return query.count()
        finally:
            session.close()
    
    # ========== UPDATE ==========
    
    @classmethod
    def update_run_status(cls, run_id: str, status: str, **kwargs) -> bool:
        """Update run status and optional fields"""
        session = cls._get_session()
        try:
            run = session.query(PresetOptimizationRun).filter_by(run_id=run_id).first()
            if not run:
                return False
            
            run.status = status
            for key, value in kwargs.items():
                if hasattr(run, key):
                    setattr(run, key, value)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update run status: {e}")
            return False
        finally:
            session.close()
    
    @classmethod
    def rename_run(cls, run_id: str, name: str) -> bool:
        """Rename a run"""
        return cls.update_run_status(run_id, status=None, name=name)
    
    # ========== DELETE ==========
    
    @classmethod
    def delete_run(cls, run_id: str) -> bool:
        """Delete a specific run"""
        session = cls._get_session()
        try:
            result = session.query(PresetOptimizationRun).filter_by(run_id=run_id).delete()
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete run: {e}")
            return False
        finally:
            session.close()
    
    @classmethod
    def delete_old_runs(cls, keep_count: int = 50) -> int:
        """Delete old runs keeping only the most recent N"""
        session = cls._get_session()
        try:
            # Get IDs of runs to keep
            keep_query = session.query(PresetOptimizationRun.id).order_by(
                desc(PresetOptimizationRun.created_at)
            ).limit(keep_count)
            
            keep_ids = [r.id for r in keep_query.all()]
            
            # Delete others
            result = session.query(PresetOptimizationRun).filter(
                ~PresetOptimizationRun.id.in_(keep_ids)
            ).delete(synchronize_session=False)
            
            session.commit()
            logger.info(f"Deleted {result} old optimization runs")
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete old runs: {e}")
            return 0
        finally:
            session.close()
    
    @classmethod
    def clear_all(cls) -> int:
        """Delete all optimization runs"""
        session = cls._get_session()
        try:
            result = session.query(PresetOptimizationRun).delete()
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to clear all runs: {e}")
            return 0
        finally:
            session.close()
    
    # ========== AGGREGATION ==========
    
    @classmethod
    def get_aggregated_by_preset(
        cls,
        preset_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get aggregated results for a specific preset across multiple runs.
        
        Args:
            preset_id: Preset ID to aggregate
            limit: Max runs to include
            
        Returns:
            List of run results for this preset
        """
        session = cls._get_session()
        try:
            runs = session.query(PresetOptimizationRun).filter(
                PresetOptimizationRun.status == 'completed'
            ).order_by(desc(PresetOptimizationRun.created_at)).limit(limit).all()
            
            results = []
            for run in runs:
                if run.preset_scores:
                    for score in run.preset_scores:
                        if score.get('preset_id') == preset_id:
                            results.append({
                                "run_id": run.run_id,
                                "mode": run.mode,
                                "timeframe": run.timeframe,
                                "created_at": run.created_at.isoformat(),
                                "score": score
                            })
                            break
            
            return results
        finally:
            session.close()
    
    @classmethod
    def get_aggregated_by_pair(
        cls,
        pair: str,
        run_id: str
    ) -> List[Dict]:
        """
        Get all preset results for a specific pair in a run.
        
        Args:
            pair: Trading pair
            run_id: Run identifier
            
        Returns:
            List of preset results for this pair
        """
        session = cls._get_session()
        try:
            run = session.query(PresetOptimizationRun).filter_by(run_id=run_id).first()
            
            if not run or not run.result_matrix:
                return []
            
            results = []
            for preset_id, pair_results in run.result_matrix.items():
                if pair in pair_results:
                    results.append({
                        "preset_id": preset_id,
                        "metrics": pair_results[pair]
                    })
            
            # Sort by PnL
            results.sort(key=lambda x: x['metrics'].get('profit_pct', 0), reverse=True)
            
            return results
        finally:
            session.close()
    
    # ========== EXPORT ==========
    
    @classmethod
    def export_to_csv(cls, run_id: str) -> Optional[str]:
        """
        Export preset scores to CSV format.
        
        Args:
            run_id: Run identifier
            
        Returns:
            CSV string or None
        """
        session = cls._get_session()
        try:
            run = session.query(PresetOptimizationRun).filter_by(run_id=run_id).first()
            
            if not run or not run.preset_scores:
                return None
            
            # CSV header
            headers = [
                "Rank", "Preset ID", "Preset Name", "Indicator", "Overall Score",
                "Avg PnL %", "Avg Win Rate %", "Avg Sharpe", "Avg Max DD %",
                "Positive Pairs", "Total Pairs", "Positive Ratio %",
                "Best Pair", "Best PnL %", "Worst Pair", "Worst PnL %",
                "Profitability Score", "Stability Score", "Universality Score"
            ]
            
            lines = [",".join(headers)]
            
            for score in run.preset_scores:
                row = [
                    str(score.get('rank', 0)),
                    score.get('preset_id', ''),
                    score.get('preset_name', '').replace(',', ';'),
                    score.get('indicator_type', ''),
                    f"{score.get('overall_score', 0):.2f}",
                    f"{score.get('avg_pnl', 0):.2f}",
                    f"{score.get('avg_win_rate', 0) * 100:.2f}",
                    f"{score.get('avg_sharpe', 0):.2f}",
                    f"{score.get('avg_max_dd', 0):.2f}",
                    str(score.get('positive_pairs', 0)),
                    str(score.get('total_pairs', 0)),
                    f"{score.get('positive_ratio', 0) * 100:.2f}",
                    score.get('best_pair', ''),
                    f"{score.get('best_pnl', 0):.2f}",
                    score.get('worst_pair', ''),
                    f"{score.get('worst_pnl', 0):.2f}",
                    f"{score.get('profitability_score', 0):.2f}",
                    f"{score.get('stability_score', 0):.2f}",
                    f"{score.get('universality_score', 0):.2f}"
                ]
                lines.append(",".join(row))
            
            return "\n".join(lines)
        finally:
            session.close()
    
    @classmethod
    def export_to_json(cls, run_id: str) -> Optional[Dict]:
        """
        Export full run data as JSON.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Full run data dict or None
        """
        detail = cls.get_run(run_id)
        if not detail:
            return None
        return asdict(detail)


# ============================================================================
# GRADE CALCULATION
# ============================================================================

def calculate_grade(score: float) -> str:
    """Calculate letter grade from score (0-100)"""
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def get_grade_color(grade: str) -> str:
    """Get color class for grade"""
    colors = {
        "A": "text-green-400",
        "B": "text-blue-400",
        "C": "text-yellow-400",
        "D": "text-orange-400",
        "F": "text-red-400"
    }
    return colors.get(grade, "text-gray-400")


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_optimizer_db():
    """Initialize optimizer database tables"""
    OptimizationResultsManager._get_engine()
    logger.info("✓ Optimizer database initialized")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "PresetOptimizationRun",
    "OptimizationResultsManager",
    "OptimizationRunSummary",
    "OptimizationRunDetail",
    "calculate_grade",
    "get_grade_color",
    "init_optimizer_db"
]
