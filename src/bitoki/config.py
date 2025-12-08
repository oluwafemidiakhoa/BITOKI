"""Configuration management for the trading strategy."""

import os
from pathlib import Path
from typing import Any, Dict, List
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager for trading strategy."""

    def __init__(self, config_path: str = "config/strategy_config.yaml"):
        """Initialize configuration from YAML file."""
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _validate_config(self) -> None:
        """Validate required configuration fields."""
        required_fields = [
            'symbol', 'timeframes', 'allowed_patterns', 'risk_pct',
            'take_profit_pips', 'poll_interval_seconds'
        ]
        for field in required_fields:
            if field not in self._config:
                raise ValueError(f"Missing required config field: {field}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    @property
    def symbol(self) -> str:
        return self._config['symbol']

    @property
    def timeframes(self) -> List[str]:
        return self._config['timeframes']

    @property
    def allowed_patterns(self) -> List[str]:
        return self._config['allowed_patterns']

    @property
    def risk_pct(self) -> float:
        return self._config['risk_pct']

    @property
    def take_profit_pips(self) -> float:
        return self._config['take_profit_pips']

    @property
    def pips_unit_in_usd(self) -> float:
        return self._config.get('pips_unit_in_usd', 1.0)

    @property
    def stoploss_padding_points(self) -> float:
        return self._config.get('stoploss_padding_points', 10)

    @property
    def atr_period(self) -> int:
        return self._config.get('atr_period', 14)

    @property
    def atr_multiplier(self) -> float:
        return self._config.get('atr_multiplier', 2.0)

    @property
    def news_block_minutes(self) -> int:
        return self._config.get('news_block_minutes', 30)

    @property
    def poll_interval_seconds(self) -> int:
        return self._config['poll_interval_seconds']

    @property
    def max_concurrent_trades(self) -> int:
        return self._config.get('max_concurrent_trades', 3)

    @property
    def trade_mode(self) -> str:
        mode = os.getenv('TRADE_MODE', self._config.get('trade_mode', 'dry_run'))
        return mode.lower()

    @property
    def order_type(self) -> str:
        return self._config.get('order_type', 'market')

    @property
    def daily_loss_limit_pct(self) -> float:
        return self.get('safety.daily_loss_limit_pct', 0.10)

    @property
    def max_trades_per_day(self) -> int:
        return self.get('safety.max_trades_per_day', 10)

    @property
    def exchange_name(self) -> str:
        return self.get('exchange.name', 'binance')

    @property
    def api_key(self) -> str:
        env_var = self.get('exchange.api_key_env', 'EXCHANGE_API_KEY')
        return os.getenv(env_var, '')

    @property
    def api_secret(self) -> str:
        env_var = self.get('exchange.api_secret_env', 'EXCHANGE_API_SECRET')
        return os.getenv(env_var, '')

    @property
    def is_sandbox(self) -> bool:
        return self.get('exchange.sandbox', True)
