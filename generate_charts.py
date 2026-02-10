#!/usr/bin/env python3
"""Generate professional charts for Visusta regulatory reports."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch
import os

# ── Visusta Brand Palette ──────────────────────────────────────────
PRIMARY_DARK = '#0D3B26'
PRIMARY = '#1A6B4B'
PRIMARY_LIGHT = '#2E8B63'
ACCENT_GREEN = '#4CAF50'
LIGHT_BG = '#E8F5E9'
WARM_GRAY = '#6B7B8D'
TEXT_DARK = '#1A1A2E'
WHITE = '#FFFFFF'
ALERT_RED = '#C62828'
ALERT_AMBER = '#F57F17'
SOFT_BLUE = '#1565C0'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'figure.facecolor': WHITE,
    'axes.facecolor': WHITE,
    'axes.edgecolor': '#D0D0D0',
    'grid.color': '#EBEBEB',
    'grid.linewidth': 0.6,
})

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_DIR = os.path.join(SCRIPT_DIR, 'charts')
os.makedirs(CHART_DIR, exist_ok=True)


# ════════════════════════════════════════════════════════════════════
# CHART 1: Hamburg Fee Increase Waterfall (Monthly Report)
# ════════════════════════════════════════════════════════════════════
def chart_hamburg_fees():
    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    categories = ['Wastewater\n(Schmutzwasser)', 'Rainwater\n(Niederschlags-\nwasser)', 'Waste Disposal\n(Müllabfuhr)', 'Admin Fees']
    increases = [3.3, 3.3, 3.4, 4.5]  # approx
    colors = [PRIMARY, PRIMARY_LIGHT, ACCENT_GREEN, WARM_GRAY]

    bars = ax.bar(categories, increases, width=0.55, color=colors, edgecolor=WHITE, linewidth=1.5, zorder=3)

    for bar, val in zip(bars, increases):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.12,
                f'+{val}%', ha='center', va='bottom', fontweight='bold',
                fontsize=11, color=TEXT_DARK)

    ax.set_ylabel('Fee Increase (%)', fontweight='bold')
    ax.set_title('Hamburg Municipal Fee Adjustments — Effective January 1, 2026',
                 fontweight='bold', pad=15, color=PRIMARY_DARK)
    ax.set_ylim(0, 5.8)
    ax.axhline(y=3.3, color=ALERT_AMBER, linestyle='--', alpha=0.5, linewidth=1, label='Average +3.3%')
    ax.legend(loc='upper right', frameon=True, framealpha=0.9, fontsize=9)
    ax.grid(axis='y', alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, 'hamburg_fees.png'), dpi=200, bbox_inches='tight')
    plt.close()


# ════════════════════════════════════════════════════════════════════
# CHART 2: VerpackDG Cost Impact Projection (Monthly Report)
# ════════════════════════════════════════════════════════════════════
def chart_verpackdg_cost():
    fig, ax = plt.subplots(figsize=(7.5, 4.0))

    tonnage = np.array([500, 1000, 2000, 5000, 10000])
    levy_cost = tonnage * 5  # €5/tonne
    service_est = tonnage * 3  # estimated OfH service fee
    total = levy_cost + service_est

    x = np.arange(len(tonnage))
    width = 0.3

    b1 = ax.bar(x - width/2, levy_cost/1000, width, label='ZSVR Levy (€5/t)', color=PRIMARY, zorder=3)
    b2 = ax.bar(x + width/2, service_est/1000, width, label='Est. OfH Service Fee (€3/t)', color=ACCENT_GREEN, zorder=3)

    for i, t in enumerate(total):
        ax.text(i, t/1000 + 0.3, f'€{t/1000:.0f}k', ha='center', fontsize=9, fontweight='bold', color=TEXT_DARK)

    ax.plot(x, total/1000, 'o--', color=ALERT_RED, markersize=6, linewidth=1.5, label='Total Est. Annual Cost', zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels([f'{t:,}t' for t in tonnage])
    ax.set_xlabel('Annual B2B Packaging Volume (tonnes)', fontweight='bold')
    ax.set_ylabel('Cost (€ thousands)', fontweight='bold')
    ax.set_title('VerpackDG: Estimated Annual EPR Cost Exposure by Volume',
                 fontweight='bold', pad=15, color=PRIMARY_DARK)
    ax.legend(loc='upper left', frameon=True, fontsize=9)
    ax.grid(axis='y', alpha=0.5, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, 'verpackdg_cost.png'), dpi=200, bbox_inches='tight')
    plt.close()


# ════════════════════════════════════════════════════════════════════
# CHART 3: PPWR Recyclability Grading Scale (Quarterly Report)
# ════════════════════════════════════════════════════════════════════
def chart_ppwr_grading():
    fig, ax = plt.subplots(figsize=(7.5, 3.5))

    grades = ['Grade A\n≥95%', 'Grade B\n≥90%', 'Grade C\n≥80%', 'Grade D\n≥70%', 'Grade E\n<70%']
    values = [95, 90, 80, 70, 50]
    colors_grad = ['#1B5E20', '#2E7D32', '#F9A825', '#E65100', '#B71C1C']

    bars = ax.barh(grades[::-1], values[::-1], height=0.55, color=colors_grad[::-1],
                   edgecolor=WHITE, linewidth=1.5, zorder=3)

    for bar, val, grade in zip(bars, values[::-1], grades[::-1]):
        label = 'BANNED from 2030' if val == 50 else f'{val}%+ recyclability'
        color = WHITE if val in [50, 70] else TEXT_DARK
        ax.text(bar.get_width() - 3, bar.get_y() + bar.get_height()/2,
                label, ha='right', va='center', fontsize=9, fontweight='bold', color=color)

    ax.set_xlabel('Recyclability Rate (%)', fontweight='bold')
    ax.set_title('PPWR Design for Recycling — Packaging Grading Scale (from 2030)',
                 fontweight='bold', pad=15, color=PRIMARY_DARK)
    ax.set_xlim(0, 105)
    ax.grid(axis='x', alpha=0.4, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, 'ppwr_grading.png'), dpi=200, bbox_inches='tight')
    plt.close()


# ════════════════════════════════════════════════════════════════════
# CHART 4: Regulatory Timeline Gantt (Quarterly Report)
# ════════════════════════════════════════════════════════════════════
def chart_regulatory_timeline():
    fig, ax = plt.subplots(figsize=(8.5, 5.0))

    regulations = [
        'Hamburg Fees (Effective)',
        'VerpackDG (Draft → Adoption)',
        'EWKFondsG FY2024 Report',
        'PPWR General Application',
        'FCM Reg 2022/1616 Deadline',
        'EmpCo Transposition',
        'EUDR Application',
        'CSRD Wave 2 Reporting',
    ]

    # Months: 1=Jan 2026, 12=Dec 2026
    starts = [1, 1, 1, 8, 7, 9, 12, 1]
    durations = [12, 6, 5, 5, 1, 4, 1, 12]
    colors_tl = [ACCENT_GREEN, ALERT_AMBER, PRIMARY_LIGHT, ALERT_RED, ALERT_RED,
                 ALERT_AMBER, ALERT_RED, WARM_GRAY]

    y_pos = np.arange(len(regulations))

    for i, (start, dur) in enumerate(zip(starts, durations)):
        ax.barh(i, dur, left=start, height=0.45, color=colors_tl[i],
                edgecolor=WHITE, linewidth=1, zorder=3, alpha=0.85)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(regulations, fontsize=9)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], fontsize=9)
    ax.set_xlabel('2026', fontweight='bold')
    ax.set_title('Regulatory Compliance Timeline — 2026 Calendar Year',
                 fontweight='bold', pad=15, color=PRIMARY_DARK)

    # Current month marker
    ax.axvline(x=2, color=PRIMARY_DARK, linewidth=2, linestyle='-', alpha=0.7, label='Current (Feb 2026)')
    ax.legend(loc='lower right', fontsize=9, frameon=True)

    ax.set_xlim(0.5, 13)
    ax.grid(axis='x', alpha=0.3, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.invert_yaxis()

    plt.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, 'regulatory_timeline.png'), dpi=200, bbox_inches='tight')
    plt.close()


# ════════════════════════════════════════════════════════════════════
# CHART 5: Recycled Content Targets Stacked (Quarterly Report)
# ════════════════════════════════════════════════════════════════════
def chart_recycled_targets():
    fig, ax = plt.subplots(figsize=(7.5, 4.0))

    categories = ['Contact-sensitive\n(PET)', 'Contact-sensitive\n(non-PET)', 'SUP Bottles', 'Other Plastic\nPackaging']
    targets_2030 = [30, 10, 30, 35]
    targets_2040 = [50, 25, 65, 65]
    increments_2040 = [t40 - t30 for t30, t40 in zip(targets_2030, targets_2040)]

    x = np.arange(len(categories))
    width = 0.45

    ax.bar(x, targets_2030, width, label='By 2030', color=PRIMARY, edgecolor=WHITE, linewidth=1, zorder=3)
    ax.bar(x, increments_2040, width, bottom=targets_2030, label='Additional by 2040',
           color=ACCENT_GREEN, alpha=0.7, edgecolor=WHITE, linewidth=1, zorder=3)

    for i, (v30, v40) in enumerate(zip(targets_2030, targets_2040)):
        ax.text(i, v30/2, f'{v30}%', ha='center', va='center', fontsize=10,
                fontweight='bold', color=WHITE)
        ax.text(i, v40 + 1.5, f'{v40}%', ha='center', va='bottom', fontsize=10,
                fontweight='bold', color=TEXT_DARK)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_ylabel('Minimum Recycled Content (%)', fontweight='bold')
    ax.set_title('PPWR Mandatory Recycled Content Targets for Plastic Packaging',
                 fontweight='bold', pad=15, color=PRIMARY_DARK)
    ax.set_ylim(0, 78)
    ax.legend(loc='upper left', frameon=True, fontsize=9)
    ax.grid(axis='y', alpha=0.4, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, 'recycled_targets.png'), dpi=200, bbox_inches='tight')
    plt.close()


# ════════════════════════════════════════════════════════════════════
# CHART 6: EWKFondsG Levy Comparison (Monthly Report)
# ════════════════════════════════════════════════════════════════════
def chart_ewk_levies():
    fig, ax = plt.subplots(figsize=(7.0, 3.8))

    items = ['To-go Food\nContainers', 'Flexible Wrappers\n(Immediate Consumption)', 'Beverage\nCups']
    levies = [0.177, 0.871, 1.236]
    colors_l = [PRIMARY_LIGHT, ACCENT_GREEN, ALERT_AMBER]

    bars = ax.barh(items, levies, height=0.5, color=colors_l, edgecolor=WHITE, linewidth=1.5, zorder=3)

    for bar, val in zip(bars, levies):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                f'€{val:.3f}/kg', ha='left', va='center', fontsize=11, fontweight='bold', color=TEXT_DARK)

    ax.set_xlabel('Levy Rate (€ per kg)', fontweight='bold')
    ax.set_title('EWKFondsG Single-Use Plastic Levy Rates — Germany',
                 fontweight='bold', pad=15, color=PRIMARY_DARK)
    ax.set_xlim(0, 1.55)
    ax.grid(axis='x', alpha=0.4, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, 'ewk_levies.png'), dpi=200, bbox_inches='tight')
    plt.close()


# ════════════════════════════════════════════════════════════════════
# Generate all charts
# ════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    chart_hamburg_fees()
    chart_verpackdg_cost()
    chart_ppwr_grading()
    chart_regulatory_timeline()
    chart_recycled_targets()
    chart_ewk_levies()
    print(f"✓ All 6 charts generated in {CHART_DIR}/")
    for f in sorted(os.listdir(CHART_DIR)):
        sz = os.path.getsize(os.path.join(CHART_DIR, f))
        print(f"  {f} ({sz/1024:.0f} KB)")
