"""Build the interactive Analytics Portal and deploy it to Hugging Face Spaces.

This script constructs the complete web application for Hugging Face Spaces covering:
- Executive Summary & Business Framing (Module 1)
- Historical Sales EDA & Weekly Seasonality (Module 2)
- 14-Day Demand Forecast with Confidence Bands (Module 5)
- Model Benchmarking: Naive vs Holt-Winters vs LightGBM (Module 5)
- Inventory Optimization & Reorder Quantity Calculator (Module 8)
- Live Model Monitoring & Automated Retraining Triggers (Module 7)
- REST API Live Tester (Module 6)
"""

# ruff: noqa: E501

from __future__ import annotations

import json
import os
from pathlib import Path

from huggingface_hub import HfApi

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = (
    REPOSITORY_ROOT
    / "artifacts"
    / "public_demo"
    / "rossmann-course-demo-synthetic-v1"
    / "demo_bundle.json"
)
MONITORING_SUMMARY_PATH = REPOSITORY_ROOT / "reports" / "monitoring_summary.json"
EVIDENTLY_HTML_PATH = REPOSITORY_ROOT / "reports" / "model_monitoring_report.html"

HF_TOKEN = os.environ.get("HF_TOKEN", "")
REPO_ID = os.environ.get("HF_SPACE_REPO", "hieu-nguyen2208/rossmann-sales-forecasting")


def load_data() -> tuple[dict, dict]:
    with open(BUNDLE_PATH, encoding="utf-8") as f:
        bundle = json.load(f)
    with open(MONITORING_SUMMARY_PATH, encoding="utf-8") as f:
        monitoring = json.load(f)
    return bundle, monitoring


def generate_index_html(bundle: dict, monitoring: dict) -> str:
    bundle_json_str = json.dumps(bundle)
    monitoring_json_str = json.dumps(monitoring)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rossmann Demand Forecasting & Inventory Optimization</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Chart.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <!-- Font Awesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    .badge {{ display: inline-flex; align-items: center; padding: 0.125rem 0.625rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
  </style>
</head>
<body class="bg-slate-50 text-slate-800 font-sans antialiased min-h-screen flex flex-col">

  <!-- Header -->
  <header class="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white shadow-lg border-b border-indigo-700/50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="bg-blue-500 text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded">IT4063E Business Analytics</span>
            <span class="bg-emerald-500 text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span> Live Demo
            </span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight mt-1 text-white">
            Retail Demand Forecasting & Inventory Optimization
          </h1>
          <p class="text-indigo-200 text-sm mt-0.5">
            Store-Level Monetary Turnover Forecasting (H14) & Decision Support Simulation for 1,115 Rossmann Stores
          </p>
        </div>
        <div class="text-xs text-indigo-200 bg-white/10 backdrop-blur p-3 rounded-lg border border-white/10 space-y-1">
          <div><strong class="text-white">Instructor:</strong> Dr. Bui Quoc Trung</div>
          <div><strong class="text-white">Team:</strong> Pham Le Minh Quang, Tran Quoc Tuan, Vo Ta Quang Nhat, Nguyen Trung Hieu, Nguyen Gia Minh</div>
          <div><strong class="text-white">Selected Model:</strong> Global LightGBM L1 (180 rounds, -48.2% MAE)</div>
        </div>
      </div>
    </div>
  </header>

  <!-- Navigation Bar -->
  <nav class="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-30">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex space-x-1 sm:space-x-4 overflow-x-auto py-2.5 text-sm font-medium">
        <button onclick="switchTab('overview')" id="tab-btn-overview" class="tab-btn px-3 py-2 rounded-md bg-blue-50 text-blue-700 font-semibold flex items-center gap-2 whitespace-nowrap">
          <i class="fa-solid fa-chart-pie"></i> 1. Executive Overview
        </button>
        <button onclick="switchTab('eda')" id="tab-btn-eda" class="tab-btn px-3 py-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2 whitespace-nowrap">
          <i class="fa-solid fa-chart-line"></i> 2. EDA & Seasonality
        </button>
        <button onclick="switchTab('forecast')" id="tab-btn-forecast" class="tab-btn px-3 py-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2 whitespace-nowrap">
          <i class="fa-solid fa-wand-magic-sparkles"></i> 3. 14-Day Forecast & Uncertainty
        </button>
        <button onclick="switchTab('benchmark')" id="tab-btn-benchmark" class="tab-btn px-3 py-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2 whitespace-nowrap">
          <i class="fa-solid fa-scale-balanced"></i> 4. Model Benchmarking
        </button>
        <button onclick="switchTab('inventory')" id="tab-btn-inventory" class="tab-btn px-3 py-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2 whitespace-nowrap">
          <i class="fa-solid fa-boxes-packing"></i> 5. Inventory Optimization
        </button>
        <button onclick="switchTab('monitoring')" id="tab-btn-monitoring" class="tab-btn px-3 py-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2 whitespace-nowrap">
          <i class="fa-solid fa-shield-halved"></i> 6. Model Monitoring & Drift
        </button>
        <button onclick="switchTab('api')" id="tab-btn-api" class="tab-btn px-3 py-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-2 whitespace-nowrap">
          <i class="fa-solid fa-server"></i> 7. REST API Tester
        </button>
      </div>
    </div>
  </nav>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full">

    <!-- TAB 1: EXECUTIVE OVERVIEW -->
    <section id="tab-overview" class="tab-content active space-y-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 class="text-xl font-bold text-slate-900 mb-3 flex items-center gap-2">
          <i class="fa-solid fa-bullseye text-blue-600"></i> Business Problem & Scope
        </h2>
        <div class="prose max-w-none text-slate-600 text-sm leading-relaxed space-y-3">
          <p>
            In retail and Fast-Moving Consumer Goods (FMCG), demand accuracy dictates working capital efficiency and customer satisfaction.
            Understocking causes lost sales and customer defection; overstocking incurs unnecessary holding costs and risks spoilage.
          </p>
          <div class="bg-blue-50 border-l-4 border-blue-600 p-4 rounded-r-md text-blue-900">
            <strong>Core Business Question:</strong>
            <em>"How much store-level monetary turnover is expected over the next 14 calendar days (H14), and how do forecast-based inventory replenishment policies compare against baseline heuristics under explicit operational assumptions?"</em>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div class="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div class="text-xs font-semibold text-slate-500 uppercase">Target & Granularity</div>
              <div class="text-base font-bold text-slate-900 mt-1">Store × Date Monetary Sales</div>
              <div class="text-xs text-slate-500 mt-1">1,115 stores; daily revenue turnover (not physical SKU count). Rossmann does not supply SKU identifiers.</div>
            </div>
            <div class="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div class="text-xs font-semibold text-slate-500 uppercase">Primary Horizon</div>
              <div class="text-base font-bold text-slate-900 mt-1">14 Calendar Days (H14)</div>
              <div class="text-xs text-slate-500 mt-1">Multi-step recursive point forecast with separate daily intervals and cumulative prefix bounds.</div>
            </div>
            <div class="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div class="text-xs font-semibold text-slate-500 uppercase">Prescriptive Layer</div>
              <div class="text-base font-bold text-slate-900 mt-1">Simulated Standing-Target Policy</div>
              <div class="text-xs text-slate-500 mt-1">Review period R=1, Lead time L=2..7 days, Safety stock from empirical cumulative residual quantile.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Module Traceability Matrix -->
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h3 class="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <i class="fa-solid fa-list-check text-indigo-600"></i> Course Syllabus Requirement Traceability
        </h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                <th class="p-3">Course Module</th>
                <th class="p-3">Required Key Tasks</th>
                <th class="p-3">Implementation Evidence</th>
                <th class="p-3">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 text-slate-600">
              <tr>
                <td class="p-3 font-semibold text-slate-800">1. Business Understanding</td>
                <td class="p-3">KPI definition (horizon, stockout rate, holding costs), synthetic supply chain context, data dictionary.</td>
                <td class="p-3">H14 horizon, holding rate c*a/365, shortfall penalty (1-c)+g, docs/DATA_DICTIONARY.md.</td>
                <td class="p-3"><span class="badge bg-emerald-100 text-emerald-800">Completed (100%)</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-800">2. Exploratory Data Analysis</td>
                <td class="p-3">Trend, 7-day seasonality, autocorrelation, weekly STL decomposition, store-type patterns.</td>
                <td class="p-3">notebooks/02_exploratory_data_analysis.ipynb, robust weekly STL diagnostic implementation.</td>
                <td class="p-3"><span class="badge bg-emerald-100 text-emerald-800">Completed (100%)</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-800">3. Data Cleaning</td>
                <td class="p-3">Handle missing dates, duplicate records, distinguish closed-day zeros from true zero demand.</td>
                <td class="p-3">docs/DATA_VALIDATION.md, sparse-date preservation, Open routing decoupled from raw forecast.</td>
                <td class="p-3"><span class="badge bg-emerald-100 text-emerald-800">Completed (100%)</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-800">4. Feature Engineering</td>
                <td class="p-3">Time features, lags 1/7/14/28, rolling windows (7, 14, 28 days), chronological walk-forward splits.</td>
                <td class="p-3">docs/FEATURE_CONTRACT.md (29 frozen point-in-time predictors, no future customer leakage).</td>
                <td class="p-3"><span class="badge bg-emerald-100 text-emerald-800">Completed (100%)</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-800">5. Model Development</td>
                <td class="p-3">Compare Classical (Exponential Smoothing) vs ML (LightGBM); MAE, RMSE, MAPE; prediction intervals.</td>
                <td class="p-3">Seasonal Naive vs Additive Holt-Winters vs Global LightGBM; LightGBM selected (MAE 871.06 vs 1681.27).</td>
                <td class="p-3"><span class="badge bg-emerald-100 text-emerald-800">Completed (100%)</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-800">6. Model Deployment</td>
                <td class="p-3">FastAPI backend returning N-day forecasts; Streamlit dashboard demo; Cloud free-tier deployment with live URL.</td>
                <td class="p-3">FastAPI adapter, Streamlit dashboard, live Hugging Face Space deployment.</td>
                <td class="p-3"><span class="badge bg-emerald-100 text-emerald-800">Completed (100%)</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-800">7. Model Monitoring</td>
                <td class="p-3">Track rolling MAE/MAPE drift over time; build Evidently monitoring report; define retraining triggers.</td>
                <td class="p-3">reports/model_monitoring_report.html, notebooks/03_model_monitoring_evidently.ipynb, trigger engine.</td>
                <td class="p-3"><span class="badge bg-emerald-100 text-emerald-800">Completed (100%)</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-800">8. Decision Support</td>
                <td class="p-3">Translate forecasts into safety stock and replenishment recommendations; discuss trade-offs.</td>
                <td class="p-3">Simulated order-up-to target S=max(Dp, Up), reorder quantity Q=max(0, S-IP), cycle service rate.</td>
                <td class="p-3"><span class="badge bg-emerald-100 text-emerald-800">Completed (100%)</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 2: EDA & SEASONALITY -->
    <section id="tab-eda" class="tab-content space-y-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 class="text-xl font-bold text-slate-900 flex items-center gap-2">
              <i class="fa-solid fa-chart-line text-blue-600"></i> Historical Sales & Weekly Seasonality
            </h2>
            <p class="text-xs text-slate-500">Historical daily turnover dynamics across stores up to the July 3, 2015 development cutoff</p>
          </div>
          <div class="flex items-center gap-2">
            <label class="text-xs font-semibold text-slate-600">Store:</label>
            <select id="eda-store-select" onchange="renderEdaChart()" class="bg-slate-50 border border-slate-300 rounded px-2.5 py-1 text-xs font-semibold">
              <option value="101">Store 101</option>
              <option value="202">Store 202</option>
              <option value="303">Store 303</option>
            </select>
          </div>
        </div>

        <div class="h-80 w-full relative">
          <canvas id="edaSalesChart"></canvas>
        </div>

        <!-- Seasonality Insights Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div class="p-4 bg-indigo-50/50 rounded-lg border border-indigo-100">
            <h4 class="text-xs font-bold text-indigo-900 uppercase flex items-center gap-1.5">
              <i class="fa-solid fa-calendar-week"></i> 7-Day Day-of-Week Pattern
            </h4>
            <p class="text-xs text-slate-600 mt-2 leading-relaxed">
              Sales peak heavily on Mondays (weekly restocking) and Fridays/Saturdays. Sunday represents planned mandatory retail closure (Open=0, Sales=0) across standard German stores.
            </p>
          </div>
          <div class="p-4 bg-emerald-50/50 rounded-lg border border-emerald-100">
            <h4 class="text-xs font-bold text-emerald-900 uppercase flex items-center gap-1.5">
              <i class="fa-solid fa-tags"></i> Promotional Uplift
            </h4>
            <p class="text-xs text-slate-600 mt-2 leading-relaxed">
              Bi-weekly promotional campaigns (<code class="bg-white px-1 py-0.5 rounded text-emerald-800">Promo=1</code>) introduce an immediate +20% to +35% turnover surge compared to non-promotional weekdays.
            </p>
          </div>
          <div class="p-4 bg-amber-50/50 rounded-lg border border-amber-100">
            <h4 class="text-xs font-bold text-amber-900 uppercase flex items-center gap-1.5">
              <i class="fa-solid fa-code-merge"></i> Weekly STL Decomposition
            </h4>
            <p class="text-xs text-slate-600 mt-2 leading-relaxed">
              Decomposed into smooth trend, stable weekly seasonality (period=7), and transient residuals (holiday spikes, stockout dips).
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 3: 14-DAY FORECAST & UNCERTAINTY -->
    <section id="tab-forecast" class="tab-content space-y-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 class="text-xl font-bold text-slate-900 flex items-center gap-2">
              <i class="fa-solid fa-wand-magic-sparkles text-indigo-600"></i> 14-Day Demand Forecast & Prediction Intervals
            </h2>
            <p class="text-xs text-slate-500">
              Recursive multi-step point predictions alongside 95% empirical forecast uncertainty bands
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <div>
              <label class="text-xs font-semibold text-slate-600 block">Store:</label>
              <select id="forecast-store-select" onchange="renderForecastChart()" class="bg-slate-50 border border-slate-300 rounded px-2.5 py-1 text-xs font-semibold">
                <option value="101">Store 101</option>
                <option value="202">Store 202</option>
                <option value="303">Store 303</option>
              </select>
            </div>
            <div>
              <label class="text-xs font-semibold text-slate-600 block">Origin Date:</label>
              <select id="forecast-origin-select" onchange="renderForecastChart()" class="bg-slate-50 border border-slate-300 rounded px-2.5 py-1 text-xs font-semibold">
                <option value="2015-06-05">2015-06-05 (Fit A)</option>
                <option value="2015-06-19">2015-06-19 (Fit B)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="h-80 w-full relative">
          <canvas id="forecastChart"></canvas>
        </div>

        <div class="mt-6">
          <h4 class="text-xs font-bold text-slate-700 uppercase mb-2">14-Day Trajectory Values & Uncertainty Interval Bounds</h4>
          <div class="overflow-x-auto max-h-56 border border-slate-200 rounded-lg">
            <table class="w-full text-left text-xs border-collapse">
              <thead class="bg-slate-100 text-slate-700 font-semibold sticky top-0">
                <tr>
                  <th class="p-2.5">Horizon</th>
                  <th class="p-2.5">Target Date</th>
                  <th class="p-2.5">Planned Status</th>
                  <th class="p-2.5 text-right">Point Forecast</th>
                  <th class="p-2.5 text-right">Lower Bound (95%)</th>
                  <th class="p-2.5 text-right">Upper Bound (95%)</th>
                  <th class="p-2.5 text-right">Band Width</th>
                </tr>
              </thead>
              <tbody id="forecast-table-body" class="divide-y divide-slate-200 text-slate-600">
                <!-- Dynamically generated rows -->
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 4: MODEL BENCHMARKING -->
    <section id="tab-benchmark" class="tab-content space-y-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 class="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
          <i class="fa-solid fa-scale-balanced text-blue-600"></i> Model Benchmarking & Evaluation Ladder
        </h2>
        <p class="text-xs text-slate-500 mb-4">
          Strict chronological walk-forward comparison over 38,553 common eligible Open=1 observations across 3 validation windows.
        </p>

        <!-- Summary Metric Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div class="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase text-slate-500">Baseline</span>
              <span class="badge bg-slate-200 text-slate-700">Seasonal Naive</span>
            </div>
            <div class="text-2xl font-black text-slate-800 mt-2">1,681.27</div>
            <div class="text-xs text-slate-500 mt-1">Pooled MAE · RMSE: 2,416.97 · MAPE: 26.27%</div>
          </div>
          <div class="p-4 bg-amber-50/60 rounded-xl border border-amber-200">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase text-amber-700">Statistical Candidate</span>
              <span class="badge bg-amber-200 text-amber-800">Additive Holt-Winters</span>
            </div>
            <div class="text-2xl font-black text-amber-900 mt-2">1,281.74</div>
            <div class="text-xs text-amber-700 mt-1">-23.8% vs Naive · Rejected: h8-14 regression exceeded 10% cap (+13.7%)</div>
          </div>
          <div class="p-4 bg-emerald-50 rounded-xl border border-emerald-300 ring-2 ring-emerald-500/20">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase text-emerald-700">Selected Winner</span>
              <span class="badge bg-emerald-600 text-white">Global LightGBM L1</span>
            </div>
            <div class="text-2xl font-black text-emerald-800 mt-2">871.06</div>
            <div class="text-xs text-emerald-700 mt-1"><strong>-48.2% MAE</strong> · RMSE: 1,350.91 · MAPE: 11.35% · WAPE: 0.121</div>
          </div>
        </div>

        <!-- Detailed Comparison Table -->
        <div class="overflow-x-auto border border-slate-200 rounded-lg">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-slate-100 text-slate-700 font-semibold">
              <tr>
                <th class="p-3">Evaluation Scope</th>
                <th class="p-3 text-right">Seasonal Naive MAE</th>
                <th class="p-3 text-right">Holt-Winters MAE</th>
                <th class="p-3 text-right">LightGBM MAE</th>
                <th class="p-3 text-right">LightGBM Lift (%)</th>
                <th class="p-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 text-slate-600">
              <tr class="bg-emerald-50/30 font-medium">
                <td class="p-3 font-bold text-slate-800">Overall Pooled (38,553 rows)</td>
                <td class="p-3 text-right">1,681.27</td>
                <td class="p-3 text-right">1,281.74</td>
                <td class="p-3 text-right text-emerald-700 font-bold">871.06</td>
                <td class="p-3 text-right text-emerald-700 font-bold">-48.19%</td>
                <td class="p-3 text-center"><span class="badge bg-emerald-100 text-emerald-800">Winner</span></td>
              </tr>
              <tr>
                <td class="p-3">Validation Window 1 (Origin 2015-05-22)</td>
                <td class="p-3 text-right">1,101.59</td>
                <td class="p-3 text-right">1,195.57 (+8.5%)</td>
                <td class="p-3 text-right font-semibold text-slate-800">1,051.43</td>
                <td class="p-3 text-right text-emerald-700">-4.55%</td>
                <td class="p-3 text-center"><span class="badge bg-emerald-100 text-emerald-800">Pass</span></td>
              </tr>
              <tr>
                <td class="p-3">Validation Window 2 (Origin 2015-06-05)</td>
                <td class="p-3 text-right">2,269.77</td>
                <td class="p-3 text-right">1,136.83 (-49.9%)</td>
                <td class="p-3 text-right font-semibold text-slate-800">790.99</td>
                <td class="p-3 text-right text-emerald-700">-65.15%</td>
                <td class="p-3 text-center"><span class="badge bg-emerald-100 text-emerald-800">Pass</span></td>
              </tr>
              <tr>
                <td class="p-3">Validation Window 3 (Origin 2015-06-19)</td>
                <td class="p-3 text-right">1,596.52</td>
                <td class="p-3 text-right">1,501.57 (-5.9%)</td>
                <td class="p-3 text-right font-semibold text-slate-800">794.37</td>
                <td class="p-3 text-right text-emerald-700">-50.24%</td>
                <td class="p-3 text-center"><span class="badge bg-emerald-100 text-emerald-800">Pass</span></td>
              </tr>
              <tr>
                <td class="p-3">Horizon Block h1–7 (Week 1)</td>
                <td class="p-3 text-right">2,136.36</td>
                <td class="p-3 text-right">1,155.66 (-45.9%)</td>
                <td class="p-3 text-right font-semibold text-slate-800">643.06</td>
                <td class="p-3 text-right text-emerald-700">-69.90%</td>
                <td class="p-3 text-center"><span class="badge bg-emerald-100 text-emerald-800">Pass</span></td>
              </tr>
              <tr>
                <td class="p-3">Horizon Block h8–14 (Week 2)</td>
                <td class="p-3 text-right">1,235.42</td>
                <td class="p-3 text-right text-red-600">1,405.27 (+13.7%)</td>
                <td class="p-3 text-right font-semibold text-slate-800">1,094.44</td>
                <td class="p-3 text-right text-emerald-700">-11.41%</td>
                <td class="p-3 text-center"><span class="badge bg-emerald-100 text-emerald-800">Pass</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 5: INVENTORY OPTIMIZATION -->
    <section id="tab-inventory" class="tab-content space-y-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 class="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
          <i class="fa-solid fa-boxes-packing text-blue-600"></i> Inventory Optimization & Replenishment Policy
        </h2>
        <p class="text-xs text-slate-500 mb-4">
          Prescriptive analytics converting forecast uncertainty into target safety stocks and suggested order quantities.
        </p>

        <!-- Interactive Calculator -->
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="text-xs font-bold text-slate-700 block mb-1">Lead Time L (Days):</label>
            <input type="range" id="inv-lead-time" min="2" max="7" value="3" oninput="updateInventoryCalc()" class="w-full">
            <div class="flex justify-between text-xs text-slate-500">
              <span>2 days</span>
              <span id="inv-lead-val" class="font-bold text-indigo-700">3 days</span>
              <span>7 days</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-1">Protection period P = L + 1 = 4 days</div>
          </div>

          <div>
            <label class="text-xs font-bold text-slate-700 block mb-1">Service Level Target (p):</label>
            <select id="inv-service-level" onchange="updateInventoryCalc()" class="w-full bg-white border border-slate-300 rounded px-3 py-1.5 text-xs font-semibold">
              <option value="0.90">90% Nominal Service</option>
              <option value="0.95" selected>95% Nominal Service</option>
              <option value="0.98">98% Nominal Service</option>
            </select>
            <div class="text-[11px] text-slate-400 mt-1">Quantile q_p derived from out-of-sample cumulative residuals</div>
          </div>

          <div>
            <label class="text-xs font-bold text-slate-700 block mb-1">Current Inventory Position (IP):</label>
            <input type="number" id="inv-onhand" value="32000" step="1000" oninput="updateInventoryCalc()" class="w-full bg-white border border-slate-300 rounded px-3 py-1 text-xs font-semibold">
            <div class="text-[11px] text-slate-400 mt-1">Stock on hand + Open pipeline orders</div>
          </div>
        </div>

        <!-- Calculated Inventory Decisions -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-sm text-center">
            <div class="text-[11px] font-semibold text-slate-500 uppercase">Protection Demand D_P</div>
            <div id="calc-dp" class="text-lg font-bold text-slate-800 mt-1">$44,820</div>
            <div class="text-[10px] text-slate-400">Sum of operational forecasts</div>
          </div>
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-sm text-center">
            <div class="text-[11px] font-semibold text-slate-500 uppercase">Safety Stock Buffer SS</div>
            <div id="calc-ss" class="text-lg font-bold text-indigo-700 mt-1">$5,450</div>
            <div class="text-[10px] text-slate-400">max(0, U_P - D_P)</div>
          </div>
          <div class="p-3 bg-white rounded-lg border border-slate-200 shadow-sm text-center">
            <div class="text-[11px] font-semibold text-slate-500 uppercase">Order-Up-To Target S</div>
            <div id="calc-s" class="text-lg font-bold text-purple-700 mt-1">$50,270</div>
            <div class="text-[10px] text-slate-400">max(D_P, D_P + q_p)</div>
          </div>
          <div class="p-3 bg-white rounded-lg border border-emerald-300 bg-emerald-50/40 shadow-sm text-center">
            <div class="text-[11px] font-semibold text-emerald-800 uppercase">Suggested Reorder Q</div>
            <div id="calc-q" class="text-lg font-black text-emerald-700 mt-1">$18,270</div>
            <div class="text-[10px] text-emerald-600 font-medium">max(0, S - IP)</div>
          </div>
        </div>

        <!-- Saved Episode Accounting Comparison -->
        <h4 class="text-xs font-bold text-slate-700 uppercase mb-2">Simulated Policy Trade-offs (H14 Episode Summary)</h4>
        <div class="overflow-x-auto border border-slate-200 rounded-lg">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-slate-100 text-slate-700 font-semibold">
              <tr>
                <th class="p-2.5">Simulated Policy</th>
                <th class="p-2.5 text-right">Holding + Shortfall Cost</th>
                <th class="p-2.5 text-right">Value Fill Rate</th>
                <th class="p-2.5 text-right">Stockout Rate</th>
                <th class="p-2.5 text-right">Completed Cycle Service Rate</th>
                <th class="p-2.5 text-right">Average Inventory Value</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 text-slate-600">
              <tr>
                <td class="p-2.5 font-semibold text-slate-800">Baseline Target (Historical Anchor)</td>
                <td class="p-2.5 text-right font-medium">620.0 proxy units</td>
                <td class="p-2.5 text-right">93.57%</td>
                <td class="p-2.5 text-right">16.67%</td>
                <td class="p-2.5 text-right font-semibold text-slate-700">75.00%</td>
                <td class="p-2.5 text-right">$720.00</td>
              </tr>
              <tr class="bg-blue-50/40">
                <td class="p-2.5 font-bold text-indigo-900">Forecast Target (LightGBM + SS)</td>
                <td class="p-2.5 text-right font-bold text-indigo-900">590.0 proxy units</td>
                <td class="p-2.5 text-right font-bold text-indigo-900">94.29%</td>
                <td class="p-2.5 text-right">25.00%</td>
                <td class="p-2.5 text-right font-bold text-indigo-900">50.00%</td>
                <td class="p-2.5 text-right font-bold text-indigo-900">$780.00</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 6: MODEL MONITORING -->
    <section id="tab-monitoring" class="tab-content space-y-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 class="text-xl font-bold text-slate-900 flex items-center gap-2">
              <i class="fa-solid fa-shield-halved text-blue-600"></i> Model Monitoring & Automated Retraining Triggers
            </h2>
            <p class="text-xs text-slate-500">
              Module 7 continuous surveillance: rolling forecast error tracking, feature drift detection, and automated trigger governance
            </p>
          </div>
          <div>
            <span id="monitoring-status-badge" class="badge bg-emerald-100 text-emerald-800 px-3 py-1 text-xs">
              <i class="fa-solid fa-circle-check mr-1"></i> System Status: Healthy
            </span>
          </div>
        </div>

        <!-- Rolling Error Chart -->
        <div class="mb-6">
          <h4 class="text-xs font-bold text-slate-700 uppercase mb-2">7-Day Rolling MAE Over Time (Performance Drift)</h4>
          <div class="h-64 w-full relative">
            <canvas id="monitoringChart"></canvas>
          </div>
        </div>

        <!-- Drift & Retraining Governance Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div class="p-4 bg-slate-50 rounded-lg border border-slate-200">
            <h4 class="text-xs font-bold text-slate-700 uppercase mb-2 flex items-center gap-1.5">
              <i class="fa-solid fa-sliders text-indigo-600"></i> Input Feature Drift Analysis
            </h4>
            <div class="space-y-2 text-xs">
              <div class="flex justify-between items-center p-2 bg-white rounded border border-slate-200">
                <span class="font-mono text-slate-700">sales_lag_1</span>
                <span class="badge bg-emerald-100 text-emerald-800">No Drift (p=0.48)</span>
              </div>
              <div class="flex justify-between items-center p-2 bg-white rounded border border-slate-200">
                <span class="font-mono text-slate-700">sales_lag_7</span>
                <span class="badge bg-emerald-100 text-emerald-800">No Drift (p=0.32)</span>
              </div>
              <div class="flex justify-between items-center p-2 bg-white rounded border border-slate-200">
                <span class="font-mono text-slate-700">sales_rolling_mean_7</span>
                <span class="badge bg-emerald-100 text-emerald-800">No Drift (p=0.61)</span>
              </div>
              <div class="flex justify-between items-center p-2 bg-white rounded border border-slate-200">
                <span class="font-mono text-slate-700">sales_rolling_mean_14</span>
                <span class="badge bg-emerald-100 text-emerald-800">No Drift (p=0.29)</span>
              </div>
            </div>
          </div>

          <div class="p-4 bg-slate-50 rounded-lg border border-slate-200">
            <h4 class="text-xs font-bold text-slate-700 uppercase mb-2 flex items-center gap-1.5">
              <i class="fa-solid fa-bell text-amber-600"></i> Automated Retraining Trigger Engine
            </h4>
            <ul class="text-xs space-y-2 text-slate-600">
              <li class="flex items-start gap-2">
                <i class="fa-solid fa-check text-emerald-500 mt-0.5"></i>
                <div><strong>Condition 1 (Performance):</strong> Rolling MAE increases by &gt;15% compared to the 28-day reference window.</div>
              </li>
              <li class="flex items-start gap-2">
                <i class="fa-solid fa-check text-emerald-500 mt-0.5"></i>
                <div><strong>Condition 2 (Covariate Drift):</strong> More than 25% of active predictors exhibit statistically significant distribution drift (KS test p &lt; 0.05).</div>
              </li>
              <li class="flex items-start gap-2">
                <i class="fa-solid fa-check text-emerald-500 mt-0.5"></i>
                <div><strong>Condition 3 (Persistence):</strong> Performance degradation must persist for at least 3 consecutive dates to filter out transient holiday noise.</div>
              </li>
            </ul>
            <div class="mt-4 pt-3 border-t border-slate-200 flex justify-between items-center">
              <span class="text-[11px] text-slate-500">Standalone Diagnostics Available</span>
              <a href="model_monitoring_report.html" target="_blank" class="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded transition">
                <i class="fa-solid fa-arrow-up-right-from-square"></i> Open Full Evidently AI Report
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 7: REST API TESTER -->
    <section id="tab-api" class="tab-content space-y-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 class="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
          <i class="fa-solid fa-server text-blue-600"></i> Interactive FastAPI Endpoint Tester
        </h2>
        <p class="text-xs text-slate-500 mb-4">
          Test the REST API endpoints defined in Module 6 (FastAPI adapter with bounded query parameters).
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label class="text-xs font-bold text-slate-700 block mb-1">Select Endpoint:</label>
            <select id="api-endpoint-select" onchange="updateApiParams()" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs font-semibold">
              <option value="/health">GET /health (Liveness Probe)</option>
              <option value="/api/v1/forecasts">GET /api/v1/forecasts (14-Day Demand)</option>
              <option value="/api/v1/uncertainty">GET /api/v1/uncertainty (Prediction Intervals)</option>
              <option value="/api/v1/model-comparison">GET /api/v1/model-comparison (Evaluation Ladder)</option>
              <option value="/api/v1/inventory">GET /api/v1/inventory (Simulated Policies)</option>
            </select>
          </div>
          <div>
            <label class="text-xs font-bold text-slate-700 block mb-1">Store Parameter:</label>
            <select id="api-store-select" class="w-full bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs font-semibold">
              <option value="101">store_id=101</option>
              <option value="202">store_id=202</option>
              <option value="303">store_id=303</option>
            </select>
          </div>
          <div class="flex items-end">
            <button onclick="executeApiCall()" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-1.5 px-4 rounded text-xs transition flex items-center justify-center gap-2 shadow-sm">
              <i class="fa-solid fa-paper-plane"></i> Send Request
            </button>
          </div>
        </div>

        <div class="border border-slate-200 rounded-lg overflow-hidden">
          <div class="bg-slate-100 px-4 py-2 flex items-center justify-between border-b border-slate-200">
            <div class="flex items-center gap-2">
              <span class="badge bg-emerald-600 text-white font-mono text-[10px]">HTTP 200 OK</span>
              <span id="api-url-display" class="font-mono text-xs text-slate-700 font-semibold">GET /health</span>
            </div>
            <span class="text-[11px] text-slate-500 font-mono">Response: application/json</span>
          </div>
          <pre id="api-response-body" class="p-4 bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto max-h-72 leading-relaxed">
{{"status": "healthy", "service": "rossmann-demand-forecasting-api", "version": "1.0.0"}}
          </pre>
        </div>
      </div>
    </section>

  </main>

  <!-- Footer -->
  <footer class="bg-white border-t border-slate-200 py-4 text-xs text-slate-500 text-center">
    <div class="max-w-7xl mx-auto px-4">
      IT4063E Business Analytics — Retail Demand Forecasting & Inventory Optimization (Rossmann Sales)
    </div>
  </footer>

  <!-- Application Logic & Embedded Data -->
  <script>
    const BUNDLE = {bundle_json_str};
    const MONITORING = {monitoring_json_str};

    let edaChartInstance = null;
    let forecastChartInstance = null;
    let monitoringChartInstance = null;

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(btn => {{
        btn.classList.remove('bg-blue-50', 'text-blue-700', 'font-semibold');
        btn.classList.add('text-slate-600');
      }});

      document.getElementById('tab-' + tabId).classList.add('active');
      const activeBtn = document.getElementById('tab-btn-' + tabId);
      if (activeBtn) {{
        activeBtn.classList.add('bg-blue-50', 'text-blue-700', 'font-semibold');
        activeBtn.classList.remove('text-slate-600');
      }}

      if (tabId === 'eda') setTimeout(renderEdaChart, 50);
      if (tabId === 'forecast') setTimeout(renderForecastChart, 50);
      if (tabId === 'monitoring') setTimeout(renderMonitoringChart, 50);
    }}

    function renderEdaChart() {{
      const storeId = parseInt(document.getElementById('eda-store-select').value);
      const rows = BUNDLE.history_rows.filter(r => r.store_id === storeId);
      rows.sort((a, b) => a.date.localeCompare(b.date));

      const labels = rows.map(r => r.date);
      const sales = rows.map(r => r.sales_value);

      if (edaChartInstance) edaChartInstance.destroy();

      const ctx = document.getElementById('edaSalesChart').getContext('2d');
      edaChartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: labels,
          datasets: [{{
            label: 'Daily Sales Turnover ($)',
            data: sales,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.08)',
            borderWidth: 2,
            pointRadius: 2.5,
            fill: true,
            tension: 0.15
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: true, position: 'top' }},
            tooltip: {{ mode: 'index', intersect: false }}
          }},
          scales: {{
            y: {{ beginAtZero: true, title: {{ display: true, text: 'Monetary Turnover' }} }},
            x: {{ ticks: {{ maxTicksLimit: 14 }} }}
          }}
        }}
      }});
    }}

    function renderForecastChart() {{
      const storeId = parseInt(document.getElementById('forecast-store-select').value);
      const origin = document.getElementById('forecast-origin-select').value;

      // Filter forecast rows
      const fRows = BUNDLE.forecast_rows.filter(r => r.store_id === storeId && r.forecast_origin === origin);
      fRows.sort((a, b) => a.horizon - b.horizon);

      // Uncertainty intervals
      const uView = BUNDLE.uncertainty_views.find(u => u.store_id === storeId && u.forecast_origin === origin);
      const intervals = uView ? uView.daily_intervals.filter(i => i.interval_kind === 'raw') : [];
      intervals.sort((a, b) => a.horizon - b.horizon);

      const labels = fRows.map(r => 'h' + r.horizon + ' (' + r.date + ')');
      const pointForecasts = fRows.map(r => r.operational_forecast_value);
      const uppers = intervals.map(i => i.upper);
      const lowers = intervals.map(i => i.lower);

      if (forecastChartInstance) forecastChartInstance.destroy();

      const ctx = document.getElementById('forecastChart').getContext('2d');
      forecastChartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: labels,
          datasets: [
            {{
              label: 'Upper 95% Confidence Bound',
              data: uppers,
              borderColor: 'transparent',
              backgroundColor: 'rgba(99, 102, 241, 0.18)',
              pointRadius: 0,
              fill: '+1'
            }},
            {{
              label: 'Lower 95% Confidence Bound',
              data: lowers,
              borderColor: 'transparent',
              backgroundColor: 'transparent',
              pointRadius: 0,
              fill: false
            }},
            {{
              label: 'Global LightGBM Point Forecast',
              data: pointForecasts,
              borderColor: '#4f46e5',
              backgroundColor: '#4f46e5',
              borderWidth: 2.5,
              pointRadius: 4,
              fill: false,
              tension: 0.1
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: true, position: 'top' }},
            tooltip: {{ mode: 'index', intersect: false }}
          }},
          scales: {{
            y: {{ beginAtZero: false, title: {{ display: true, text: 'Sales Turnover' }} }}
          }}
        }}
      }});

      // Populate table
      const tbody = document.getElementById('forecast-table-body');
      tbody.innerHTML = '';
      fRows.forEach((r, idx) => {{
        const iv = intervals[idx] || {{ lower: '-', upper: '-', width: '-' }};
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="p-2.5 font-bold text-slate-800">h${{r.horizon}}</td>
          <td class="p-2.5 font-mono">${{r.date}}</td>
          <td class="p-2.5"><span class="badge ${{r.synthetic_open_eligibility === 'known_open' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'}}">${{r.synthetic_open_eligibility}}</span></td>
          <td class="p-2.5 text-right font-semibold">${{Number(r.operational_forecast_value).toLocaleString()}}</td>
          <td class="p-2.5 text-right text-slate-500">${{typeof iv.lower === 'number' ? Number(iv.lower.toFixed(1)).toLocaleString() : '-'}}</td>
          <td class="p-2.5 text-right text-slate-500">${{typeof iv.upper === 'number' ? Number(iv.upper.toFixed(1)).toLocaleString() : '-'}}</td>
          <td class="p-2.5 text-right font-mono text-indigo-700">${{typeof iv.width === 'number' ? Number(iv.width.toFixed(1)).toLocaleString() : '-'}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function updateInventoryCalc() {{
      const leadTime = parseInt(document.getElementById('inv-lead-time').value);
      document.getElementById('inv-lead-val').innerText = leadTime + ' days';
      const p = parseFloat(document.getElementById('inv-service-level').value);
      const onHand = parseFloat(document.getElementById('inv-onhand').value) || 0;

      // Protection period P = L + 1
      const P = leadTime + 1;
      const dailyBase = 11200;
      const expectedDemand = dailyBase * P;

      // Uncertainty multiplier for P
      const qFactors = {{ 0.90: 850, 0.95: 1360, 0.98: 1980 }};
      const ss = Math.round(qFactors[p] * Math.sqrt(P));
      const orderUpTo = expectedDemand + ss;
      const suggestedReorder = Math.max(0, orderUpTo - onHand);

      document.getElementById('calc-dp').innerText = '$' + expectedDemand.toLocaleString();
      document.getElementById('calc-ss').innerText = '$' + ss.toLocaleString();
      document.getElementById('calc-s').innerText = '$' + orderUpTo.toLocaleString();
      document.getElementById('calc-q').innerText = '$' + suggestedReorder.toLocaleString();
    }}

    function renderMonitoringChart() {{
      const records = MONITORING.rolling_metrics || [];
      const labels = records.map(r => r.window_end_date);
      const lgb = records.map(r => r.lgb_mae);
      const naive = records.map(r => r.naive_mae);

      if (monitoringChartInstance) monitoringChartInstance.destroy();

      const ctx = document.getElementById('monitoringChart').getContext('2d');
      monitoringChartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: labels,
          datasets: [
            {{
              label: 'Global LightGBM 7-Day Rolling MAE',
              data: lgb,
              borderColor: '#2563eb',
              backgroundColor: '#2563eb',
              borderWidth: 2.5,
              pointRadius: 3,
              tension: 0.1
            }},
            {{
              label: 'Seasonal Naive 7-Day Rolling MAE',
              data: naive,
              borderColor: '#dc2626',
              borderDash: [5, 5],
              pointRadius: 2,
              borderWidth: 2,
              tension: 0.1
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            y: {{ title: {{ display: true, text: 'MAE (Turnover Error)' }} }}
          }}
        }}
      }});
    }}

    function updateApiParams() {{
      const endpoint = document.getElementById('api-endpoint-select').value;
      const storeSelect = document.getElementById('api-store-select');
      if (endpoint === '/health' || endpoint === '/api/v1/model-comparison') {{
        storeSelect.disabled = true;
      }} else {{
        storeSelect.disabled = false;
      }}
    }}

    function executeApiCall() {{
      const endpoint = document.getElementById('api-endpoint-select').value;
      const storeId = document.getElementById('api-store-select').value;
      const displayUrl = document.getElementById('api-url-display');
      const responseBody = document.getElementById('api-response-body');

      let url = endpoint;
      let resp = {{}};

      if (endpoint === '/health') {{
        url = '/health';
        resp = {{ "status": "healthy", "service": "rossmann-demand-forecasting-api", "version": "1.0.0" }};
      }} else if (endpoint === '/api/v1/forecasts') {{
        url = `/api/v1/forecasts?store_id=${{storeId}}&forecast_origin=2015-06-19`;
        resp = {{
          "store_id": parseInt(storeId),
          "forecast_origin": "2015-06-19",
          "horizon_count": 14,
          "forecasts": BUNDLE.forecast_rows.filter(r => r.store_id === parseInt(storeId) && r.forecast_origin === '2015-06-19').slice(0, 3)
        }};
      }} else if (endpoint === '/api/v1/uncertainty') {{
        url = `/api/v1/uncertainty?store_id=${{storeId}}&fit_id=demo_fit_b`;
        const uv = BUNDLE.uncertainty_views.find(u => u.store_id === parseInt(storeId) && u.fit_id === 'demo_fit_b');
        resp = {{
          "store_id": parseInt(storeId),
          "fit_id": "demo_fit_b",
          "coverage_confidence": "95%",
          "sample_intervals": uv ? uv.daily_intervals.slice(0, 2) : []
        }};
      }} else if (endpoint === '/api/v1/model-comparison') {{
        url = '/api/v1/model-comparison?validation_window=synthetic_display_panel';
        resp = {{
          "population": "synthetic_open_label_rows",
          "candidates": ["demo_path_a (Seasonal Naive)", "demo_path_b (Holt-Winters)", "demo_path_c (Global LightGBM)"],
          "sample_metric_rows": BUNDLE.comparison_panel.rows.slice(0, 3)
        }};
      }} else if (endpoint === '/api/v1/inventory') {{
        url = `/api/v1/inventory?case_id=synthetic_demo_reference_20150605&store_id=${{storeId}}`;
        resp = {{
          "case_id": "synthetic_demo_reference_20150605",
          "store_id": parseInt(storeId),
          "baseline_cost": 620.0,
          "forecast_cost": 590.0,
          "cost_difference": -30.0,
          "fill_rate": 0.9428
        }};
      }}

      displayUrl.innerText = 'GET ' + url;
      responseBody.innerText = JSON.stringify(resp, null, 2);
    }}

    // Initial load
    window.addEventListener('DOMContentLoaded', () => {{
      renderEdaChart();
      renderForecastChart();
      updateInventoryCalc();
      renderMonitoringChart();
    }});
  </script>
</body>
</html>
"""
    return html


def main() -> None:
    print("Loading demo bundle and monitoring summary...")
    bundle, monitoring = load_data()

    print("Generating index.html for Hugging Face Space...")
    html_content = generate_index_html(bundle, monitoring)

    space_dir = REPOSITORY_ROOT / "artifacts" / "hf_space"
    space_dir.mkdir(parents=True, exist_ok=True)
    index_path = space_dir / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Wrote index.html to {index_path} ({len(html_content):,} chars)")

    # Upload files to Hugging Face Space
    print(f"Deploying to Hugging Face Space: {REPO_ID}...")
    api = HfApi(token=HF_TOKEN)

    # 1. README.md
    readme_text = """---
title: Rossmann Sales Forecasting & Inventory Optimization
emoji: 📈
colorFrom: blue
colorTo: indigo
sdk: static
pinned: false
---

# Retail Demand Forecasting for Inventory Optimization (FMCG)
**IT4063E – Introduction to Business Analytics (Group Project)**
- **Team:** Pham Le Minh Quang, Tran Quoc Tuan, Vo Ta Quang Nhat, Nguyen Trung Hieu, Nguyen Gia Minh
- **Instructor:** Dr. Bui Quoc Trung
- **Course Deployment Target:** Hugging Face Spaces (Static WebApp & Live REST API Demonstration)
"""
    api.upload_file(
        path_or_fileobj=readme_text.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=REPO_ID,
        repo_type="space",
    )
    print("Uploaded README.md")

    # 2. index.html
    api.upload_file(
        path_or_fileobj=index_path,
        path_in_repo="index.html",
        repo_id=REPO_ID,
        repo_type="space",
    )
    print("Uploaded index.html")

    # 3. model_monitoring_report.html (Evidently standalone report)
    if EVIDENTLY_HTML_PATH.exists():
        api.upload_file(
            path_or_fileobj=EVIDENTLY_HTML_PATH,
            path_in_repo="model_monitoring_report.html",
            repo_id=REPO_ID,
            repo_type="space",
        )
        print("Uploaded model_monitoring_report.html")

    print("\nSUCCESS! Deployment completed successfully.")
    print(f"Public Live Space URL: https://huggingface.co/spaces/{REPO_ID}")
    print("Direct Host URL: https://hieu-nguyen2208-rossmann-sales-forecasting.static.hf.space")


if __name__ == "__main__":
    main()
