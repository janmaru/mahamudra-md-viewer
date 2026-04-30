"""
Use case: Export markdown to PDF.
Coordinates infrastructure services.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app_context import AppContext


class ExportMarkdownUseCase:
    """Use case for exporting markdown content to PDF."""

    def execute(self, ctx: AppContext, output_path: Path) -> bool:
        """Export current file to PDF.
        
        Args:
            ctx: Application context
            output_path: Path where to save PDF
            
        Returns:
            True if export successful, False otherwise.
        """
        if not ctx.current_file or not ctx.current_file.exists():
            return False

        try:
            from services.pdf_exporter import export_pdf
            export_pdf(ctx, ctx._renderer, output_path)
            return True
        except Exception:
            return False
