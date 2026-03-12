"""
Stroke order widget for displaying kanji stroke order.

This widget renders KanjiVG SVG data to show stroke order
for kanji characters.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath
from PyQt5.QtSvg import QSvgRenderer
from typing import Optional
import re


class StrokeOrderWidget(QWidget):
    """Widget to display kanji stroke order from SVG data."""

    def __init__(self, parent=None):
        """
        Initialize the stroke order widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._svg_data: Optional[str] = None
        self._renderer: Optional[QSvgRenderer] = None
        self._stroke_count = 0
        self._current_stroke = 0  # For animation
        self._animating = False
        self._animation_timer: Optional[QTimer] = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # SVG display area
        self.svg_widget = StrokeSvgWidget(self)
        self.svg_widget.setMinimumSize(120, 120)
        self.svg_widget.setMaximumSize(200, 200)
        layout.addWidget(self.svg_widget, alignment=Qt.AlignCenter)

        # Stroke count label
        self.stroke_label = QLabel("Strokes: -")
        self.stroke_label.setAlignment(Qt.AlignCenter)
        self.stroke_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        layout.addWidget(self.stroke_label)

        # Animation controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)

        self.play_btn = QPushButton("Play")
        self.play_btn.setFixedWidth(60)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.play_btn.clicked.connect(self._toggle_animation)
        controls_layout.addWidget(self.play_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedWidth(60)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.reset_btn.clicked.connect(self._reset_animation)
        controls_layout.addWidget(self.reset_btn)

        layout.addLayout(controls_layout)

        self.setLayout(layout)
        self.setStyleSheet("""
            StrokeOrderWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """)

    def set_svg(self, svg_data: str, stroke_count: int = 0):
        """
        Set the SVG data to display.

        Args:
            svg_data: SVG content as a string
            stroke_count: Number of strokes
        """
        self._svg_data = svg_data
        self._stroke_count = stroke_count
        self._current_stroke = stroke_count  # Show all strokes initially

        # Update stroke label
        if stroke_count > 0:
            self.stroke_label.setText(f"Strokes: {stroke_count}")
        else:
            self.stroke_label.setText("Strokes: -")

        # Create renderer
        if svg_data:
            self._renderer = QSvgRenderer()
            self._renderer.load(svg_data.encode("utf-8"))
            self.svg_widget.set_renderer(self._renderer)
            self.play_btn.setEnabled(True)
        else:
            self._renderer = None
            self.svg_widget.set_renderer(None)
            self.play_btn.setEnabled(False)

        self.svg_widget.update()

    def clear(self):
        """Clear the stroke order display."""
        self._svg_data = None
        self._renderer = None
        self._stroke_count = 0
        self._current_stroke = 0
        self._stop_animation()
        self.stroke_label.setText("Strokes: -")
        self.svg_widget.set_renderer(None)
        self.svg_widget.update()

    def _toggle_animation(self):
        """Toggle stroke animation on/off."""
        if self._animating:
            self._stop_animation()
        else:
            self._start_animation()

    def _start_animation(self):
        """Start the stroke-by-stroke animation."""
        if not self._svg_data or self._stroke_count == 0:
            return

        self._animating = True
        self._current_stroke = 0
        self.play_btn.setText("Pause")

        # Create animation timer
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animation_step)
        self._animation_timer.start(500)  # 500ms per stroke

    def _stop_animation(self):
        """Stop the animation."""
        self._animating = False
        self.play_btn.setText("Play")

        if self._animation_timer:
            self._animation_timer.stop()
            self._animation_timer = None

    def _reset_animation(self):
        """Reset animation to show all strokes."""
        self._stop_animation()
        self._current_stroke = self._stroke_count
        self._update_visible_strokes()

    def _animation_step(self):
        """Advance animation by one stroke."""
        if self._current_stroke < self._stroke_count:
            self._current_stroke += 1
            self._update_visible_strokes()
        else:
            # Animation complete
            self._stop_animation()

    def _update_visible_strokes(self):
        """Update the SVG to show only the current number of strokes."""
        if not self._svg_data:
            return

        # Modify SVG to show only strokes up to current_stroke
        modified_svg = self._modify_svg_visibility(
            self._svg_data, self._current_stroke
        )

        if modified_svg:
            renderer = QSvgRenderer()
            renderer.load(modified_svg.encode("utf-8"))
            self.svg_widget.set_renderer(renderer)
        self.svg_widget.update()

    def _modify_svg_visibility(self, svg_data: str, visible_strokes: int) -> str:
        """
        Modify SVG to show only the specified number of strokes.

        Args:
            svg_data: Original SVG content
            visible_strokes: Number of strokes to show

        Returns:
            Modified SVG content
        """
        # Find all path elements and hide those beyond visible_strokes
        path_pattern = re.compile(r'(<path[^>]*>)', re.IGNORECASE)
        paths = path_pattern.findall(svg_data)

        modified = svg_data
        for i, path in enumerate(paths):
            if i >= visible_strokes:
                # Hide this stroke by setting opacity to 0
                if 'style="' in path:
                    hidden_path = path.replace('style="', 'style="opacity:0;')
                else:
                    hidden_path = path.replace('<path', '<path style="opacity:0"')
                modified = modified.replace(path, hidden_path)

        return modified


class StrokeSvgWidget(QWidget):
    """Widget that renders SVG using QSvgRenderer."""

    def __init__(self, parent=None):
        """Initialize the SVG widget."""
        super().__init__(parent)
        self._renderer: Optional[QSvgRenderer] = None
        self.setMinimumSize(100, 100)

    def set_renderer(self, renderer: Optional[QSvgRenderer]):
        """Set the SVG renderer."""
        self._renderer = renderer
        self.update()

    def paintEvent(self, event):
        """Paint the SVG content."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), QColor("#ffffff"))

        # Draw grid lines (guide for stroke practice)
        self._draw_grid(painter)

        # Draw SVG
        if self._renderer and self._renderer.isValid():
            # Center the SVG in the widget
            size = self._renderer.defaultSize()
            if size.width() > 0 and size.height() > 0:
                # Scale to fit
                scale = min(
                    (self.width() - 10) / size.width(),
                    (self.height() - 10) / size.height()
                )
                scaled_width = size.width() * scale
                scaled_height = size.height() * scale

                x = (self.width() - scaled_width) / 2
                y = (self.height() - scaled_height) / 2

                from PyQt5.QtCore import QRectF
                target_rect = QRectF(x, y, scaled_width, scaled_height)
                self._renderer.render(painter, target_rect)

    def _draw_grid(self, painter: QPainter):
        """Draw guide grid lines."""
        pen = QPen(QColor("#e0e0e0"))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        # Center cross
        cx = self.width() // 2
        cy = self.height() // 2

        # Vertical line
        painter.drawLine(cx, 5, cx, self.height() - 5)
        # Horizontal line
        painter.drawLine(5, cy, self.width() - 5, cy)

        # Diagonal lines (optional, for more detailed guide)
        pen.setColor(QColor("#f0f0f0"))
        painter.setPen(pen)
        painter.drawLine(5, 5, self.width() - 5, self.height() - 5)
        painter.drawLine(self.width() - 5, 5, 5, self.height() - 5)
