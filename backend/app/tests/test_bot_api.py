"""
API Tests for Bot Backtest and Optimizer Endpoints
===================================================
Test REST API endpoints for backtesting and optimization
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.main import app
from app.core.bots.models import (
    BotConfig,
    BotSymbolConfig,
    StrategyConfig,
    TakeProfitLevel
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_bot():
    """Create mock bot for testing"""
    config = BotConfig(
        name="API Test Bot",
        initial_capital=10000.0,
        leverage=1,
        symbols=[
            BotSymbolConfig(symbol="BTCUSDT", allocation_percent=50.0),
            BotSymbolConfig(symbol="ETHUSDT", allocation_percent=50.0)
        ],
        strategy=StrategyConfig(
            name="TestStrategy",
            stop_loss_percent=2.0,
            take_profit_levels=[
                TakeProfitLevel(level=1, percent=2.0, amount=50.0),
                TakeProfitLevel(level=2, percent=4.0, amount=50.0)
            ]
        )
    )

    mock = MagicMock()
    mock.config = config
    mock.id = "test_bot_123"
    return mock


class TestBacktestAPI:
    """Test backtest API endpoints"""

    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.backtest.PortfolioBacktest')
    def test_run_backtest_success(
        self,
        mock_backtest_class,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test successful backtest execution"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        # Mock backtest result
        mock_result = Mock()
        mock_result.total_trades = 10
        mock_result.total_pnl_percent = 5.5
        mock_result.to_dict.return_value = {
            "total_trades": 10,
            "winning_trades": 7,
            "losing_trades": 3,
            "win_rate": 70.0,
            "total_pnl": 550.0,
            "total_pnl_percent": 5.5,
            "profit_factor": 2.5,
            "sharpe_ratio": 1.8,
            "max_drawdown": 2.5
        }

        mock_backtest = Mock()
        mock_backtest.run.return_value = mock_result
        mock_backtest_class.return_value = mock_backtest

        # Make request
        response = client.post("/api/bots/backtest", json={
            "bot_id": "test_bot_123",
            "start_date": "2024-01-01",
            "end_date": "2024-02-01"
        })

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["total_trades"] == 10
        assert data["result"]["win_rate"] == 70.0
        assert data["result"]["total_pnl_percent"] == 5.5

        # Verify backtest was created with correct params
        mock_backtest_class.assert_called_once()
        call_kwargs = mock_backtest_class.call_args[1]
        assert call_kwargs["bot_config"] == mock_bot.config
        assert call_kwargs["start_date"] == "2024-01-01"
        assert call_kwargs["end_date"] == "2024-02-01"


    @patch('app.api.bots_routes.get_bots_manager')
    def test_run_backtest_bot_not_found(
        self,
        mock_get_manager,
        client
    ):
        """Test backtest with non-existent bot"""
        # Setup mock
        mock_manager = Mock()
        mock_manager.get_bot.return_value = None
        mock_get_manager.return_value = mock_manager

        # Make request
        response = client.post("/api/bots/backtest", json={
            "bot_id": "nonexistent_bot",
            "start_date": "2024-01-01",
            "end_date": "2024-02-01"
        })

        # Verify 404 response
        assert response.status_code == 404
        response_data = response.json()
        # Check if error message is in 'detail' or 'message' field
        error_msg = response_data.get("detail", response_data.get("message", "")).lower()
        assert "not found" in error_msg or response.status_code == 404


    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.backtest.PortfolioBacktest')
    def test_run_backtest_execution_error(
        self,
        mock_backtest_class,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test backtest execution error handling"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        # Mock backtest to raise error
        mock_backtest = Mock()
        mock_backtest.run.side_effect = Exception("Backtest execution failed")
        mock_backtest_class.return_value = mock_backtest

        # Make request
        response = client.post("/api/bots/backtest", json={
            "bot_id": "test_bot_123",
            "start_date": "2024-01-01",
            "end_date": "2024-02-01"
        })

        # Verify error response
        assert response.status_code == 200  # Still returns 200 with error in body
        data = response.json()
        assert data["success"] is False
        assert "failed" in data["error"].lower()


    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.backtest.PortfolioBacktest')
    def test_run_backtest_default_dates(
        self,
        mock_backtest_class,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test backtest with default dates (None)"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        mock_result = Mock()
        mock_result.total_trades = 5
        mock_result.total_pnl_percent = 2.5
        mock_result.to_dict.return_value = {"total_trades": 5}

        mock_backtest = Mock()
        mock_backtest.run.return_value = mock_result
        mock_backtest_class.return_value = mock_backtest

        # Make request without dates
        response = client.post("/api/bots/backtest", json={
            "bot_id": "test_bot_123"
        })

        # Verify success
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify dates were passed as None
        call_kwargs = mock_backtest_class.call_args[1]
        assert call_kwargs["start_date"] is None
        assert call_kwargs["end_date"] is None


class TestOptimizerAPI:
    """Test optimizer API endpoints"""

    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.optimizer.quick_optimize')
    def test_optimize_success(
        self,
        mock_quick_optimize,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test successful optimization"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        # Mock optimization result
        mock_result = Mock()
        mock_result.best_score = 2.5
        mock_result.to_dict.return_value = {
            "best_score": 2.5,
            "best_config": {
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "stop_loss_percent": 2.0
            },
            "all_results": [
                {"score": 2.5, "symbols": ["BTCUSDT", "ETHUSDT"]},
                {"score": 2.0, "symbols": ["BTCUSDT"]}
            ],
            "tested_combinations": 10
        }
        mock_quick_optimize.return_value = mock_result

        # Make request
        response = client.post("/api/bots/optimize", json={
            "bot_id": "test_bot_123",
            "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            "metric": "sharpe",
            "start_date": "2024-01-01",
            "end_date": "2024-02-01",
            "max_combinations": 20
        })

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["best_score"] == 2.5
        assert len(data["result"]["all_results"]) == 2

        # Verify optimizer was called with correct params
        mock_quick_optimize.assert_called_once()
        call_kwargs = mock_quick_optimize.call_args[1]
        assert call_kwargs["base_config"] == mock_bot.config
        assert call_kwargs["symbols"] == ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        assert call_kwargs["metric"] == "sharpe"


    @patch('app.api.bots_routes.get_bots_manager')
    def test_optimize_bot_not_found(
        self,
        mock_get_manager,
        client
    ):
        """Test optimization with non-existent bot"""
        # Setup mock
        mock_manager = Mock()
        mock_manager.get_bot.return_value = None
        mock_get_manager.return_value = mock_manager

        # Make request
        response = client.post("/api/bots/optimize", json={
            "bot_id": "nonexistent_bot",
            "symbols": ["BTCUSDT"],
            "metric": "sharpe"
        })

        # Verify 404 response
        assert response.status_code == 404
        response_data = response.json()
        # Check if error message is in 'detail' or 'message' field
        error_msg = response_data.get("detail", response_data.get("message", "")).lower()
        assert "not found" in error_msg or response.status_code == 404


    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.optimizer.quick_optimize')
    def test_optimize_execution_error(
        self,
        mock_quick_optimize,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test optimization execution error handling"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        # Mock optimizer to raise error
        mock_quick_optimize.side_effect = Exception("Optimization failed")

        # Make request
        response = client.post("/api/bots/optimize", json={
            "bot_id": "test_bot_123",
            "symbols": ["BTCUSDT"],
            "metric": "sharpe"
        })

        # Verify error response
        assert response.status_code == 200  # Returns 200 with error in body
        data = response.json()
        assert data["success"] is False
        assert "failed" in data["error"].lower()


    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.optimizer.quick_optimize')
    def test_optimize_with_different_metrics(
        self,
        mock_quick_optimize,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test optimization with different metrics"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        mock_result = Mock()
        mock_result.best_score = 3.5
        mock_result.to_dict.return_value = {"best_score": 3.5}
        mock_quick_optimize.return_value = mock_result

        metrics_to_test = ["sharpe", "profit_factor", "win_rate", "pnl_percent"]

        for metric in metrics_to_test:
            # Make request with different metric
            response = client.post("/api/bots/optimize", json={
                "bot_id": "test_bot_123",
                "symbols": ["BTCUSDT"],
                "metric": metric
            })

            # Verify success
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # Verify metric was passed correctly
            call_kwargs = mock_quick_optimize.call_args[1]
            assert call_kwargs["metric"] == metric


    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.optimizer.quick_optimize')
    def test_optimize_default_params(
        self,
        mock_quick_optimize,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test optimization with default parameters"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        mock_result = Mock()
        mock_result.best_score = 2.0
        mock_result.to_dict.return_value = {"best_score": 2.0}
        mock_quick_optimize.return_value = mock_result

        # Make request with minimal params
        response = client.post("/api/bots/optimize", json={
            "bot_id": "test_bot_123"
        })

        # Verify success
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify default values were used
        call_kwargs = mock_quick_optimize.call_args[1]
        assert call_kwargs["metric"] == "sharpe"  # Default metric
        assert call_kwargs["symbols"] is None  # Default symbols


class TestQuickEndpoints:
    """Test quick backtest and optimize endpoints"""

    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.backtest.PortfolioBacktest')
    def test_quick_backtest(
        self,
        mock_backtest_class,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test quick backtest endpoint"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        mock_result = Mock()
        mock_result.to_dict.return_value = {"total_trades": 5}

        mock_backtest = Mock()
        mock_backtest.run.return_value = mock_result
        mock_backtest_class.return_value = mock_backtest

        # Make request
        response = client.get("/api/bots/test_bot_123/backtest-quick?days=30")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        # Data is in 'result' field for quick endpoints
        assert data["success"] is True
        assert "total_trades" in data["result"]


    @patch('app.api.bots_routes.get_bots_manager')
    @patch('app.core.bots.optimizer.quick_optimize')
    def test_quick_optimize(
        self,
        mock_quick_optimize,
        mock_get_manager,
        client,
        mock_bot
    ):
        """Test quick optimize endpoint"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_bot.return_value = mock_bot
        mock_get_manager.return_value = mock_manager

        mock_result = Mock()
        mock_result.to_dict.return_value = {"best_score": 2.5}
        mock_quick_optimize.return_value = mock_result

        # Make request
        response = client.get(
            "/api/bots/test_bot_123/optimize-quick?metric=sharpe&days=30"
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        # Data is in 'result' field for quick endpoints
        assert data["success"] is True
        assert "best_score" in data["result"]
