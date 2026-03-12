"""
Card management window for viewing, filtering, and managing flashcards.
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QComboBox,
                              QLabel, QLineEdit, QMessageBox, QHeaderView,
                              QCheckBox, QRadioButton, QButtonGroup, QGroupBox,
                              QFormLayout, QScrollArea, QFrame, QWidget,
                              QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer


class FilterCheckboxPanel(QWidget):
    """A scrollable panel of checkboxes for multi-select filtering."""

    filter_changed = pyqtSignal()

    def __init__(self, title: str, items: list, parent=None):
        """
        Initialize the filter panel.

        Args:
            title: Panel title
            items: List of filter items (strings)
            parent: Parent widget
        """
        super().__init__(parent)
        self.title = title
        self.items = items
        self.checkboxes = {}
        self.all_checkbox = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Title label
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50;")
        layout.addWidget(title_label)

        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.StyledPanel)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)

        # Container for checkboxes
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        checkbox_layout = QVBoxLayout(container)
        checkbox_layout.setContentsMargins(5, 5, 5, 5)
        checkbox_layout.setSpacing(2)

        # "All" checkbox
        self.all_checkbox = QCheckBox("All")
        self.all_checkbox.setChecked(True)
        self.all_checkbox.setStyleSheet("color: #2c3e50; font-weight: bold;")
        self.all_checkbox.stateChanged.connect(self._on_all_changed)
        checkbox_layout.addWidget(self.all_checkbox)

        # Individual item checkboxes
        for item in self.items:
            cb = QCheckBox(item)
            cb.setStyleSheet("color: #2c3e50;")
            cb.stateChanged.connect(self._on_item_changed)
            checkbox_layout.addWidget(cb)
            self.checkboxes[item] = cb

        checkbox_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _on_all_changed(self, state):
        """Handle 'All' checkbox change."""
        if state == Qt.Checked:
            # Uncheck all individual items
            for cb in self.checkboxes.values():
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
            self.filter_changed.emit()

    def _on_item_changed(self, state):
        """Handle individual item checkbox change."""
        # Check if any items are selected
        any_selected = any(cb.isChecked() for cb in self.checkboxes.values())

        # Update "All" checkbox
        self.all_checkbox.blockSignals(True)
        self.all_checkbox.setChecked(not any_selected)
        self.all_checkbox.blockSignals(False)

        self.filter_changed.emit()

    def get_selected(self) -> list:
        """
        Get list of selected items.

        Returns:
            List of selected item strings, or empty list if "All" is selected
        """
        if self.all_checkbox.isChecked():
            return []  # Empty means "all"
        return [item for item, cb in self.checkboxes.items() if cb.isChecked()]

    def is_all_selected(self) -> bool:
        """Check if 'All' is selected."""
        return self.all_checkbox.isChecked()

    def set_items(self, items: list):
        """
        Update the list of items.

        Args:
            items: New list of filter items
        """
        # Clear existing checkboxes (except "All")
        container = self.all_checkbox.parent()
        layout = container.layout()

        # Remove old checkboxes
        for cb in self.checkboxes.values():
            layout.removeWidget(cb)
            cb.deleteLater()
        self.checkboxes.clear()

        # Remove stretch
        while layout.count() > 1:
            item = layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        # Add new checkboxes
        self.items = items
        for item in items:
            cb = QCheckBox(item)
            cb.setStyleSheet("color: #2c3e50;")
            cb.stateChanged.connect(self._on_item_changed)
            layout.addWidget(cb)
            self.checkboxes[item] = cb

        layout.addStretch()

        # Reset to "All" selected
        self.all_checkbox.setChecked(True)


class CardManager(QDialog):
    """Dialog for managing flashcards."""

    # Signal emitted when a group is saved
    group_saved = pyqtSignal()

    def __init__(self, database, parent=None):
        """
        Initialize the card manager.

        Args:
            database: Database instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.database = database
        self.all_cards = []
        self.filtered_cards = []
        self.selected_subset = set()  # IDs of cards selected for study
        self.setup_ui()
        self.load_cards()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Manage Flashcards")
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Title and search row
        header_layout = QHBoxLayout()

        title = QLabel("Flashcard Manager")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Search box
        header_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search front, reading, or meaning...")
        self.search_box.setMinimumWidth(250)
        self.search_box.textChanged.connect(self.apply_filters)
        header_layout.addWidget(self.search_box)

        layout.addLayout(header_layout)

        # Filter description
        filter_desc = QLabel("Filters: Select items within each column (OR logic), columns combine with AND logic")
        filter_desc.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(filter_desc)

        # Filter panels in a horizontal layout
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        # Type filter panel
        type_items = ["kanji", "vocabulary", "phrase", "kana", "pronunciation"]
        self.type_panel = FilterCheckboxPanel("Type", type_items)
        self.type_panel.filter_changed.connect(self.apply_filters)
        filter_layout.addWidget(self.type_panel)

        # Level filter panel
        level_items = ["N5", "N4", "N3", "N2", "N1", "custom"]
        self.level_panel = FilterCheckboxPanel("Level", level_items)
        self.level_panel.filter_changed.connect(self.apply_filters)
        filter_layout.addWidget(self.level_panel)

        # Source file filter panel (populated after loading cards)
        self.source_panel = FilterCheckboxPanel("Source File", [])
        self.source_panel.filter_changed.connect(self.apply_filters)
        filter_layout.addWidget(self.source_panel)

        # Tags filter panel (populated after loading cards)
        self.tags_panel = FilterCheckboxPanel("Tags", [])
        self.tags_panel.filter_changed.connect(self.apply_filters)
        filter_layout.addWidget(self.tags_panel)

        # Set fixed height for filter panels
        filter_container = QWidget()
        filter_container.setLayout(filter_layout)
        filter_container.setFixedHeight(180)
        layout.addWidget(filter_container)

        # Cards table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Select", "Front", "Reading", "Meaning", "Type", "Level", "Source", "Tags"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Stats label
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.stats_label)

        # Action buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All for Study")
        self.select_all_btn.clicked.connect(self.select_all_for_study)
        button_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton("Clear Study Selection")
        self.clear_selection_btn.clicked.connect(self.clear_study_selection)
        button_layout.addWidget(self.clear_selection_btn)

        self.save_group_btn = QPushButton("Save as Group")
        self.save_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.save_group_btn.clicked.connect(self.save_as_group)
        button_layout.addWidget(self.save_group_btn)

        button_layout.addStretch()

        self.delete_btn = QPushButton("Delete Selected Cards")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_btn)

        self.delete_all_btn = QPushButton("Delete All Cards")
        self.delete_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #922b21;
            }
        """)
        self.delete_all_btn.clicked.connect(self.delete_all_cards)
        button_layout.addWidget(self.delete_all_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_cards(self):
        """Load all cards from the database."""
        self.all_cards = self.database.get_all_cards()

        # Block filter signals during panel rebuild to prevent cascading updates
        self.source_panel.blockSignals(True)
        self.tags_panel.blockSignals(True)

        # Populate source file panel with unique filenames
        source_files = set()
        for card in self.all_cards:
            file_path = card.get('file_path', '')
            if file_path:
                filename = os.path.basename(file_path)
                source_files.add(filename)
        self.source_panel.set_items(sorted(source_files))

        # Populate tags panel with unique tags
        tags = set()
        for card in self.all_cards:
            card_tags = card.get('tags', '') or ''
            for tag in card_tags.split(','):
                tag = tag.strip()
                if tag:
                    tags.add(tag)
        self.tags_panel.set_items(sorted(tags))

        # Restore signals and apply filters
        self.source_panel.blockSignals(False)
        self.tags_panel.blockSignals(False)

        self.apply_filters()

    def _reload_cards_safely(self):
        """Reload cards with signal blocking to prevent crashes during rebuild."""
        try:
            self.table.blockSignals(True)
            self.load_cards()
        except Exception as e:
            print(f"Error reloading cards: {e}")
        finally:
            self.table.blockSignals(False)

    def apply_filters(self):
        """Apply current filters to card list using multi-select AND/OR logic."""
        # Get selected values from each panel
        selected_types = self.type_panel.get_selected()
        selected_levels = self.level_panel.get_selected()
        selected_sources = self.source_panel.get_selected()
        selected_tags = self.tags_panel.get_selected()
        search_text = self.search_box.text().lower()

        # Filter cards
        self.filtered_cards = []
        for card in self.all_cards:
            # Type filter (OR within selection)
            if selected_types:
                if card.get('card_type') not in selected_types:
                    continue

            # Level filter (OR within selection)
            if selected_levels:
                if card.get('level') not in selected_levels:
                    continue

            # Source file filter (OR within selection)
            if selected_sources:
                file_path = card.get('file_path', '')
                filename = os.path.basename(file_path) if file_path else ''
                if filename not in selected_sources:
                    continue

            # Tags filter (OR within selection - card must have at least one selected tag)
            if selected_tags:
                card_tags = card.get('tags', '') or ''
                card_tag_list = [t.strip() for t in card_tags.split(',')]
                if not any(tag in card_tag_list for tag in selected_tags):
                    continue

            # Search filter
            if search_text:
                searchable = (
                    card.get('front', '').lower() +
                    card.get('reading', '').lower() +
                    card.get('meaning', '').lower()
                )
                if search_text not in searchable:
                    continue

            self.filtered_cards.append(card)

        self.update_table()

    def update_table(self):
        """Update the table with filtered cards."""
        # Block signals and clear cell widgets before changing row count
        # to prevent stale checkbox stateChanged signals from firing
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget is not None:
                widget.blockSignals(True)
                self.table.removeCellWidget(row, 0)
        self.table.setRowCount(0)
        self.table.blockSignals(False)

        self.table.setRowCount(len(self.filtered_cards))

        for row, card in enumerate(self.filtered_cards):
            # Checkbox for study selection
            checkbox = QCheckBox()
            checkbox.setChecked(card['id'] in self.selected_subset)
            checkbox.stateChanged.connect(
                lambda state, card_id=card['id']: self.toggle_study_selection(card_id, state)
            )
            checkbox_widget = QTableWidgetItem()
            self.table.setItem(row, 0, checkbox_widget)
            self.table.setCellWidget(row, 0, checkbox)

            # Card data
            self.table.setItem(row, 1, QTableWidgetItem(card.get('front', '')))
            self.table.setItem(row, 2, QTableWidgetItem(card.get('reading', '')))
            self.table.setItem(row, 3, QTableWidgetItem(card.get('meaning', '')))
            self.table.setItem(row, 4, QTableWidgetItem(card.get('card_type', '')))
            self.table.setItem(row, 5, QTableWidgetItem(card.get('level', '')))

            # Source file (extract filename from path)
            file_path = card.get('file_path', '')
            source_name = os.path.basename(file_path) if file_path else ''
            self.table.setItem(row, 6, QTableWidgetItem(source_name))

            self.table.setItem(row, 7, QTableWidgetItem(card.get('tags', '') or ''))

        # Update stats
        self.stats_label.setText(
            f"Showing {len(self.filtered_cards)} of {len(self.all_cards)} cards | "
            f"Selected for study: {len(self.selected_subset)}"
        )

    def toggle_study_selection(self, card_id: int, state: int):
        """
        Toggle a card's study selection status.

        Args:
            card_id: The card ID
            state: Checkbox state (Qt.Checked or Qt.Unchecked)
        """
        if state == Qt.Checked:
            self.selected_subset.add(card_id)
        else:
            self.selected_subset.discard(card_id)

        self.stats_label.setText(
            f"Showing {len(self.filtered_cards)} of {len(self.all_cards)} cards | "
            f"Selected for study: {len(self.selected_subset)}"
        )

    def select_all_for_study(self):
        """Select all filtered cards for study."""
        for card in self.filtered_cards:
            self.selected_subset.add(card['id'])
        self.update_table()

    def clear_study_selection(self):
        """Clear study selection."""
        self.selected_subset.clear()
        self.update_table()

    def _block_all_signals(self, block: bool):
        """Block or unblock signals on all interactive widgets.

        This prevents spurious signal firing during modal dialogs
        which can cause crashes in PyQt5's nested event loops.
        """
        self.table.blockSignals(block)
        self.type_panel.blockSignals(block)
        self.level_panel.blockSignals(block)
        self.source_panel.blockSignals(block)
        self.tags_panel.blockSignals(block)
        self.search_box.blockSignals(block)

        # Also block signals on all checkbox cell widgets in the table
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget is not None:
                widget.blockSignals(block)

    def delete_selected(self):
        """Delete selected cards from the database."""
        try:
            # Collect card IDs from two sources:
            # 1. Rows highlighted via table row selection (clicking/shift-clicking rows)
            # 2. Rows with study checkboxes ticked (via "Select All for Study" etc.)
            card_ids_to_delete = set()

            # Source 1: table row selection
            selected_indexes = self.table.selectionModel().selectedRows()
            for index in selected_indexes:
                row = index.row()
                if 0 <= row < len(self.filtered_cards):
                    card_ids_to_delete.add(self.filtered_cards[row]['id'])

            # Source 2: study checkboxes that are ticked
            for row in range(self.table.rowCount()):
                widget = self.table.cellWidget(row, 0)
                if widget is not None and widget.isChecked():
                    if 0 <= row < len(self.filtered_cards):
                        card_ids_to_delete.add(self.filtered_cards[row]['id'])

            if not card_ids_to_delete:
                self.stats_label.setText(
                    "No cards selected. Click on rows or tick checkboxes to select cards for deletion."
                )
                return

            card_ids_to_delete = list(card_ids_to_delete)
            count = len(card_ids_to_delete)

            # Block all widget signals during the confirmation dialog
            # to prevent spurious events in the nested event loop
            self._block_all_signals(True)
            try:
                reply = QMessageBox.question(
                    self,
                    "Confirm Deletion",
                    f"Are you sure you want to delete {count} card(s)?\n\n"
                    "This will permanently remove the selected cards and all "
                    "their review history.\n\n"
                    "This action cannot be undone.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
            finally:
                self._block_all_signals(False)

            if reply != QMessageBox.Yes:
                return

            # Perform deletion
            deleted_count = 0
            for card_id in card_ids_to_delete:
                try:
                    if self.database.delete_card(card_id):
                        deleted_count += 1
                        self.selected_subset.discard(card_id)
                except Exception as e:
                    print(f"Error deleting card {card_id}: {e}")

            # Update status label instead of showing another modal dialog
            self.stats_label.setText(f"Successfully deleted {deleted_count} card(s).")

            # Defer reload to after all event processing completes
            QTimer.singleShot(0, self._reload_cards_safely)

        except Exception as e:
            print(f"Error in delete_selected: {e}")
            import traceback
            traceback.print_exc()
            self.stats_label.setText(f"Error during deletion: {e}")

    def delete_all_cards(self):
        """Delete all cards from the database, resetting the system."""
        try:
            total_cards = len(self.all_cards)
            if total_cards == 0:
                self.stats_label.setText("No cards to delete.")
                return

            # Block all widget signals during confirmation dialogs
            self._block_all_signals(True)
            try:
                # First confirmation
                reply = QMessageBox.warning(
                    self,
                    "Delete All Cards",
                    f"WARNING: You are about to delete ALL {total_cards} cards "
                    "from the database.\n\n"
                    "This will permanently remove:\n"
                    "  - All flashcards\n"
                    "  - All review history\n"
                    "  - All study sessions\n"
                    "  - All card groups\n"
                    "  - All source file and tag references\n\n"
                    "This action CANNOT be undone.\n\n"
                    "Are you sure you want to proceed?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
            finally:
                self._block_all_signals(False)

            if reply != QMessageBox.Yes:
                return

            # Second confirmation for safety
            self._block_all_signals(True)
            try:
                reply2 = QMessageBox.critical(
                    self,
                    "Final Confirmation",
                    f"FINAL WARNING: This will permanently delete all "
                    f"{total_cards} cards and reset the entire system.\n\n"
                    "Click Yes to confirm deletion.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
            finally:
                self._block_all_signals(False)

            if reply2 != QMessageBox.Yes:
                return

            # Perform deletion
            deleted_count = self.database.delete_all_cards()

            if deleted_count >= 0:
                self.selected_subset.clear()
                self.stats_label.setText(
                    f"All {deleted_count} cards deleted. System has been reset."
                )
            else:
                self.stats_label.setText("Error occurred while deleting cards.")

            # Defer reload to after all event processing completes
            QTimer.singleShot(0, self._reload_cards_safely)

        except Exception as e:
            print(f"Error in delete_all_cards: {e}")
            import traceback
            traceback.print_exc()
            self.stats_label.setText(f"Error during deletion: {e}")

    def get_selected_subset(self):
        """
        Get the set of selected card IDs for study.

        Returns:
            Set of card IDs
        """
        return self.selected_subset

    def _get_current_filters(self):
        """Get current filter settings as a dictionary."""
        selected_types = self.type_panel.get_selected()
        selected_levels = self.level_panel.get_selected()
        selected_sources = self.source_panel.get_selected()
        selected_tags = self.tags_panel.get_selected()

        return {
            'type': ','.join(selected_types) if selected_types else None,
            'level': ','.join(selected_levels) if selected_levels else None,
            'source': ','.join(selected_sources) if selected_sources else None,
            'tags': ','.join(selected_tags) if selected_tags else None
        }

    def _has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        return any([
            not self.type_panel.is_all_selected(),
            not self.level_panel.is_all_selected(),
            not self.source_panel.is_all_selected(),
            not self.tags_panel.is_all_selected()
        ])

    def save_as_group(self):
        """Open dialog to save current selection/filters as a named group."""
        # Check if we have any selection or filters
        has_selection = len(self.selected_subset) > 0
        has_filters = self._has_active_filters()

        if not has_selection and not has_filters:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please either select specific cards or apply filters before saving a group."
            )
            return

        # Open save dialog
        dialog = GroupSaveDialog(
            has_selection=has_selection,
            has_filters=has_filters,
            filters=self._get_current_filters(),
            selection_count=len(self.selected_subset),
            filtered_count=len(self.filtered_cards),
            parent=self
        )

        if dialog.exec_() == QDialog.Accepted:
            name, group_type = dialog.get_result()

            # Check if name already exists
            existing = self.database.get_card_group_by_name(name)
            if existing:
                reply = QMessageBox.question(
                    self,
                    "Group Exists",
                    f"A group named '{name}' already exists. Do you want to replace it?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                # Delete existing group
                self.database.delete_card_group(existing['id'])

            # Create the group
            if group_type == 'static':
                # Save specific card IDs
                card_ids = list(self.selected_subset) if has_selection else [c['id'] for c in self.filtered_cards]
                group_id = self.database.create_card_group(
                    name=name,
                    group_type='static',
                    card_ids=card_ids
                )
            else:
                # Save filter criteria
                filters = self._get_current_filters()
                group_id = self.database.create_card_group(
                    name=name,
                    group_type='dynamic',
                    filter_type=filters['type'],
                    filter_level=filters['level'],
                    filter_tags=filters['tags']
                )

            if group_id:
                QMessageBox.information(
                    self,
                    "Group Saved",
                    f"Group '{name}' has been saved successfully."
                )
                # Notify that a group was saved
                self.group_saved.emit()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to save the group. Please try again."
                )


class GroupSaveDialog(QDialog):
    """Dialog for saving a card group with name and type selection."""

    def __init__(self, has_selection: bool, has_filters: bool, filters: dict,
                 selection_count: int, filtered_count: int, parent=None):
        """
        Initialize the group save dialog.

        Args:
            has_selection: Whether cards are manually selected
            has_filters: Whether filters are applied
            filters: Current filter settings
            selection_count: Number of selected cards
            filtered_count: Number of filtered cards
            parent: Parent widget
        """
        super().__init__(parent)
        self.has_selection = has_selection
        self.has_filters = has_filters
        self.filters = filters
        self.selection_count = selection_count
        self.filtered_count = filtered_count
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Save Card Group")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Group name
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter group name...")
        form_layout.addRow("Group Name:", self.name_edit)
        layout.addLayout(form_layout)

        # Group type selection
        type_group = QGroupBox("Group Type")
        type_layout = QVBoxLayout()

        self.type_button_group = QButtonGroup(self)

        # Static option
        self.static_radio = QRadioButton("Static (fixed set of cards)")
        if self.has_selection:
            self.static_radio.setText(f"Static ({self.selection_count} selected cards)")
        else:
            self.static_radio.setText(f"Static ({self.filtered_count} filtered cards)")
        self.type_button_group.addButton(self.static_radio, 0)
        type_layout.addWidget(self.static_radio)

        static_desc = QLabel("Cards are saved by ID. Group won't change unless manually updated.")
        static_desc.setStyleSheet("color: #7f8c8d; margin-left: 20px; font-size: 11px;")
        static_desc.setWordWrap(True)
        type_layout.addWidget(static_desc)

        # Dynamic option (only if filters are set)
        self.dynamic_radio = QRadioButton("Dynamic (based on current filters)")
        if self.has_filters:
            filter_desc_parts = []
            if self.filters.get('type'):
                filter_desc_parts.append(f"Type: {self.filters['type']}")
            if self.filters.get('level'):
                filter_desc_parts.append(f"Level: {self.filters['level']}")
            if self.filters.get('source'):
                filter_desc_parts.append(f"Source: {self.filters['source']}")
            if self.filters.get('tags'):
                filter_desc_parts.append(f"Tags: {self.filters['tags']}")
            filter_text = "; ".join(filter_desc_parts)
            self.dynamic_radio.setText(f"Dynamic ({filter_text})")
        else:
            self.dynamic_radio.setEnabled(False)
            self.dynamic_radio.setText("Dynamic (no filters applied)")

        self.type_button_group.addButton(self.dynamic_radio, 1)
        type_layout.addWidget(self.dynamic_radio)

        dynamic_desc = QLabel("Group automatically includes cards matching the filter criteria.")
        dynamic_desc.setStyleSheet("color: #7f8c8d; margin-left: 20px; font-size: 11px;")
        dynamic_desc.setWordWrap(True)
        type_layout.addWidget(dynamic_desc)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Default selection
        if self.has_selection:
            self.static_radio.setChecked(True)
        elif self.has_filters:
            self.dynamic_radio.setChecked(True)
        else:
            self.static_radio.setChecked(True)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Group")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        save_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def validate_and_accept(self):
        """Validate input and accept dialog."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a group name.")
            return
        self.accept()

    def get_result(self):
        """
        Get the dialog result.

        Returns:
            Tuple of (name, group_type)
        """
        name = self.name_edit.text().strip()
        group_type = 'static' if self.static_radio.isChecked() else 'dynamic'
        return name, group_type
