import os
import json

class SimpleJsonStore:
    """Simple JSON-based data store."""
    
    def __init__(self):
        """Initialize the data store."""
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def save_candidates(self, job_id, candidates):
        """Save candidates to a JSON file."""
        filename = os.path.join(self.data_dir, f"job_{job_id}.json")
        with open(filename, "w") as f:
            json.dump(candidates, f, indent=2)
    
    def load_candidates(self, job_id):
        """Load candidates from a JSON file."""
        filename = os.path.join(self.data_dir, f"job_{job_id}.json")
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return []
    
    def save_results(self, filename, results):
        """Save results to a JSON file."""
        file_path = os.path.join(self.data_dir, filename) if not os.path.isabs(filename) else filename
        with open(file_path, "w") as f:
            json.dump(results, f, indent=2)