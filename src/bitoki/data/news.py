"""News and economic calendar integration."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from loguru import logger


class NewsEvent:
    """Represents an economic news event."""

    def __init__(
        self,
        title: str,
        time: datetime,
        impact: str,
        currency: str = "USD",
        actual: Optional[str] = None,
        forecast: Optional[str] = None,
        previous: Optional[str] = None
    ):
        self.title = title
        self.time = time
        self.impact = impact.upper()  # LOW, MEDIUM, HIGH
        self.currency = currency
        self.actual = actual
        self.forecast = forecast
        self.previous = previous

    def is_high_impact(self) -> bool:
        """Check if this is a high impact event."""
        return self.impact == "HIGH"

    def minutes_until_event(self) -> float:
        """Calculate minutes until event occurs."""
        delta = self.time - datetime.now()
        return delta.total_seconds() / 60

    def __repr__(self) -> str:
        return f"<NewsEvent: {self.title} at {self.time} ({self.impact})>"


class NewsChecker:
    """Checks for high-impact economic news events."""

    FOREXFACTORY_URL = "https://www.forexfactory.com/calendar"

    def __init__(self, target_currency: str = "USD"):
        """
        Initialize news checker.

        Args:
            target_currency: Currency to monitor (e.g., 'USD')
        """
        self.target_currency = target_currency
        self.cached_events: List[NewsEvent] = []
        self.last_fetch: Optional[datetime] = None
        self.cache_duration_minutes = 15

    def get_upcoming_and_recent_news(
        self,
        lookback_minutes: int = 60,
        lookahead_hours: int = 24
    ) -> List[NewsEvent]:
        """
        Get news events within the specified time window.

        Args:
            lookback_minutes: Minutes to look back for recent events
            lookahead_hours: Hours to look ahead for upcoming events

        Returns:
            List of NewsEvent objects
        """
        # Use cache if recent
        if self._is_cache_valid():
            return self._filter_events_by_timeframe(lookback_minutes, lookahead_hours)

        # Fetch fresh data
        try:
            events = self._fetch_forexfactory_calendar()
            self.cached_events = events
            self.last_fetch = datetime.now()
            logger.info(f"Fetched {len(events)} news events from ForexFactory")
            return self._filter_events_by_timeframe(lookback_minutes, lookahead_hours)

        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            # Return cached events if available
            if self.cached_events:
                logger.warning("Using cached news events due to fetch error")
                return self._filter_events_by_timeframe(lookback_minutes, lookahead_hours)
            return []

    def has_high_impact_within(self, minutes: int) -> bool:
        """
        Check if there's a high-impact event within specified minutes.

        Args:
            minutes: Time window to check (past and future)

        Returns:
            True if high-impact event found within window
        """
        events = self.get_upcoming_and_recent_news(
            lookback_minutes=minutes,
            lookahead_hours=minutes // 60 + 1
        )

        for event in events:
            if event.is_high_impact():
                mins_until = event.minutes_until_event()
                if abs(mins_until) <= minutes:
                    logger.warning(
                        f"High-impact event detected: {event.title} "
                        f"in {mins_until:.1f} minutes"
                    )
                    return True

        return False

    def _is_cache_valid(self) -> bool:
        """Check if cached events are still valid."""
        if not self.last_fetch or not self.cached_events:
            return False
        age_minutes = (datetime.now() - self.last_fetch).total_seconds() / 60
        return age_minutes < self.cache_duration_minutes

    def _filter_events_by_timeframe(
        self,
        lookback_minutes: int,
        lookahead_hours: int
    ) -> List[NewsEvent]:
        """Filter events by time window."""
        now = datetime.now()
        start_time = now - timedelta(minutes=lookback_minutes)
        end_time = now + timedelta(hours=lookahead_hours)

        return [
            event for event in self.cached_events
            if start_time <= event.time <= end_time
        ]

    def _fetch_forexfactory_calendar(self) -> List[NewsEvent]:
        """
        Fetch economic calendar from ForexFactory.

        Note: This is a simplified implementation. In production, you might want to:
        1. Use official API if available
        2. Add more robust error handling
        3. Handle rate limiting
        4. Parse more detailed event information
        """
        events = []

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(self.FOREXFACTORY_URL, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # This is a simplified parser - ForexFactory's actual structure may vary
            # You may need to adjust selectors based on current site structure
            calendar_rows = soup.find_all('tr', class_='calendar__row')

            current_date = datetime.now().date()

            for row in calendar_rows:
                try:
                    # Extract time
                    time_cell = row.find('td', class_='calendar__time')
                    if not time_cell:
                        continue

                    time_str = time_cell.text.strip()
                    if not time_str or time_str in ['All Day', 'Tentative']:
                        continue

                    # Extract impact
                    impact_cell = row.find('td', class_='calendar__impact')
                    impact_spans = impact_cell.find_all('span', class_='impact') if impact_cell else []
                    impact_level = len(impact_spans)  # 1=low, 2=medium, 3=high

                    if impact_level == 3:
                        impact = "HIGH"
                    elif impact_level == 2:
                        impact = "MEDIUM"
                    else:
                        impact = "LOW"

                    # Extract currency
                    currency_cell = row.find('td', class_='calendar__currency')
                    currency = currency_cell.text.strip() if currency_cell else "USD"

                    # Filter by target currency
                    if currency != self.target_currency:
                        continue

                    # Extract title
                    event_cell = row.find('td', class_='calendar__event')
                    title = event_cell.text.strip() if event_cell else "Unknown Event"

                    # Parse time
                    event_time = datetime.strptime(
                        f"{current_date} {time_str}",
                        "%Y-%m-%d %I:%M%p"
                    )

                    # Extract forecast/actual/previous if available
                    actual = forecast = previous = None
                    actual_cell = row.find('td', class_='calendar__actual')
                    forecast_cell = row.find('td', class_='calendar__forecast')
                    previous_cell = row.find('td', class_='calendar__previous')

                    if actual_cell:
                        actual = actual_cell.text.strip()
                    if forecast_cell:
                        forecast = forecast_cell.text.strip()
                    if previous_cell:
                        previous = previous_cell.text.strip()

                    events.append(NewsEvent(
                        title=title,
                        time=event_time,
                        impact=impact,
                        currency=currency,
                        actual=actual,
                        forecast=forecast,
                        previous=previous
                    ))

                except Exception as e:
                    logger.debug(f"Error parsing calendar row: {e}")
                    continue

        except requests.RequestException as e:
            logger.error(f"Error fetching ForexFactory calendar: {e}")
            raise

        return events

    def get_mock_events(self) -> List[NewsEvent]:
        """
        Get mock events for testing (when live API is unavailable).

        Returns:
            List of mock NewsEvent objects
        """
        now = datetime.now()
        return [
            NewsEvent(
                title="Non-Farm Payrolls",
                time=now + timedelta(hours=2),
                impact="HIGH",
                currency="USD",
                forecast="200K",
                previous="180K"
            ),
            NewsEvent(
                title="Unemployment Rate",
                time=now + timedelta(hours=2),
                impact="HIGH",
                currency="USD"
            ),
            NewsEvent(
                title="Retail Sales",
                time=now - timedelta(minutes=30),
                impact="MEDIUM",
                currency="USD"
            ),
        ]
