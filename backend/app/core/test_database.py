"""
Komas Database Test Script
==========================
Run: python -m app.core.test_database
"""
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import (
    init_db, close_db, create_default_settings,
    DatabaseManager, SettingsManager, PresetManager, BotManager,
    SignalManager, DataCacheManager, DB_PATH
)


async def test_database():
    print("=" * 60)
    print("KOMAS DATABASE TEST")
    print("=" * 60)
    
    # Initialize
    print(f"\n1. Initializing database at: {DB_PATH}")
    init_db(echo=False)
    print("   ✓ Database initialized")
    
    # Create default settings
    print("\n2. Creating default settings...")
    await create_default_settings()
    print("   ✓ Default settings created")
    
    # Test Settings
    print("\n3. Testing Settings...")
    await SettingsManager.set("test.string", "Hello World", "Test string setting")
    await SettingsManager.set("test.int", 42, "Test integer setting")
    await SettingsManager.set("test.float", 3.14, "Test float setting")
    await SettingsManager.set("test.bool", True, "Test boolean setting")
    await SettingsManager.set("test.json", {"foo": "bar", "nums": [1, 2, 3]}, "Test JSON setting")
    
    # Read back
    assert await SettingsManager.get("test.string") == "Hello World"
    assert await SettingsManager.get("test.int") == 42
    assert await SettingsManager.get("test.float") == 3.14
    assert await SettingsManager.get("test.bool") == True
    assert await SettingsManager.get("test.json") == {"foo": "bar", "nums": [1, 2, 3]}
    assert await SettingsManager.get("nonexistent", "default") == "default"
    
    all_settings = await SettingsManager.get_all()
    print(f"   ✓ Settings work ({len(all_settings)} total)")
    
    # Test Presets
    print("\n4. Testing Presets...")
    preset = await PresetManager.create(
        name="Test Preset",
        description="A test preset",
        settings={
            "trg_atr_length": 45,
            "trg_multiplier": 4.0,
            "tp_count": 4,
        },
        tags=["test", "example"]
    )
    print(f"   Created preset ID: {preset.id}")
    
    # Read back
    loaded = await PresetManager.get(preset.id)
    assert loaded is not None
    assert loaded.name == "Test Preset"
    assert loaded.settings["trg_atr_length"] == 45
    
    # Update
    await PresetManager.update(preset.id, is_favorite=True, win_rate=75.5)
    
    # List
    presets = await PresetManager.list_all()
    assert len(presets) >= 1
    print(f"   ✓ Presets work ({len(presets)} total)")
    
    # Test Bots
    print("\n5. Testing Bots...")
    bot = await BotManager.create(
        name="Test Bot",
        symbol="BTCUSDT",
        timeframe="1h",
        preset_id=preset.id,
        telegram_enabled=True
    )
    print(f"   Created bot ID: {bot.id}")
    
    # Activate
    await BotManager.activate(bot.id)
    
    # List active
    active_bots = await BotManager.list_all(active_only=True)
    assert len(active_bots) >= 1
    print(f"   ✓ Bots work ({len(active_bots)} active)")
    
    # Test Signals
    print("\n6. Testing Signals...")
    signal = await SignalManager.create(
        bot_id=bot.id,
        symbol="BTCUSDT",
        timeframe="1h",
        direction="long",
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profits=[
            {"percent": 1.05, "amount": 50, "price": 50525.0},
            {"percent": 1.95, "amount": 30, "price": 50975.0},
        ]
    )
    print(f"   Created signal ID: {signal.id}")
    
    # Close signal
    await SignalManager.close(
        signal.id,
        exit_price=50525.0,
        exit_reason="tp1",
        pnl_percent=1.05,
        pnl_amount=52.5
    )
    
    # Update bot stats
    await BotManager.increment_stats(bot.id, is_win=True, pnl=52.5)
    
    recent = await SignalManager.list_recent(limit=10)
    print(f"   ✓ Signals work ({len(recent)} recent)")
    
    # Test DataCache
    print("\n7. Testing DataCache...")
    cache = await DataCacheManager.upsert(
        symbol="BTCUSDT",
        timeframe="1h",
        source="binance",
        candles_count=8760,
        is_complete=True
    )
    print(f"   Created cache ID: {cache.id}")
    
    caches = await DataCacheManager.list_all()
    print(f"   ✓ DataCache works ({len(caches)} entries)")
    
    # Cleanup test data
    print("\n8. Cleanup...")
    await SettingsManager.delete("test.string")
    await SettingsManager.delete("test.int")
    await SettingsManager.delete("test.float")
    await SettingsManager.delete("test.bool")
    await SettingsManager.delete("test.json")
    print("   ✓ Test settings deleted")
    
    # Close
    await close_db()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_database())
