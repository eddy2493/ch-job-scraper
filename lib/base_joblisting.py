from abc import ABC, abstractmethod
from typing import Dict, Any


class JobListing(ABC):
    @abstractmethod
    def get_id(self) -> str:
        """Return a unique ID for the job listing."""
        pass

    @abstractmethod
    def generate_telegram_message(self) -> str:
        """Generate a formatted Telegram message for the job listing."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the job listing into a dictionary format."""
        pass