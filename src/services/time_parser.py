"""
Enhanced Time Parser

Advanced time parsing with support for natural language,
multiple formats, timezone awareness, and validation.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from src.config import config


class TimeParseError(Exception):
    """Exception raised when time parsing fails."""
    pass


class EnhancedTimeParser:
    """Advanced time parser with natural language support."""
    
    def __init__(self):
        """Initialize the time parser."""
        self.timezone = ZoneInfo(config.SCHEDULER_TIMEZONE)
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for time parsing."""
        # Relative time patterns
        self.relative_patterns = [
            # "через X минут/часов/дней"
            (r'через\s+(\d+)\s+(минут[ауы]?|мин)', 'minutes'),
            (r'через\s+(\d+)\s+(час[аов]?)', 'hours'),
            (r'через\s+(\d+)\s+(день|дня|дней)', 'days'),
            (r'через\s+(\d+)\s+(неделя|недели|недель)', 'weeks'),
            
            # "in X minutes/hours/days" (English)
            (r'in\s+(\d+)\s+(minute[s]?|min[s]?)', 'minutes'),
            (r'in\s+(\d+)\s+(hour[s]?)', 'hours'),
            (r'in\s+(\d+)\s+(day[s]?)', 'days'),
            (r'in\s+(\d+)\s+(week[s]?)', 'weeks'),
        ]
        
        # Absolute time patterns
        self.absolute_patterns = [
            # "сегодня в HH:MM"
            (r'сегодня\s+в\s+(\d{1,2}):(\d{2})', 'today'),
            (r'today\s+at\s+(\d{1,2}):(\d{2})', 'today'),
            
            # "завтра в HH:MM"
            (r'завтра\s+в\s+(\d{1,2}):(\d{2})', 'tomorrow'),
            (r'tomorrow\s+at\s+(\d{1,2}):(\d{2})', 'tomorrow'),
            
            # "послезавтра в HH:MM"
            (r'послезавтра\s+в\s+(\d{1,2}):(\d{2})', 'day_after_tomorrow'),
            
            # "в понедельник в HH:MM"
            (r'в\s+(понедельник|вторник|среду?|четверг|пятницу|субботу|воскресенье)\s+в\s+(\d{1,2}):(\d{2})', 'weekday'),
            
            # "DD.MM в HH:MM" или "DD.MM.YYYY в HH:MM"
            (r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\s+в\s+(\d{1,2}):(\d{2})', 'date'),
        ]
        
        # Weekday mapping
        self.weekdays = {
            'понедельник': 0, 'вторник': 1, 'среду': 2, 'четверг': 3,
            'пятницу': 4, 'субботу': 5, 'воскресенье': 6,
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
    
    def parse(self, time_str: str) -> datetime:
        """
        Parse time string and return datetime object.
        
        Args:
            time_str: Time string to parse
            
        Returns:
            Parsed datetime object
            
        Raises:
            TimeParseError: If parsing fails
        """
        time_str = time_str.lower().strip()
        now = datetime.now(self.timezone)
        
        # Try relative time patterns
        result = self._parse_relative(time_str, now)
        if result:
            return result
        
        # Try absolute time patterns
        result = self._parse_absolute(time_str, now)
        if result:
            return result
        
        # Try special cases
        result = self._parse_special(time_str, now)
        if result:
            return result
        
        raise TimeParseError(f"Не удалось распознать формат времени: '{time_str}'")
    
    def _parse_relative(self, time_str: str, now: datetime) -> Optional[datetime]:
        """Parse relative time expressions."""
        for pattern, unit in self.relative_patterns:
            match = re.search(pattern, time_str, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                
                if unit == 'minutes':
                    return now + timedelta(minutes=value)
                elif unit == 'hours':
                    return now + timedelta(hours=value)
                elif unit == 'days':
                    return now + timedelta(days=value)
                elif unit == 'weeks':
                    return now + timedelta(weeks=value)
        
        return None
    
    def _parse_absolute(self, time_str: str, now: datetime) -> Optional[datetime]:
        """Parse absolute time expressions."""
        for pattern, time_type in self.absolute_patterns:
            match = re.search(pattern, time_str, re.IGNORECASE)
            if match:
                if time_type == 'today':
                    hour, minute = int(match.group(1)), int(match.group(2))
                    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target <= now:
                        target += timedelta(days=1)  # Next day if time passed
                    return target
                
                elif time_type == 'tomorrow':
                    hour, minute = int(match.group(1)), int(match.group(2))
                    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    return target + timedelta(days=1)
                
                elif time_type == 'day_after_tomorrow':
                    hour, minute = int(match.group(1)), int(match.group(2))
                    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    return target + timedelta(days=2)
                
                elif time_type == 'weekday':
                    weekday_name = match.group(1)
                    hour, minute = int(match.group(2)), int(match.group(3))
                    
                    target_weekday = self.weekdays.get(weekday_name)
                    if target_weekday is None:
                        continue
                    
                    return self._get_next_weekday(now, target_weekday, hour, minute)
                
                elif time_type == 'date':
                    day = int(match.group(1))
                    month = int(match.group(2))
                    year = int(match.group(3)) if match.group(3) else now.year
                    hour = int(match.group(4))
                    minute = int(match.group(5))
                    
                    try:
                        target = now.replace(year=year, month=month, day=day, 
                                           hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # If date is in the past and no year specified, try next year
                        if target <= now and not match.group(3):
                            target = target.replace(year=year + 1)
                        
                        return target
                    except ValueError:
                        continue  # Invalid date
        
        return None
    
    def _parse_special(self, time_str: str, now: datetime) -> Optional[datetime]:
        """Parse special time expressions."""
        special_cases = {
            'сейчас': now + timedelta(minutes=1),
            'скоро': now + timedelta(minutes=15),
            'потом': now + timedelta(hours=2),
            'позже': now + timedelta(hours=4),
            'вечером': now.replace(hour=18, minute=0, second=0, microsecond=0),
            'утром': (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0),
        }
        
        for phrase, target_time in special_cases.items():
            if phrase in time_str:
                # Adjust if time is in the past
                if target_time <= now:
                    if phrase == 'вечером':
                        target_time += timedelta(days=1)
                
                return target_time
        
        return None
    
    def _get_next_weekday(self, now: datetime, target_weekday: int, hour: int, minute: int) -> datetime:
        """Get next occurrence of a specific weekday."""
        days_ahead = target_weekday - now.weekday()
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        target = now + timedelta(days=days_ahead)
        return target.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    def get_suggestions(self, text: str) -> List[str]:
        """Get time suggestions based on reminder text."""
        text_lower = text.lower()
        suggestions = []
        
        # Context-based suggestions
        if any(word in text_lower for word in ['лекарство', 'таблетка', 'витамин', 'medicine']):
            suggestions.extend(['через 8 часов', 'завтра в 9:00', 'каждый день в 9:00'])
        
        elif any(word in text_lower for word in ['звонок', 'позвонить', 'call']):
            suggestions.extend(['через 30 минут', 'завтра в 10:00', 'в понедельник в 9:00'])
        
        elif any(word in text_lower for word in ['купить', 'магазин', 'buy', 'shop']):
            suggestions.extend(['через 2 часа', 'завтра после работы', 'в субботу'])
        
        elif any(word in text_lower for word in ['встреча', 'собрание', 'meeting']):
            suggestions.extend(['завтра в 14:00', 'в понедельник в 10:00'])
        
        else:
            # Generic suggestions
            suggestions.extend(['через 30 минут', 'через 1 час', 'завтра в 10:00'])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def validate_time(self, parsed_time: datetime) -> Tuple[bool, Optional[str]]:
        """
        Validate parsed time.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        now = datetime.now(self.timezone)
        
        # Check if time is in the future
        if parsed_time <= now:
            return False, "Время должно быть в будущем"
        
        # Check if time is too far in the future (more than 1 year)
        if parsed_time > now + timedelta(days=365):
            return False, "Время слишком далеко в будущем"
        
        # Check if hour and minute are valid
        if not (0 <= parsed_time.hour <= 23):
            return False, "Некорректный час"
        
        if not (0 <= parsed_time.minute <= 59):
            return False, "Некорректная минута"
        
        return True, None


# Global parser instance
time_parser = EnhancedTimeParser()
