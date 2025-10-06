from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import os
from datetime import datetime, timedelta

class JobScraper(ABC):
    def __init__(self, company_name: str):
        self.company = company_name
        self.current_listings = []

    @abstractmethod
    def scrape(self) -> List[Any]:
        """Scrape job listings from a specific job site."""
        pass

    def save(self, folder: str = None) -> None:
        """Save the current state of scraped job listings."""
        if folder is None:
            folder = self.company

        if not os.path.exists(folder):
            os.makedirs(folder)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(folder, f"state_{timestamp}.json")

        state = {"listings": [job.to_dict() for job in self.current_listings]}
        try:
            with open(filename, "w") as file:
                json.dump(state, file)
            print(f"State saved to {filename}")

            # Cleanup states older than 24 hours
            #self._cleanup_old_states(folder, max_age_hours=24)
        except Exception as e:
            print(f"Failed to save state: {e}")

    def _cleanup_old_states(self, folder: str, max_age_hours: int = 24) -> None:
        """Delete state files older than max_age_hours."""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=max_age_hours)

            json_files = [f for f in os.listdir(folder) if f.endswith(".json") and f.startswith("state_")]

            for json_file in json_files:
                file_path = os.path.join(folder, json_file)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    print(f"Deleted old state: {json_file}")
        except Exception as e:
            print(f"Error cleaning up old states: {e}")

    def load_previous_state(self, folder: str = None) -> List[Any]:
        """Load the most recent saved state of job listings."""
        if folder is None:
            folder = self.company

        if not os.path.exists(folder):
            print(f"No folder found for {folder}.")
            return []

        json_files = [f for f in os.listdir(folder) if f.endswith(".json")]
        if not json_files:
            print(f"No previous state files found in {folder}.")
            return []

        json_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
        latest_file = json_files[0]
        latest_filepath = os.path.join(folder, latest_file)

        try:
            with open(latest_filepath, "r") as file:
                previous_listings = json.load(file)
                return [self._create_listing_from_dict(data) for data in previous_listings.get("listings", [])]
        except Exception as e:
            print(f"Error loading previous state: {e}")
            return []

    @abstractmethod
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> Any:
        """Convert a dictionary back into a job listing object."""
        pass
