"""
Tests for Telegram Multi-Channel Support
=========================================
Tests for channel manager, signal router, and related functionality
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from app.core.notifications.models import (
    TelegramChannel,
    TelegramChannelCreate,
    TelegramChannelUpdate,
    ChannelRoutingRules,
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    NotificationFormat
)
from app.core.notifications.channel_manager import ChannelManager
from app.core.notifications.signal_router import SignalRouter


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def channel_manager(temp_data_dir):
    """Create channel manager with temp directory"""
    return ChannelManager(data_dir=temp_data_dir)


@pytest.fixture
def sample_channel_data():
    """Sample channel creation data"""
    return TelegramChannelCreate(
        name="Test Channel",
        chat_id="@testchannel",
        enabled=True,
        message_format=NotificationFormat.SIMPLE
    )


@pytest.fixture
def sample_signal():
    """Sample signal data"""
    return SignalData(
        symbol="BTCUSDT",
        direction="LONG",
        entry_price=50000.0,
        tp_targets=[51000.0, 52000.0],
        tp_amounts=[50.0, 50.0],
        sl_price=49000.0,
        leverage=10,
        timeframe="1h",
        indicator_name="TRG",
        score=85,
        grade="A"
    )


# ============ CHANNEL MANAGER TESTS ============


class TestChannelManager:
    """Test ChannelManager functionality"""

    def test_create_channel(self, channel_manager, sample_channel_data):
        """Test creating a new channel"""
        channel = channel_manager.create_channel(sample_channel_data)

        assert channel.id is not None
        assert channel.name == "Test Channel"
        assert channel.chat_id == "@testchannel"
        assert channel.enabled is True
        assert len(channel_manager.get_all_channels()) == 1

    def test_create_duplicate_name(self, channel_manager, sample_channel_data):
        """Test creating channel with duplicate name fails"""
        channel_manager.create_channel(sample_channel_data)

        with pytest.raises(ValueError, match="already exists"):
            channel_manager.create_channel(sample_channel_data)

    def test_create_duplicate_chat_id(self, channel_manager):
        """Test creating channel with duplicate chat_id fails"""
        data1 = TelegramChannelCreate(
            name="Channel 1",
            chat_id="@samechat",
            enabled=True
        )
        data2 = TelegramChannelCreate(
            name="Channel 2",
            chat_id="@samechat",
            enabled=True
        )

        channel_manager.create_channel(data1)

        with pytest.raises(ValueError, match="already exists"):
            channel_manager.create_channel(data2)

    def test_get_channel(self, channel_manager, sample_channel_data):
        """Test getting channel by ID"""
        created = channel_manager.create_channel(sample_channel_data)
        retrieved = channel_manager.get_channel(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_nonexistent_channel(self, channel_manager):
        """Test getting non-existent channel returns None"""
        result = channel_manager.get_channel("nonexistent-id")
        assert result is None

    def test_get_all_channels(self, channel_manager):
        """Test getting all channels"""
        # Create multiple channels
        for i in range(3):
            data = TelegramChannelCreate(
                name=f"Channel {i}",
                chat_id=f"@channel{i}",
                enabled=True
            )
            channel_manager.create_channel(data)

        channels = channel_manager.get_all_channels()
        assert len(channels) == 3

    def test_get_enabled_channels(self, channel_manager):
        """Test getting only enabled channels"""
        # Create enabled channel
        data1 = TelegramChannelCreate(
            name="Enabled",
            chat_id="@enabled",
            enabled=True
        )
        # Create disabled channel
        data2 = TelegramChannelCreate(
            name="Disabled",
            chat_id="@disabled",
            enabled=False
        )

        channel_manager.create_channel(data1)
        channel_manager.create_channel(data2)

        enabled = channel_manager.get_enabled_channels()
        assert len(enabled) == 1
        assert enabled[0].name == "Enabled"

    def test_update_channel(self, channel_manager, sample_channel_data):
        """Test updating channel"""
        channel = channel_manager.create_channel(sample_channel_data)

        update_data = TelegramChannelUpdate(
            name="Updated Channel",
            enabled=False
        )
        updated = channel_manager.update_channel(channel.id, update_data)

        assert updated.name == "Updated Channel"
        assert updated.enabled is False
        assert updated.chat_id == "@testchannel"  # Unchanged

    def test_update_nonexistent_channel(self, channel_manager):
        """Test updating non-existent channel raises error"""
        update_data = TelegramChannelUpdate(name="New Name")

        with pytest.raises(ValueError, match="not found"):
            channel_manager.update_channel("nonexistent-id", update_data)

    def test_delete_channel(self, channel_manager, sample_channel_data):
        """Test deleting channel"""
        channel = channel_manager.create_channel(sample_channel_data)
        assert len(channel_manager.get_all_channels()) == 1

        success = channel_manager.delete_channel(channel.id)
        assert success is True
        assert len(channel_manager.get_all_channels()) == 0

    def test_delete_nonexistent_channel(self, channel_manager):
        """Test deleting non-existent channel"""
        success = channel_manager.delete_channel("nonexistent-id")
        assert success is False

    def test_increment_message_count(self, channel_manager, sample_channel_data):
        """Test incrementing message count"""
        channel = channel_manager.create_channel(sample_channel_data)
        initial_count = channel.messages_sent

        channel_manager.increment_message_count(channel.id)
        updated = channel_manager.get_channel(channel.id)

        assert updated.messages_sent == initial_count + 1
        assert updated.last_sent is not None

    def test_get_stats(self, channel_manager):
        """Test getting channel statistics"""
        # Create channels
        data1 = TelegramChannelCreate(name="Ch1", chat_id="@ch1", enabled=True)
        data2 = TelegramChannelCreate(name="Ch2", chat_id="@ch2", enabled=False)

        ch1 = channel_manager.create_channel(data1)
        ch2 = channel_manager.create_channel(data2)

        # Increment messages
        channel_manager.increment_message_count(ch1.id)
        channel_manager.increment_message_count(ch1.id)

        stats = channel_manager.get_stats()

        assert stats["total_channels"] == 2
        assert stats["enabled_channels"] == 1
        assert stats["disabled_channels"] == 1
        assert stats["total_messages_sent"] == 2

    def test_persistence(self, temp_data_dir):
        """Test that channels persist across manager instances"""
        # Create manager and add channel
        manager1 = ChannelManager(data_dir=temp_data_dir)
        data = TelegramChannelCreate(
            name="Persistent Channel",
            chat_id="@persist",
            enabled=True
        )
        channel = manager1.create_channel(data)

        # Create new manager instance
        manager2 = ChannelManager(data_dir=temp_data_dir)

        # Should load existing channel
        channels = manager2.get_all_channels()
        assert len(channels) == 1
        assert channels[0].name == "Persistent Channel"
        assert channels[0].id == channel.id


# ============ SIGNAL ROUTER TESTS ============


class TestSignalRouter:
    """Test SignalRouter functionality"""

    def test_route_signal_no_channels(self, sample_signal):
        """Test routing with no channels"""
        router = SignalRouter([])
        result = router.route_signal(sample_signal)
        assert result == []

    def test_route_signal_all_match(self, sample_signal):
        """Test routing when all channels match"""
        # Create channels with no filters (match all)
        channels = [
            TelegramChannel(
                id="ch1",
                name="Channel 1",
                chat_id="@ch1",
                enabled=True,
                routing_rules=ChannelRoutingRules()
            ),
            TelegramChannel(
                id="ch2",
                name="Channel 2",
                chat_id="@ch2",
                enabled=True,
                routing_rules=ChannelRoutingRules()
            )
        ]

        router = SignalRouter(channels)
        result = router.route_signal(sample_signal)

        assert len(result) == 2

    def test_route_signal_disabled_channel(self, sample_signal):
        """Test that disabled channels are excluded"""
        channels = [
            TelegramChannel(
                id="ch1",
                name="Enabled",
                chat_id="@enabled",
                enabled=True,
                routing_rules=ChannelRoutingRules()
            ),
            TelegramChannel(
                id="ch2",
                name="Disabled",
                chat_id="@disabled",
                enabled=False,
                routing_rules=ChannelRoutingRules()
            )
        ]

        router = SignalRouter(channels)
        result = router.route_signal(sample_signal)

        assert len(result) == 1
        assert result[0].name == "Enabled"

    def test_route_signal_indicator_filter(self, sample_signal):
        """Test routing with indicator filter"""
        # Channel only wants TRG signals
        trg_channel = TelegramChannel(
            id="trg",
            name="TRG Only",
            chat_id="@trg",
            enabled=True,
            routing_rules=ChannelRoutingRules(indicators=["TRG"])
        )

        # Channel only wants Dominant signals
        dominant_channel = TelegramChannel(
            id="dom",
            name="Dominant Only",
            chat_id="@dominant",
            enabled=True,
            routing_rules=ChannelRoutingRules(indicators=["Dominant"])
        )

        router = SignalRouter([trg_channel, dominant_channel])
        result = router.route_signal(sample_signal)  # TRG signal

        assert len(result) == 1
        assert result[0].name == "TRG Only"

    def test_route_signal_symbol_filter(self, sample_signal):
        """Test routing with symbol filter"""
        # BTC only channel
        btc_channel = TelegramChannel(
            id="btc",
            name="BTC Only",
            chat_id="@btc",
            enabled=True,
            routing_rules=ChannelRoutingRules(symbols=["BTCUSDT"])
        )

        # ETH only channel
        eth_channel = TelegramChannel(
            id="eth",
            name="ETH Only",
            chat_id="@eth",
            enabled=True,
            routing_rules=ChannelRoutingRules(symbols=["ETHUSDT"])
        )

        router = SignalRouter([btc_channel, eth_channel])
        result = router.route_signal(sample_signal)  # BTCUSDT

        assert len(result) == 1
        assert result[0].name == "BTC Only"

    def test_route_signal_direction_filter(self, sample_signal):
        """Test routing with direction filter"""
        # Long only channel
        long_channel = TelegramChannel(
            id="long",
            name="Long Only",
            chat_id="@long",
            enabled=True,
            routing_rules=ChannelRoutingRules(directions=["LONG"])
        )

        # Short only channel
        short_channel = TelegramChannel(
            id="short",
            name="Short Only",
            chat_id="@short",
            enabled=True,
            routing_rules=ChannelRoutingRules(directions=["SHORT"])
        )

        router = SignalRouter([long_channel, short_channel])
        result = router.route_signal(sample_signal)  # LONG signal

        assert len(result) == 1
        assert result[0].name == "Long Only"

    def test_route_signal_min_score_filter(self, sample_signal):
        """Test routing with minimum score filter"""
        # High quality channel (min 80)
        premium_channel = TelegramChannel(
            id="premium",
            name="Premium",
            chat_id="@premium",
            enabled=True,
            routing_rules=ChannelRoutingRules(min_score=80)
        )

        # Any quality channel
        free_channel = TelegramChannel(
            id="free",
            name="Free",
            chat_id="@free",
            enabled=True,
            routing_rules=ChannelRoutingRules(min_score=50)
        )

        router = SignalRouter([premium_channel, free_channel])
        result = router.route_signal(sample_signal)  # Score 85

        assert len(result) == 2  # Both match

        # Test with low score signal
        low_score_signal = sample_signal.model_copy()
        low_score_signal.score = 70
        result = router.route_signal(low_score_signal)

        assert len(result) == 1
        assert result[0].name == "Free"

    def test_route_signal_grade_filter(self, sample_signal):
        """Test routing with grade filter"""
        # A-B only channel
        premium_channel = TelegramChannel(
            id="premium",
            name="Premium",
            chat_id="@premium",
            enabled=True,
            routing_rules=ChannelRoutingRules(score_grades=["A", "B"])
        )

        router = SignalRouter([premium_channel])
        result = router.route_signal(sample_signal)  # Grade A

        assert len(result) == 1

        # Test with C grade signal
        c_signal = sample_signal.model_copy()
        c_signal.grade = "C"
        result = router.route_signal(c_signal)

        assert len(result) == 0

    def test_route_signal_combined_filters(self, sample_signal):
        """Test routing with multiple filters combined"""
        # Channel wants: TRG + BTCUSDT + LONG + Grade A
        strict_channel = TelegramChannel(
            id="strict",
            name="Strict Channel",
            chat_id="@strict",
            enabled=True,
            routing_rules=ChannelRoutingRules(
                indicators=["TRG"],
                symbols=["BTCUSDT"],
                directions=["LONG"],
                score_grades=["A"]
            )
        )

        router = SignalRouter([strict_channel])
        result = router.route_signal(sample_signal)

        assert len(result) == 1  # All conditions match

        # Change one condition
        different_signal = sample_signal.model_copy()
        different_signal.direction = "SHORT"
        result = router.route_signal(different_signal)

        assert len(result) == 0  # Doesn't match direction

    def test_route_tp_hit(self):
        """Test routing TP hit notifications"""
        tp_data = TPHitData(
            signal_id=1,
            symbol="BTCUSDT",
            direction="LONG",
            tp_level=1,
            tp_price=51000.0,
            entry_price=50000.0,
            profit_percent=2.0,
            amount_closed=50.0,
            remaining_position=50.0
        )

        # Channel with TP notifications enabled
        tp_channel = TelegramChannel(
            id="tp",
            name="TP Channel",
            chat_id="@tp",
            enabled=True,
            routing_rules=ChannelRoutingRules(notify_tp_hit=True)
        )

        # Channel with TP notifications disabled
        no_tp_channel = TelegramChannel(
            id="notp",
            name="No TP Channel",
            chat_id="@notp",
            enabled=True,
            routing_rules=ChannelRoutingRules(notify_tp_hit=False)
        )

        router = SignalRouter([tp_channel, no_tp_channel])
        result = router.route_tp_hit(tp_data)

        assert len(result) == 1
        assert result[0].name == "TP Channel"

    def test_route_sl_hit(self):
        """Test routing SL hit notifications"""
        sl_data = SLHitData(
            signal_id=1,
            symbol="BTCUSDT",
            direction="LONG",
            sl_price=49000.0,
            entry_price=50000.0,
            loss_percent=-2.0,
            sl_mode="fixed"
        )

        channel = TelegramChannel(
            id="sl",
            name="SL Channel",
            chat_id="@sl",
            enabled=True,
            routing_rules=ChannelRoutingRules(notify_sl_hit=True)
        )

        router = SignalRouter([channel])
        result = router.route_sl_hit(sl_data)

        assert len(result) == 1

    def test_route_signal_closed(self):
        """Test routing signal closed notifications"""
        closed_data = SignalClosedData(
            signal_id=1,
            symbol="BTCUSDT",
            direction="LONG",
            entry_price=50000.0,
            exit_price=51000.0,
            pnl_percent=2.0,
            close_reason="tp_all",
            tp_hits=[1, 2]
        )

        channel = TelegramChannel(
            id="closed",
            name="Closed Channel",
            chat_id="@closed",
            enabled=True,
            routing_rules=ChannelRoutingRules(notify_signal_closed=True)
        )

        router = SignalRouter([channel])
        result = router.route_signal_closed(closed_data)

        assert len(result) == 1

    def test_update_channels(self, sample_signal):
        """Test updating router channels"""
        router = SignalRouter([])
        result = router.route_signal(sample_signal)
        assert len(result) == 0

        # Add channels
        channels = [
            TelegramChannel(
                id="ch1",
                name="Channel 1",
                chat_id="@ch1",
                enabled=True,
                routing_rules=ChannelRoutingRules()
            )
        ]
        router.update_channels(channels)

        result = router.route_signal(sample_signal)
        assert len(result) == 1

    def test_get_channel_by_id(self):
        """Test getting channel by ID"""
        channel = TelegramChannel(
            id="test-id",
            name="Test",
            chat_id="@test",
            enabled=True,
            routing_rules=ChannelRoutingRules()
        )

        router = SignalRouter([channel])
        result = router.get_channel_by_id("test-id")

        assert result is not None
        assert result.id == "test-id"

    def test_get_active_channels(self):
        """Test getting only active channels"""
        channels = [
            TelegramChannel(
                id="active",
                name="Active",
                chat_id="@active",
                enabled=True,
                routing_rules=ChannelRoutingRules()
            ),
            TelegramChannel(
                id="inactive",
                name="Inactive",
                chat_id="@inactive",
                enabled=False,
                routing_rules=ChannelRoutingRules()
            )
        ]

        router = SignalRouter(channels)
        active = router.get_active_channels()

        assert len(active) == 1
        assert active[0].id == "active"

    def test_get_channels_count(self):
        """Test getting channel counts"""
        channels = [
            TelegramChannel(
                id="ch1",
                name="Enabled 1",
                chat_id="@en1",
                enabled=True,
                routing_rules=ChannelRoutingRules()
            ),
            TelegramChannel(
                id="ch2",
                name="Enabled 2",
                chat_id="@en2",
                enabled=True,
                routing_rules=ChannelRoutingRules()
            ),
            TelegramChannel(
                id="ch3",
                name="Disabled",
                chat_id="@dis",
                enabled=False,
                routing_rules=ChannelRoutingRules()
            )
        ]

        router = SignalRouter(channels)
        counts = router.get_channels_count()

        assert counts["total"] == 3
        assert counts["enabled"] == 2
        assert counts["disabled"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
