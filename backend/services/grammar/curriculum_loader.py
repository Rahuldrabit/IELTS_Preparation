"""Grammar curriculum loader - reads JSON curriculum files and provides structured access."""
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class CurriculumLoader:
    """Loads and provides access to grammar curriculum content from JSON files."""
    
    def __init__(self, curriculum_dir: Optional[str] = None):
        self.curriculum_dir = curriculum_dir or os.path.join(
            os.path.dirname(__file__), "curriculum"
        )
        self.modules: Dict[int, Dict] = {}
        self.topics: Dict[int, Dict] = {}
        self._load_curriculum()
    
    def _load_curriculum(self) -> None:
        """Load all curriculum JSON files."""
        curriculum_path = Path(self.curriculum_dir)
        
        if not curriculum_path.exists():
            raise FileNotFoundError(f"Curriculum directory not found: {curriculum_path}")
        
        for json_file in curriculum_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    module_data = json.load(f)
                
                module_id = module_data.get("module_id")
                if module_id is None:
                    continue
                
                self.modules[module_id] = module_data
                
                # Index topics by ID for easy lookup
                for topic in module_data.get("topics", []):
                    topic_id = topic.get("topic_id")
                    if topic_id:
                        self.topics[topic_id] = {
                            **topic,
                            "module_id": module_id,
                            "module_name": module_data["module_name"]
                        }
                        
            except Exception as e:
                print(f"Error loading curriculum file {json_file}: {e}")
    
    def get_module(self, module_id: int) -> Optional[Dict]:
        """Get a module by ID."""
        return self.modules.get(module_id)
    
    def get_topic(self, topic_id: int) -> Optional[Dict]:
        """Get a topic by ID."""
        return self.topics.get(topic_id)
    
    def get_all_modules(self) -> List[Dict]:
        """Get all modules in order."""
        return [self.modules[module_id] for module_id in sorted(self.modules.keys())]
    
    def get_all_topics(self) -> List[Dict]:
        """Get all topics across all modules."""
        return [self.topics[topic_id] for topic_id in sorted(self.topics.keys())]
    
    def get_topics_by_module(self, module_id: int) -> List[Dict]:
        """Get all topics for a specific module."""
        module = self.get_module(module_id)
        if not module:
            return []
        return module.get("topics", [])
    
    def get_topic_by_name(self, topic_name: str) -> Optional[Dict]:
        """Get a topic by name."""
        for topic_id, topic in self.topics.items():
            if topic["topic_name"] == topic_name:
                return topic
        return None
    
    def get_lesson_content(self, topic_id: int) -> Optional[Dict]:
        """Get full lesson content for a topic."""
        topic = self.get_topic(topic_id)
        if not topic:
            return None
        
        return {
            "topic_id": topic["topic_id"],
            "topic_name": topic["topic_name"],
            "module_id": topic["module_id"],
            "module_name": topic["module_name"],
            "description": topic["description"],
            "rules": topic.get("rules", []),
            "examples": topic.get("examples", {}),
            "common_mistakes": topic.get("common_mistakes", [])
        }
    
    def get_journey_map(self) -> Dict[str, Any]:
        """Get the full grammar journey map with module/topic structure."""
        modules_list = []
        
        for module_id in sorted(self.modules.keys()):
            module = self.modules[module_id]
            topics = module.get("topics", [])
            
            modules_list.append({
                "module_id": module_id,
                "module_name": module["module_name"],
                "description": module.get("description", ""),
                "topic_count": len(topics),
                "topics": [
                    {
                        "topic_id": topic["topic_id"],
                        "topic_name": topic["topic_name"],
                        "description": topic.get("description", ""),
                        "order": topic.get("order", 0)
                    }
                    for topic in topics
                ]
            })
        
        return {
            "total_modules": len(self.modules),
            "total_topics": len(self.topics),
            "modules": modules_list
        }


# Singleton instance
_curriculum_loader: Optional[CurriculumLoader] = None


def get_curriculum_loader() -> CurriculumLoader:
    """Get the singleton curriculum loader instance."""
    global _curriculum_loader
    if _curriculum_loader is None:
        _curriculum_loader = CurriculumLoader()
    return _curriculum_loader