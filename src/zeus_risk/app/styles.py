"""Restrained application-wide Qt Widgets styling."""

APPLICATION_STYLESHEET = """
QWidget {
    color: #172033;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}
QMainWindow, QWidget#applicationRoot {
    background: #f4f6fa;
}
QMenuBar {
    background: #ffffff;
    color: #172033;
    border-bottom: 1px solid #e2e8f0;
}
QMenuBar::item {
    background: transparent;
    padding: 5px 9px;
}
QMenuBar::item:selected, QMenuBar::item:pressed {
    background: #e2e8f0;
    color: #0f172a;
}
QMenu {
    background: #ffffff;
    color: #172033;
    border: 1px solid #cbd5e1;
}
QMenu::item:selected {
    background: #ccfbf1;
    color: #134e4a;
}
QFrame#heroPanel {
    background: #111827;
    border-radius: 14px;
}
QLabel#brandMark {
    color: #fbbf24;
    font-size: 30px;
    font-weight: 800;
}
QLabel#heroTitle {
    color: white;
    font-size: 24px;
    font-weight: 700;
}
QLabel#heroSubtitle {
    color: #cbd5e1;
    font-size: 13px;
}
QLabel#pageTitle {
    color: #111827;
    font-size: 20px;
    font-weight: 700;
}
QLabel#pageSubtitle, QLabel#mutedLabel {
    color: #64748b;
}
QFrame#summaryCard, QFrame#metricCard {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}
QLabel#summaryTitle, QLabel#metricTitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
}
QLabel#summaryValue {
    color: #111827;
    font-size: 20px;
    font-weight: 700;
}
QLabel#metricValue {
    color: #0f766e;
    font-size: 27px;
    font-weight: 750;
}
QLabel#successBanner {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 7px;
    color: #047857;
    padding: 9px 12px;
}
QLabel#errorBanner {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 7px;
    color: #b91c1c;
    padding: 9px 12px;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    min-height: 34px;
    padding: 0 15px;
    font-weight: 600;
}
QPushButton:hover {
    border-color: #64748b;
    background: #f8fafc;
}
QPushButton#primaryButton {
    background: #0f766e;
    border-color: #0f766e;
    color: white;
}
QPushButton#primaryButton:hover {
    background: #115e59;
}
QPushButton#primaryButton:disabled {
    background: #94a3b8;
    border-color: #94a3b8;
}
QTabWidget::pane {
    border: 0;
}
QTabBar::tab {
    background: transparent;
    color: #64748b;
    font-weight: 650;
    padding: 10px 18px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    color: #0f766e;
    border-bottom: 3px solid #0f766e;
}
QGroupBox {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    font-weight: 700;
    margin-top: 12px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 13px;
    padding: 0 5px;
}
QTableView {
    background: white;
    alternate-background-color: #f8fafc;
    border: 0;
    gridline-color: #e2e8f0;
    selection-background-color: #ccfbf1;
    selection-color: #134e4a;
}
QHeaderView::section {
    background: #f8fafc;
    border: 0;
    border-bottom: 1px solid #e2e8f0;
    color: #475569;
    font-weight: 700;
    padding: 8px;
}
QDoubleSpinBox, QSpinBox {
    background: white;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    min-height: 32px;
    padding: 0 8px;
}
QStatusBar {
    background: white;
    border-top: 1px solid #e2e8f0;
    color: #475569;
}
"""
