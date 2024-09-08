#
# Created on:  Sun Sep 08 2024
# By:  Lukas Mettler (lukas.mettler@student.kit.edu)
# https://github.com/LEMettler
#


import webbrowser
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QListWidget, QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QColorDialog, 
                             QScrollArea, QFrame)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSize
from consecutive_collisions import ConsecutiveCollisionBuilder


class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)

        self.toggle_button = QPushButton(title)
        self.toggle_button.setStyleSheet("text-align: left; padding: 5px;")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)

        self.toggle_button.toggled.connect(self.on_pressed)

        self.content_area = QScrollArea()
        self.content_area.setStyleSheet("QScrollArea { border: none; }")
        self.content_area.setWidgetResizable(True)

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation()

    def on_pressed(self):
        self.toggle_animation()

    def toggle_animation(self):
        checked = self.toggle_button.isChecked()
        self.content_area.setVisible(checked)

    def setContentLayout(self, layout):
        self.content_area.setWidget(QWidget())
        self.content_area.widget().setLayout(layout)

class CollisionGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.ccb = None

    def initUI(self):
        layout = QVBoxLayout()

        # Initial parameters
        init_group = QGroupBox("Initial Parameters")
        init_layout = QFormLayout()
        self.file_name = QLineEdit()
        self.file_name.setText('output.svg')
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(800)
        self.height_input = QSpinBox()
        self.height_input.setRange(1, 10000)
        self.height_input.setValue(400)
        self.poc_x_input = QSpinBox()
        self.poc_x_input.setRange(0, 10000)
        self.poc_x_input.setValue(300)
        self.poc_y_input = QSpinBox()
        self.poc_y_input.setRange(0, 10000)
        self.poc_y_input.setValue(100)

        init_layout.addRow("Filename:", self.file_name)
        
        width_layout = QFormLayout()
        width_layout.addRow("Width:", self.width_input)
        height_layout = QFormLayout()
        height_layout.addRow("Height:", self.height_input)
        width_height_layout = QHBoxLayout()
        width_height_layout.addLayout(width_layout)
        width_height_layout.addLayout(height_layout)

        initx_layout = QFormLayout()
        initx_layout.addRow("X0:", self.poc_x_input)
        inity_layout = QFormLayout()
        inity_layout.addRow("Y0:", self.poc_y_input)
        xyinit_layout = QHBoxLayout()
        xyinit_layout.addLayout(initx_layout)
        xyinit_layout.addLayout(inity_layout)

        init_layout.addRow(width_height_layout)
        init_layout.addRow(xyinit_layout)
        
        init_group.setLayout(init_layout)
        layout.addWidget(init_group)

        # Create builder button
        self.create_builder_btn = QPushButton("Create Builder")
        self.create_builder_btn.clicked.connect(self.create_builder)
        layout.addWidget(self.create_builder_btn)

        # Collision parameters
        self.collision_group = QGroupBox("Add Collision")
        collision_layout = QFormLayout()
        self.new_point_x = QSpinBox()
        self.new_point_x.setRange(0, 10000)
        self.new_point_y = QSpinBox()
        self.new_point_y.setRange(0, 10000)
        self.border_collision_input = QLineEdit()
        self.add_path_btn = QPushButton("Add Path")
        self.add_path_btn.clicked.connect(self.add_path)
        self.paths_list = QListWidget()

        collision_layout.addRow("New Point X:", self.new_point_x)
        collision_layout.addRow("New Point Y:", self.new_point_y)
        collision_layout.addRow("Border Collision:", self.border_collision_input)
        collision_layout.addRow(self.add_path_btn)
        collision_layout.addRow("Paths:", self.paths_list)
        self.collision_group.setLayout(collision_layout)
        layout.addWidget(self.collision_group)

        # Configuration parameters (collapsible)
        self.config_box = CollapsibleBox("Configuration (click to expand)")
        config_layout = QFormLayout()
        self.config_inputs = {}
        default_config = {
            'n_secondaries': (QSpinBox, (1, 100), 20),
            'alpha_std': (QDoubleSpinBox, (0, 360), 40),
            'length_mean': (QDoubleSpinBox, (0, 1000), 100),
            'length_std': (QDoubleSpinBox, (0, 1000), 20),
            'primary_color': (QPushButton, None, '#ffffff'),
            'secondary_color': (QPushButton, None, '#ff4444'),
            'box_color': (QPushButton, None, '#555555'),
            'background_color': (QPushButton, None, '#cc4444'),
            'primary_stroke_width': (QDoubleSpinBox, (0, 100), 3),
            'secondary_stroke_width': (QDoubleSpinBox, (0, 100), 3),
            'primary_begin': (QDoubleSpinBox, (0, 100), 0),
            'secondary_duration': (QDoubleSpinBox, (0, 100), 0.5),
            'primary_duration': (QDoubleSpinBox, (0, 100), 3),
            'dur_fade_primary': (QDoubleSpinBox, (0, 100), 0.25),
            'dur_fade_secondary': (QDoubleSpinBox, (0, 100), 0.25),
            'dur_freeze_secondary': (QDoubleSpinBox, (0, 100), 0.0)
        }

        for key, (widget_type, range_or_none, start_value) in default_config.items():
            if widget_type == QPushButton:
                self.config_inputs[key] = QPushButton("Select Color")
                self.config_inputs[key].setStyleSheet(f"background-color: {start_value};")
                self.config_inputs[key].clicked.connect(lambda _, k=key: self.choose_color(k))
            else:
                self.config_inputs[key] = widget_type()
                if range_or_none:
                    self.config_inputs[key].setRange(*range_or_none)
                    self.config_inputs[key].setValue(start_value)
            config_layout.addRow(key, self.config_inputs[key])

        self.config_box.setContentLayout(config_layout)
        layout.addWidget(self.config_box)

        # Add collision button
        self.add_collision_btn = QPushButton("Add Collision")
        self.add_collision_btn.clicked.connect(self.add_collision)
        layout.addWidget(self.add_collision_btn)

        # Generate SVG button
        self.generate_svg_btn = QPushButton("Generate SVG")
        self.generate_svg_btn.clicked.connect(self.generate_svg)
        layout.addWidget(self.generate_svg_btn)

        self.setLayout(layout)
        self.setWindowTitle('Consecutive Collision Builder GUI')
        
        # Set a regular size for the window
        self.resize(600, 800)

        # Disable all widgets after Create Builder button initially
        self.set_widgets_enabled(False)

        self.show()

    def set_widgets_enabled(self, enabled):
        self.collision_group.setEnabled(enabled)
        self.config_box.setEnabled(enabled)
        self.add_collision_btn.setEnabled(enabled)
        self.generate_svg_btn.setEnabled(enabled)

    def create_builder(self):
        width = self.width_input.value()
        height = self.height_input.value()
        poc = [self.poc_x_input.value(), self.poc_y_input.value()]
        self.ccb = ConsecutiveCollisionBuilder(width, height, poc)

        # Enable all widgets after Create Builder button is clicked
        self.set_widgets_enabled(True)
        
        # Disable the Create Builder button and initial parameters
        self.create_builder_btn.setEnabled(False)
        self.file_name.setEnabled(False)
        self.width_input.setEnabled(False)
        self.height_input.setEnabled(False)
        self.poc_x_input.setEnabled(False)
        self.poc_y_input.setEnabled(False)

    def add_path(self):
        path = self.border_collision_input.text().split(',')
        self.paths_list.addItem(','.join(path))
        self.border_collision_input.clear()

    def choose_color(self, key):
        color = QColorDialog.getColor()
        if color.isValid():
            self.config_inputs[key].setStyleSheet(f"background-color: {color.name()};")

    def add_collision(self):
        if not self.ccb:
            print("Please create a builder first")
            return

        new_point = [self.new_point_x.value(), self.new_point_y.value()]
        border_collisions = [item.text().split(',') for item in self.paths_list.findItems('*', Qt.MatchWildcard)]

        config = {}
        for key, widget in self.config_inputs.items():
            if isinstance(widget, QPushButton):
                config[key] = widget.styleSheet().split(': ')[-1][:-1]
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                config[key] = widget.value()

        self.ccb.addCollision(new_point, border_collisions, **config)
        print("Collision added")
        self.paths_list.clear()

    def generate_svg(self):
        if not self.ccb:
            print("Please create a builder first")
            return

        self.ccb.to_svg(self.file_name.text())
        print(f"SVG generated: {self.file_name.text()}")
        webbrowser.open(self.file_name.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CollisionGUI()
    sys.exit(app.exec_())