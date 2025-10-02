from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import os
from datetime import datetime

class JobScraper(ABC):
    def __init__(self, company_name: str):
        self.company = company_name
        self.current_listings = []

    @abstractmethod
    def scrape(self) -> List[Any]:
        """Scrape job listings from a specific job site."""
        pass

    def save(self, folder: str = None, last_seen_times: Dict[str, str] = None, keep_last_n: int = 3) -> None:
        """Save the current state of scraped job listings with last_seen timestamps."""
        if folder is None:
            folder = self.company

        if not os.path.exists(folder):
            os.makedirs(folder)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(folder, f"state_{timestamp}.json")

        state = {
            "listings": [job.to_dict() for job in self.current_listings],
            "last_seen": last_seen_times or {}
        }
        try:
            with open(filename, "w") as file:
                json.dump(state, file)
            print(f"State saved to {filename}")

            # Cleanup old state files, keep only the most recent N
            self._cleanup_old_states(folder, keep_last_n)
        except Exception as e:
            print(f"Failed to save state: {e}")

    def _cleanup_old_states(self, folder: str, keep_last_n: int) -> None:
        """Delete old state files, keeping only the most recent N files."""
        try:
            json_files = [f for f in os.listdir(folder) if f.endswith(".json") and f.startswith("state_")]
            if len(json_files) <= keep_last_n:
                return  # Nothing to cleanup

            # Sort by modification time (newest first)
            json_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)

            # Delete older files beyond keep_last_n
            files_to_delete = json_files[keep_last_n:]
            for old_file in files_to_delete:
                old_path = os.path.join(folder, old_file)
                os.remove(old_path)
                print(f"Deleted old state: {old_file}")
        except Exception as e:
            print(f"Error cleaning up old states: {e}")

    def load_previous_state(self, folder: str = None) -> tuple[List[Any], Dict[str, str]]:
        """Load the most recent saved state of job listings and last_seen timestamps."""
        if folder is None:
            folder = self.company

        if not os.path.exists(folder):
            print(f"No folder found for {folder}.")
            return [], {}

        json_files = [f for f in os.listdir(folder) if f.endswith(".json")]
        if not json_files:
            print(f"No previous state files found in {folder}.")
            return [], {}

        json_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
        latest_file = json_files[0]
        latest_filepath = os.path.join(folder, latest_file)

        try:
            with open(latest_filepath, "r") as file:
                previous_state = json.load(file)
                listings = [self._create_listing_from_dict(data) for data in previous_state.get("listings", [])]
                last_seen = previous_state.get("last_seen", {})
                return listings, last_seen
        except Exception as e:
            print(f"Error loading previous state: {e}")
            return [], {}

    @abstractmethod
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> Any:
        """Convert a dictionary back into a job listing object."""
        pass
