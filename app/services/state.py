from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class AppState:
    latest_html_path: Optional[Path] = None
    ingested_files: Dict[str, Path] = field(default_factory=dict)

    def update_file(self, filename: str, path: Path) -> None:
        self.ingested_files[filename] = path
        if path.suffix.lower() in {".html", ".htm"}:
            self.latest_html_path = path


app_state = AppState()
