# =====================================================
# IMPORTS
# =====================================================

from contextlib import contextmanager
from datetime import datetime, timedelta
from html import escape
from io import BytesIO
from pathlib import Path
import hashlib
import hmac
import os
import re
import secrets

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database import PredictionHistory, SessionLocal, User
from database import get_all_users
from database import delete_user
from database import promote_to_admin
from database import demote_to_user
from database import get_total_users
from database import get_total_predictions
from database import get_high_risk_predictions
from database import get_admin_count


# =====================================================
# CONSTANTS
# =====================================================

APP_TITLE = "Financial Operations Analytics"
ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT_DIR / "models" / "churn_prediction_model.pkl"
PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260000
SESSION_TIMEOUT_MINUTES = int(os.getenv("FOA_SESSION_TIMEOUT_MINUTES", "45"))

RISK_ORDER = ["LOW RISK", "MEDIUM RISK", "HIGH RISK"]
RISK_COLORS = {
    "LOW RISK": "#10B981",
    "MEDIUM RISK": "#F59E0B",
    "HIGH RISK": "#EF4444",
}


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="FOA",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown(
    """
    <style>
        :root {
            --bg: #050816;
            --bg-2: #070B18;
            --panel: rgba(8, 17, 32, 0.84);
            --panel-strong: rgba(15, 23, 42, 0.96);
            --line: rgba(96, 165, 250, 0.20);
            --line-strong: rgba(125, 211, 252, 0.45);
            --text: #F8FAFC;
            --muted: #94A3B8;
            --blue: #3B82F6;
            --cyan: #22D3EE;
            --green: #10B981;
            --amber: #F59E0B;
            --red: #EF4444;
            [data-testid="stHorizontalBlock"] {
             align-items: center;
        }
        }

        html, body, [class*="css"] {
            font-family: Inter, "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text);
            background: var(--bg);
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(59, 130, 246, 0.18), transparent 28%),
                radial-gradient(circle at 86% 12%, rgba(34, 211, 238, 0.12), transparent 24%),
                linear-gradient(180deg, #050816 0%, #070B18 44%, #050816 100%);
        }

        .block-container {
         max-width: 1640px;
         padding-top: 0.6rem;
         padding-bottom: 1rem;
         padding-left: 1.75rem;
         padding-right: 1.75rem;
        }

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(6, 12, 25, 0.98), rgba(15, 23, 42, 0.98));
            border-right: 1px solid var(--line);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        h1, h2, h3, h4, p {
            letter-spacing: 0;
        }

        .auth-shell {
            min-height: 92vh;
            display: grid;
            grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.78fr);
            gap: 1.2rem;
            align-items: center;
        }

        .auth-visual {
            position: relative;
            overflow: hidden;
            min-height: 720px;
            padding: clamp(1.35rem, 2vw, 2.25rem);
            border: 1px solid rgba(125, 211, 252, 0.22);
            border-radius: 28px;
            background:
                linear-gradient(145deg, rgba(15, 23, 42, 0.92), rgba(8, 17, 32, 0.72)),
                radial-gradient(circle at 20% 20%, rgba(59, 130, 246, 0.25), transparent 30%);
            box-shadow: 0 28px 80px rgba(0, 0, 0, 0.42);
        }

        .auth-visual:before {
            content: "";
            position: absolute;
            inset: -35%;
            background:
                conic-gradient(from 180deg, transparent, rgba(34, 211, 238, 0.18), transparent, rgba(59, 130, 246, 0.14), transparent);
            animation: slow-rotate 18s linear infinite;
            opacity: 0.9;
        }

        .auth-visual:after {
            content: "";
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(125, 211, 252, 0.065) 1px, transparent 1px),
                linear-gradient(90deg, rgba(125, 211, 252, 0.065) 1px, transparent 1px);
            background-size: 48px 48px;
            mask-image: radial-gradient(circle at 58% 42%, black 0%, transparent 72%);
            opacity: 0.62;
        }

        .auth-inner {
            position: relative;
            z-index: 1;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 1rem;
        }

        .brand-chip {
            display: inline-flex;
            width: fit-content;
            align-items: center;
            gap: 0.55rem;
            padding: 0.5rem 0.8rem;
            color: #BFDBFE;
            background: rgba(15, 23, 42, 0.74);
            border: 1px solid rgba(125, 211, 252, 0.22);
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 750;
        }

        .auth-title {
            max-width: 860px;
            margin: 1.25rem 0 0.65rem;
            color: white;
            font-size: clamp(2.2rem, 4vw, 4.6rem);
            line-height: 0.98;
            font-weight: 880;
        }

        .auth-copy {
            max-width: 670px;
            color: #CBD5E1;
            font-size: clamp(0.92rem, 1.05vw, 1.06rem);
            line-height: 1.55;
        }

        .intelligence-stage {
            position: relative;
            min-height: 180px;  
            margin-top: 1rem;
            border: 1px solid rgba(125, 211, 252, 0.18);
            border-radius: 24px;
            background:
                linear-gradient(145deg, rgba(2, 6, 23, 0.54), rgba(15, 23, 42, 0.36)),
                radial-gradient(circle at 50% 50%, rgba(59, 130, 246, 0.18), transparent 42%);
            overflow: hidden;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 24px 60px rgba(0, 0, 0, 0.28);
        }

        .orbital-core {
            position: absolute;
            width: clamp(124px, 14vw, 168px);
            height: clamp(124px, 14vw, 168px);
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            border-radius: 999px;
            background:
                radial-gradient(circle, rgba(248, 250, 252, 0.16) 0 8%, rgba(34, 211, 238, 0.30) 9% 18%, rgba(37, 99, 235, 0.16) 19% 42%, rgba(15, 23, 42, 0.20) 43%);
            border: 1px solid rgba(125, 211, 252, 0.30);
            box-shadow:
                0 0 52px rgba(34, 211, 238, 0.28),
                inset 0 0 42px rgba(59, 130, 246, 0.22);
        }

        .orbital-core:before,
        .orbital-core:after {
            content: "";
            position: absolute;
            inset: -34px;
            border-radius: 999px;
            border: 1px solid rgba(125, 211, 252, 0.22);
            animation: slow-rotate 14s linear infinite;
        }

        .orbital-core:after {
            inset: -68px;
            border-style: dashed;
            border-color: rgba(167, 139, 250, 0.24);
            animation-duration: 22s;
            animation-direction: reverse;
        }

        .signal-line {
            position: absolute;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(125, 211, 252, 0.58), transparent);
            transform-origin: left center;
            opacity: 0.82;
        }

        .signal-line.one {
            width: 38%;
            left: 9%;
            top: 34%;
            transform: rotate(7deg);
        }

        .signal-line.two {
            width: 33%;
            right: 8%;
            top: 62%;
            transform: rotate(-11deg);
        }

        .signal-line.three {
            width: 30%;
            left: 18%;
            bottom: 20%;
            transform: rotate(-5deg);
        }

        .terminal-panel {
            position: absolute;
            width: min(220px, 36%);
            padding: 0.75rem;
            border: 1px solid rgba(125, 211, 252, 0.24);
            border-radius: 16px;
            background: rgba(2, 6, 23, 0.70);
            box-shadow: 0 18px 42px rgba(0, 0, 0, 0.34);
            backdrop-filter: blur(18px);
        }

        .terminal-panel.top {
            top: 1.1rem;
            right: 1.2rem;
        }

        .terminal-panel.bottom {
            bottom: 1.1rem;
            left: 1.2rem;
        }

        .terminal-panel .panel-label {
            color: #93C5FD;
            font-size: 0.68rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        .mini-bars {
            display: flex;
            align-items: end;
            gap: 0.35rem;
            height: 42px;
        }

        .mini-bars span {
            flex: 1;
            border-radius: 999px 999px 0 0;
            background: linear-gradient(180deg, #67E8F9, #2563EB);
            box-shadow: 0 0 20px rgba(34, 211, 238, 0.24);
        }

        .waveform {
            width: 100%;
            height: 46px;
        }

        .waveform path {
            fill: none;
            stroke: #67E8F9;
            stroke-width: 3;
            filter: drop-shadow(0 0 8px rgba(34, 211, 238, 0.55));
            stroke-dasharray: 320;
            animation: trace-line 5s ease-in-out infinite;
        }

        .node {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: #67E8F9;
            box-shadow: 0 0 22px rgba(103, 232, 249, 0.85);
            animation: node-pulse 2.8s ease-in-out infinite;
        }

        .node.n1 { left: 12%; top: 32%; }
        .node.n2 { right: 14%; top: 58%; animation-delay: -0.8s; }
        .node.n3 { left: 26%; bottom: 18%; animation-delay: -1.6s; }

        .auth-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .floating-card {
            position: relative;
            overflow: hidden;
            min-height: 104px;
            padding: 0.85rem;
            border: 1px solid rgba(125, 211, 252, 0.22);
            border-radius: 18px;
            background: rgba(8, 17, 32, 0.72);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 18px 38px rgba(0, 0, 0, 0.28);
            animation: float-card 6s ease-in-out infinite;
        }

        .floating-card:nth-child(2) {
            animation-delay: -1.4s;
        }

        .floating-card:nth-child(3) {
            animation-delay: -2.7s;
        }

        .floating-card:nth-child(4) {
            animation-delay: -4.1s;
        }

        .floating-card span {
            color: #93C5FD;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .floating-card h3 {
            color: white;
            margin: 0.48rem 0 0.25rem;
            font-size: clamp(1rem, 1.2vw, 1.18rem);
        }

        .floating-card p {
            color: var(--muted);
            margin: 0;
            line-height: 1.35;
            font-size: 0.82rem;
        }

        .security-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 0.85rem;
        }

        .security-pill {
            padding: 0.7rem;
            border-radius: 14px;
            color: #CBD5E1;
            background: rgba(15, 23, 42, 0.66);
            border: 1px solid rgba(148, 163, 184, 0.14);
            font-size: 0.86rem;
        }
        .auth-panel {
             display: flex;
             align-items: center;
             justify-content: center;
             min-height: auto;
             height: 100%;
        }

        .auth-card {
            max-width: 520px;
            margin: auto;
            padding: clamp(1.2rem, 2vw, 1.65rem);
            border: 1px solid rgba(125, 211, 252, 0.24);
            border-radius: 24px;
            background:
                linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(8, 17, 32, 0.90));
            box-shadow: 0 28px 70px rgba(0, 0, 0, 0.38);
        }

        .page-title {
            color: var(--text);
            font-size: clamp(1.9rem, 3vw, 2.8rem);
            font-weight: 820;
            margin: 0 0 0.3rem;
        }

        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.95rem 1.1rem;
            margin-bottom: 1.25rem;
            border: 1px solid rgba(125, 211, 252, 0.18);
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.86), rgba(8, 17, 32, 0.72));
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.26);
            backdrop-filter: blur(18px);
        }

        .header-title {
            color: white;
            font-weight: 850;
            font-size: 1rem;
            margin: 0;
        }

        .header-meta {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            flex-wrap: wrap;
            color: var(--muted);
            font-size: 0.82rem;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 0.6rem;
            border-radius: 999px;
            border: 1px solid rgba(125, 211, 252, 0.22);
            color: #BFDBFE;
            background: rgba(14, 165, 233, 0.10);
            font-weight: 750;
        }

        .notify {
            padding: 0.9rem 1rem;
            margin: 0.75rem 0;
            border-radius: 14px;
            border: 1px solid rgba(125, 211, 252, 0.18);
            background: rgba(8, 17, 32, 0.78);
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.25);
            animation: fade-in 260ms ease both;
        }

        .notify strong {
            display: block;
            color: white;
            margin-bottom: 0.2rem;
        }

        .notify p {
            color: #CBD5E1;
            margin: 0;
        }

        .notify.success { border-color: rgba(16, 185, 129, 0.38); background: rgba(6, 78, 59, 0.28); }
        .notify.error { border-color: rgba(239, 68, 68, 0.38); background: rgba(127, 29, 29, 0.25); }
        .notify.warning { border-color: rgba(245, 158, 11, 0.38); background: rgba(120, 53, 15, 0.25); }
        .notify.info { border-color: rgba(59, 130, 246, 0.36); background: rgba(30, 64, 175, 0.22); }

        .strength-track {
            height: 8px;
            width: 100%;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.18);
            overflow: hidden;
            margin: 0.45rem 0 0.25rem;
        }

        .strength-fill {
            height: 100%;
            border-radius: 999px;
            transition: width 180ms ease;
        }

        .empty-state {
            position: relative;
            overflow: hidden;
            padding: 2rem;
            border: 1px solid rgba(125, 211, 252, 0.20);
            border-radius: 20px;
            background:
                radial-gradient(circle at 18% 24%, rgba(59, 130, 246, 0.18), transparent 30%),
                linear-gradient(145deg, rgba(15, 23, 42, 0.90), rgba(8, 17, 32, 0.74));
            box-shadow: 0 22px 58px rgba(0, 0, 0, 0.34);
        }

        .empty-mark {
            width: 76px;
            height: 76px;
            border-radius: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #BAE6FD;
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.42), rgba(14, 165, 233, 0.18));
            border: 1px solid rgba(125, 211, 252, 0.24);
            font-weight: 900;
            font-size: 1.35rem;
            margin-bottom: 1rem;
        }

        .chart-shell {
            padding: 0.7rem;
            border: 1px solid rgba(125, 211, 252, 0.14);
            border-radius: 18px;
            background: rgba(8, 17, 32, 0.34);
        }

        .footer-shell {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
            color: #94A3B8;
            padding: 1rem 0 0;
            font-size: 0.84rem;
        }

        .subtitle {
            color: var(--muted);
            font-size: 1.02rem;
            line-height: 1.65;
            margin: 0;
        }

        .section-label {
            color: #BFDBFE;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .card, .profile-card, .sidebar-card, .data-panel {
            background:
                linear-gradient(145deg, rgba(15, 23, 42, 0.90), rgba(30, 41, 59, 0.76));
            border: 1px solid var(--line);
            border-radius: 18px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.32);
            backdrop-filter: blur(18px);
        }

        .card {
            padding: 1.35rem;
            transition: transform 170ms ease, border-color 170ms ease, box-shadow 170ms ease;
        }

        .card:hover {
            transform: translateY(-2px);
            border-color: var(--line-strong);
            box-shadow: 0 24px 58px rgba(0, 0, 0, 0.42);
        }

        .metric-card h4 {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 800;
            margin: 0 0 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .metric-card h2 {
            color: var(--text);
            font-size: clamp(1.65rem, 2.6vw, 2.25rem);
            font-weight: 850;
            margin: 0;
        }

        .metric-card p {
            color: #93C5FD;
            font-size: 0.9rem;
            margin: 0.55rem 0 0;
        }

        .sidebar-brand {
            color: white;
            font-size: 1.75rem;
            font-weight: 900;
            margin-bottom: 1rem;
        }

        .sidebar-card {
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .sidebar-card h3 {
            color: white;
            font-size: 1rem;
            margin: 0 0 0.35rem;
        }

        .sidebar-card p {
            color: var(--muted);
            margin: 0.24rem 0;
        }

        .status-dot {
            display: inline-block;
            width: 0.62rem;
            height: 0.62rem;
            border-radius: 999px;
            margin-right: 0.55rem;
            box-shadow: 0 0 18px currentColor;
        }

        .insight-item {
            background: rgba(8, 17, 32, 0.66);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }

        .insight-item h4 {
            color: white;
            margin: 0 0 0.45rem;
            font-size: 1rem;
        }

        .insight-item p {
            color: var(--muted);
            line-height: 1.55;
            margin: 0;
        }

        .recommendation-card {
            border-left: 3px solid #38BDF8;
            background: rgba(8, 17, 32, 0.72);
            border-radius: 14px;
            padding: 1rem;
        }

        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] button {
            background: linear-gradient(135deg, #2563EB, #0EA5E9);
            color: white;
            border: 0;
            border-radius: 12px;
            min-height: 3rem;
            font-weight: 800;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.24);
            width: 100%;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            color: white;
            border: 0;
            filter: brightness(1.08);
            transform: translateY(-1px);
        }

        [data-testid="metric-container"] {
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.90), rgba(30, 41, 59, 0.78));
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 1rem;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 16px;
            overflow: hidden;
        }

        div[data-testid="stRadio"] label {
            color: #CBD5E1;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stSelectbox"] div[data-baseweb="select"],
        [data-testid="stMultiSelect"] div[data-baseweb="select"] {
            border-radius: 12px;
            border-color: rgba(125, 211, 252, 0.20);
            background-color: rgba(2, 6, 23, 0.52);
            color: #F8FAFC;
        }

        section[data-testid="stSidebar"] [role="radiogroup"] label {
            padding: 0.35rem 0.4rem;
            border-radius: 12px;
            transition: background 160ms ease, transform 160ms ease;
        }

        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: rgba(59, 130, 246, 0.10);
            transform: translateX(2px);
        }

        @keyframes slow-rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes float-card {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }

        @keyframes trace-line {
            0%, 100% { stroke-dashoffset: 0; opacity: 0.72; }
            50% { stroke-dashoffset: -120; opacity: 1; }
        }

        @keyframes node-pulse {
            0%, 100% { transform: scale(1); opacity: 0.75; }
            50% { transform: scale(1.65); opacity: 1; }
        }

        @keyframes fade-in {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 1050px) {
            .auth-shell {
                grid-template-columns: 1fr;
            }

            .auth-visual, .auth-panel {
                min-height: auto;
            }

            .auth-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .auth-panel {
                 margin-top: -40px;
            }
        }
        

        @media (max-height: 820px) and (min-width: 1051px) {
            .block-container {
                padding-top: 0.75rem;
                padding-bottom: 1rem;
            }

            .auth-visual, .auth-panel {
                min-height: calc(100vh - 2rem);
            }

            .auth-title {
                font-size: clamp(2rem, 3.35vw, 3.85rem);
                margin-top: 0.8rem;
            }

            .intelligence-stage {
                min-height: 205px;
            }

            .floating-card {
                min-height: 86px;
                padding: 0.7rem;
            }

            .floating-card p {
                display: none;
            }

            .security-strip {
                display: none;
            }
        }

        @media (max-width: 760px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .auth-visual, .auth-card, .card {
                padding: 1rem;
                border-radius: 16px;
            }

            .auth-grid, .security-strip {
                grid-template-columns: 1fr;
            }

            .intelligence-stage {
                min-height: 360px;
            }

            .terminal-panel {
                position: relative;
                width: auto;
                inset: auto !important;
                margin: 1rem;
            }

            .orbital-core {
                top: 48%;
                width: 132px;
                height: 132px;
            }

            .app-header {
                align-items: flex-start;
                flex-direction: column;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# SESSION STATE
# =====================================================

def initialize_session_state() -> None:
    defaults = {
        "logged_in": False,
        "username": "",
        "edit_mode": False,
        "auth_failures": 0,
        "last_login": "",
        "last_activity": datetime.now().isoformat(timespec="seconds"),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def enforce_session_timeout() -> None:
    if not st.session_state.get("logged_in"):
        return

    try:
        last_activity = datetime.fromisoformat(st.session_state.last_activity)
    except ValueError:
        last_activity = datetime.now()

    if datetime.now() - last_activity > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        for key in ["logged_in", "username", "edit_mode"]:
            st.session_state.pop(key, None)
        notify("Session expired", "Your secure session timed out. Please sign in again.", "warning")
        st.stop()

    st.session_state.last_activity = datetime.now().isoformat(timespec="seconds")


# =====================================================
# SECURITY HELPERS
# =====================================================

def normalize_username(username: str) -> str:
    return (username or "").strip()


def sanitize(value: object) -> str:
    return escape(str(value or ""))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_password: str) -> bool:
    if not stored_password:
        return False

    parts = stored_password.split("$")
    if len(parts) == 4 and parts[0] == PASSWORD_SCHEME:
        _, iterations, salt, expected = parts
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(digest, expected)

    return hmac.compare_digest(password, stored_password)


def is_hashed_password(stored_password: str) -> bool:
    return bool(stored_password and stored_password.startswith(f"{PASSWORD_SCHEME}$"))


def validate_password_strength(password: str) -> list[str]:
    issues = []
    if len(password) < 8:
        issues.append("Use at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        issues.append("Add one uppercase letter.")
    if not re.search(r"[a-z]", password):
        issues.append("Add one lowercase letter.")
    if not re.search(r"\d", password):
        issues.append("Add one number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        issues.append("Add one symbol.")
    return issues


def password_strength_score(password: str) -> tuple[int, str, str]:
    checks = [
        len(password) >= 8,
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"\d", password)),
        bool(re.search(r"[^A-Za-z0-9]", password)),
    ]
    score = sum(checks)
    if score <= 2:
        return score, "Weak", "#EF4444"
    if score <= 4:
        return score, "Good", "#F59E0B"
    return score, "Enterprise strong", "#10B981"


def has_valid_username_format(username: str) -> bool:
    if "@" in username:
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", username))
    return bool(re.match(r"^[A-Za-z0-9_.-]{3,64}$", username))


def validate_account_fields(username: str, password: str | None, require_password: bool = True) -> list[str]:
    issues = []
    if not username:
        issues.append("Username or email is required.")
    if username and not has_valid_username_format(username):
        issues.append("Use a valid email address or a 3+ character username with letters, numbers, dots, dashes, or underscores.")
    if password or require_password:
        issues.extend(validate_password_strength(password or ""))
    return issues


# =====================================================
# DATABASE HELPERS
# =====================================================

@contextmanager
def get_db_session(commit: bool = False):
    db = SessionLocal()
    try:
        yield db
        if commit:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_user(username: str):
    username = normalize_username(username)
    if not username:
        return None

    with get_db_session() as db:
        return db.query(User).filter(User.username == username).first()


def create_user(username: str, password: str, company: str, role: str, location: str, department: str) -> None:
    with get_db_session(commit=True) as db:
        db.add(
            User(
                username=normalize_username(username),
                password=hash_password(password),
                company=company.strip(),
                role=role.strip(),
                location=location.strip(),
                department=department.strip(),
            )
        )


def migrate_legacy_password(username: str, password: str) -> None:
    with get_db_session(commit=True) as db:
        user = db.query(User).filter(User.username == username).first()
        if user and not is_hashed_password(user.password):
            user.password = hash_password(password)


def save_prediction(
    username: str,
    tenure: int,
    monthly_charges: float,
    total_charges: float,
    probability: float,
    risk: str,
) -> None:
    with get_db_session(commit=True) as db:
        db.add(
            PredictionHistory(
                username=username,
                tenure=int(tenure),
                monthly_charges=float(monthly_charges),
                total_charges=float(total_charges),
                probability=float(probability),
                risk=risk,
                prediction_date=datetime.now().isoformat(timespec="seconds"),
            )
        )


def get_prediction_history(username: str):
    with get_db_session() as db:
        return (
            db.query(PredictionHistory)
            .filter(PredictionHistory.username == username)
            .order_by(PredictionHistory.id.desc())
            .all()
        )


def get_all_predictions():
    with get_db_session() as db:
        return db.query(PredictionHistory).order_by(PredictionHistory.id.desc()).all()


def update_user_profile(user_id: int, old_username: str, values: dict) -> None:
    with get_db_session(commit=True) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError("Your account could not be found. Please log in again.")

        existing_user = db.query(User).filter(User.username == values["username"]).first()
        if existing_user and existing_user.id != user_id:
            raise ValueError("Username already exists. Try another username.")

        user.username = values["username"]
        user.company = values["company"]
        user.role = values["role"]
        user.department = values["department"]
        user.location = values["location"]
        if values.get("password"):
            user.password = hash_password(values["password"])

        (
            db.query(PredictionHistory)
            .filter(PredictionHistory.username == old_username)
            .update({PredictionHistory.username: values["username"]}, synchronize_session=False)
        )


# =====================================================
# MODEL HELPERS
# =====================================================

@st.cache_resource(show_spinner=False)
def load_model():
    return joblib.load(MODEL_PATH)


def build_prediction_frame(model, tenure: int, monthly_charges: float, total_charges: float) -> pd.DataFrame:
    input_data = pd.DataFrame(
        {
            "tenure": [tenure],
            "MonthlyCharges": [monthly_charges],
            "TotalCharges": [total_charges],
        }
    )

    feature_names = list(getattr(model, "feature_names_in_", input_data.columns))
    for column in feature_names:
        if column not in input_data.columns:
            input_data[column] = 0

    return input_data[feature_names]


def classify_risk(probability: float) -> str:
    if probability > 0.70:
        return "HIGH RISK"
    if probability > 0.40:
        return "MEDIUM RISK"
    return "LOW RISK"


def confidence_score(probability: float) -> float:
    return max(probability, 1 - probability)


def recommendation_for_risk(risk: str, probability: float) -> str:
    if risk == "HIGH RISK":
        return (
            "Open an executive retention case, prioritize a proactive outreach sequence, "
            "and review pricing or service friction before renewal exposure increases."
        )
    if risk == "MEDIUM RISK":
        return (
            "Place the account into a monitored retention segment and trigger a targeted "
            "value-review campaign within the next business cycle."
        )
    return (
        "Maintain automated engagement and continue monitoring. This account currently "
        "shows a healthy retention profile."
    )


# =====================================================
# DATAFRAME HELPERS
# =====================================================

def clean_risk_label(risk: str) -> str:
    text = (risk or "").upper()
    if "HIGH" in text:
        return "HIGH RISK"
    if "MEDIUM" in text:
        return "MEDIUM RISK"
    return "LOW RISK"


def predictions_to_dataframe(predictions) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {
                "Date": item.prediction_date,
                "Tenure": item.tenure,
                "Monthly Charges": item.monthly_charges,
                "Total Charges": item.total_charges,
                "Probability": item.probability,
                "Risk": clean_risk_label(item.risk),
            }
            for item in predictions
        ]
    )

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Date",
                "Tenure",
                "Monthly Charges",
                "Total Charges",
                "Probability",
                "Risk",
                "Retention Probability",
                "Confidence",
            ]
        )

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Probability"] = pd.to_numeric(df["Probability"], errors="coerce").fillna(0)
    df["Monthly Charges"] = pd.to_numeric(df["Monthly Charges"], errors="coerce").fillna(0)
    df["Total Charges"] = pd.to_numeric(df["Total Charges"], errors="coerce").fillna(0)
    df["Tenure"] = pd.to_numeric(df["Tenure"], errors="coerce").fillna(0).astype(int)
    df["Retention Probability"] = 1 - df["Probability"]
    df["Confidence"] = df["Probability"].apply(confidence_score)
    return df


def get_dashboard_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_predictions": 0,
            "retention_rate": 0,
            "high_risk_count": 0,
            "avg_probability": 0,
            "avg_confidence": 0,
            "revenue_exposure": 0,
            "monthly_exposure": 0,
            "latest_risk": "No Data",
            "model_runs_30d": 0,
        }

    recent_cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
    dated = df.dropna(subset=["Date"])
    recent_runs = int((dated["Date"] >= recent_cutoff).sum()) if not dated.empty else 0

    return {
        "total_predictions": int(len(df)),
        "retention_rate": float(df["Retention Probability"].mean() * 100),
        "high_risk_count": int((df["Risk"] == "HIGH RISK").sum()),
        "avg_probability": float(df["Probability"].mean()),
        "avg_confidence": float(df["Confidence"].mean() * 100),
        "revenue_exposure": float(df["Total Charges"].sum()),
        "monthly_exposure": float(df["Monthly Charges"].sum()),
        "latest_risk": str(df.iloc[0]["Risk"]),
        "model_runs_30d": recent_runs,
    }


def build_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or df["Date"].isna().all():
        return pd.DataFrame(columns=["Month", "Predictions", "Average Churn Risk", "Revenue Exposure"])

    dated = df.dropna(subset=["Date"]).copy()
    dated["Month"] = dated["Date"].dt.to_period("M").astype(str)
    return (
        dated.groupby("Month", as_index=False)
        .agg(
            Predictions=("Risk", "size"),
            Average_Churn_Risk=("Probability", "mean"),
            Revenue_Exposure=("Total Charges", "sum"),
        )
        .rename(
            columns={
                "Average_Churn_Risk": "Average Churn Risk",
                "Revenue_Exposure": "Revenue Exposure",
            }
        )
        .sort_values("Month")
    )


def build_forecast_summary(trend_df: pd.DataFrame) -> dict:
    if trend_df.empty:
        return {"next_volume": 0, "next_risk": 0, "direction": "No historical trend available yet."}

    last_rows = trend_df.tail(3)
    next_volume = int(round(last_rows["Predictions"].mean()))
    next_risk = float(last_rows["Average Churn Risk"].mean())

    if len(trend_df) >= 2:
        delta = trend_df.iloc[-1]["Average Churn Risk"] - trend_df.iloc[-2]["Average Churn Risk"]
        if delta > 0.03:
            direction = "Churn pressure is increasing versus the previous period."
        elif delta < -0.03:
            direction = "Churn pressure is improving versus the previous period."
        else:
            direction = "Churn pressure is stable versus the previous period."
    else:
        direction = "More prediction history will improve the forecast signal."

    return {"next_volume": next_volume, "next_risk": next_risk, "direction": direction}


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    export_df = df.copy()
    if "Date" in export_df:
        export_df["Date"] = export_df["Date"].astype(str)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Prediction History")
    return output.getvalue()


# =====================================================
# UI HELPERS
# =====================================================

def plotly_layout(fig, height: int = 420):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#F8FAFC",
        title_font_size=18,
        height=height,
        margin=dict(l=20, r=20, t=58, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="#0F172A", bordercolor="#38BDF8", font_color="#F8FAFC"),
    )
    fig.update_xaxes(
        zeroline=False,
        gridcolor="rgba(148, 163, 184, 0.14)",
        linecolor="rgba(148, 163, 184, 0.20)",
    )
    fig.update_yaxes(
        zeroline=False,
        gridcolor="rgba(148, 163, 184, 0.14)",
        linecolor="rgba(148, 163, 184, 0.20)",
    )
    return fig


def notify(title: str, message: str, level: str = "info") -> None:
    level = level if level in {"success", "error", "warning", "info"} else "info"
    st.markdown(
        f"""
        <div class="notify {level}">
            <strong>{sanitize(title)}</strong>
            <p>{sanitize(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_password_strength(password: str) -> None:
    score, label, color = password_strength_score(password)
    width = max(score, 1) * 20
    st.markdown(
        f"""
        <div class="strength-track">
            <div class="strength-fill" style="width:{width}%; background:{color};"></div>
        </div>
        <div style="color:{color}; font-size:0.82rem; font-weight:750;">{sanitize(label)}</div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, label: str = "Enterprise Analytics") -> None:
    st.markdown(
        f"""
        <div style="padding-bottom: 1.4rem;">
            <div class="section-label">{sanitize(label)}</div>
            <h1 class="page-title">{sanitize(title)}</h1>
            <p class="subtitle">{sanitize(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="card metric-card">
            <h4>{sanitize(title)}</h4>
            <h2>{sanitize(value)}</h2>
            <p>{sanitize(caption)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, message: str, cta: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-mark">FOA</div>
            <h3 style="color:white; margin-top:0;">{sanitize(title)}</h3>
            <p class="subtitle">{sanitize(message)}</p>
            {f'<div style="margin-top:1rem;"><span class="badge">{sanitize(cta)}</span></div>' if cta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app_header(current_user, page: str) -> None:
    last_login = st.session_state.get("last_login") or "Current secure session"
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <div class="section-label">FOA Intelligence Workspace</div>
                <p class="header-title">{sanitize(page)}</p>
            </div>
            <div class="header-meta">
                <span class="badge">Secure environment</span>
                <span>{sanitize(current_user.username)}</span>
                <span>Last login: {sanitize(last_login)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    year = datetime.now().year
    st.markdown(
        f"""
        <div class="footer-shell">
            <span>FOA Intelligence © {year}</span>
            <span>Secure AI analytics powered by Python, Streamlit, SQLAlchemy, Plotly and scikit-learn</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(current_user) -> str:
    pages = ["Dashboard", "Predict Churn", "Prediction History", "Account Profile"]
    requested_page = st.session_state.pop("nav_override", None)
    default_index = pages.index(requested_page) if requested_page in pages else 0

    st.sidebar.markdown('<div class="sidebar-brand">FOA Intelligence</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        f"""
        <div class="sidebar-card">
            <div class="section-label">Secure Workspace</div>
            <h3>{sanitize(current_user.username)}</h3>
            <p>{sanitize(current_user.role or "Enterprise User")}</p>
            <p style="color:#60A5FA;">{sanitize(current_user.company or "Financial Operations")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pages = [
        "Dashboard",
        "Predict Churn",
        "Prediction History",
        "Account Profile"
    ]

    # SHOW ADMIN PANEL ONLY FOR ADMINS
    if current_user.role_type == "Admin":
        pages.append("Admin Panel")

    page = st.sidebar.radio(
        "Navigation",
        pages,
        index=default_index
    )

    st.sidebar.markdown(
        """
        <div class="sidebar-card">
            <h3>Enterprise Controls</h3>
            <p>AI prediction engine</p>
            <p>Risk intelligence</p>
            <p>Audit-ready exports</p>
            <p>Executive analytics</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Secure Logout"):
        for key in ["logged_in", "username", "edit_mode"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    return page


# =====================================================
# AUTHENTICATION PAGES
# =====================================================

def render_auth_visual() -> None:
    st.markdown(
        """
        <div class="auth-visual">
            <div class="auth-inner">
                <div>
                    <div class="brand-chip">FOA Secure AI Cloud</div>
                    <h1 class="auth-title">AI Financial Intelligence Platform</h1>
                    <p class="auth-copy">
                        Enterprise Customer Risk Analytics, Predictive Retention Intelligence,
                        and Real-Time Business Forecasting for finance, operations, and executive teams.
                    </p>
                    <div class="intelligence-stage" aria-hidden="true">
                        <div class="signal-line one"></div>
                        <div class="signal-line two"></div>
                        <div class="signal-line three"></div>
                        <div class="node n1"></div>
                        <div class="node n2"></div>
                        <div class="node n3"></div>
                        <div class="orbital-core"></div>
                        <div class="terminal-panel top">
                            <div class="panel-label">Risk Telemetry</div>
                            <div class="mini-bars">
                                <span style="height:34%;"></span>
                                <span style="height:58%;"></span>
                                <span style="height:44%;"></span>
                                <span style="height:82%;"></span>
                                <span style="height:66%;"></span>
                                <span style="height:92%;"></span>
                            </div>
                        </div>
                        <div class="terminal-panel bottom">
                            <div class="panel-label">Forecast Signal</div>
                            <svg class="waveform" viewBox="0 0 260 70" role="img" aria-label="Abstract analytics signal">
                                <path d="M4 48 C 32 8, 55 12, 78 42 S 120 64, 145 32 S 187 7, 213 35 S 241 60, 256 22"></path>
                            </svg>
                        </div>
                    </div>
                    <div class="auth-grid">
                        <div class="floating-card">
                            <span>Risk Engine</span>
                            <h3>Churn Scoring</h3>
                            <p>Model-driven retention probability and account risk segmentation.</p>
                        </div>
                        <div class="floating-card">
                            <span>Forecasting</span>
                            <h3>Trend Signal</h3>
                            <p>Prediction history converted into operational intelligence.</p>
                        </div>
                        <div class="floating-card">
                            <span>Security</span>
                            <h3>Hardened Access</h3>
                            <p>PBKDF2 credentials, session control, and validated account flows.</p>
                        </div>
                        <div class="floating-card">
                            <span>Reporting</span>
                            <h3>Audit Exports</h3>
                            <p>CSV and Excel outputs for leadership and operations reviews.</p>
                        </div>
                    </div>
                </div>
                <div class="security-strip">
                    <div class="security-pill">Encrypted password storage</div>
                    <div class="security-pill">Database-backed analytics</div>
                    <div class="security-pill">Executive-grade workflows</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_login_form() -> None:
    st.markdown('<div class="section-label">Secure Access</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='color:white; margin-top:0;'>Sign in to FOA</h2>", unsafe_allow_html=True)
    st.caption("Authenticate to open your enterprise analytics workspace.")

    show_password = st.checkbox("Show password", key="login_show_password")
    password_type = "default" if show_password else "password"

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username or email", placeholder="name@company.com")
        password = st.text_input("Password", type=password_type)
        submitted = st.form_submit_button("Authenticate")

    st.caption("Legacy accounts are upgraded to encrypted password storage after successful login.")

    if not submitted:
        return

    username = normalize_username(username)
    if not username or not password:
        notify("Missing credentials", "Enter both username and password.", "warning")
        return

    if st.session_state.auth_failures >= 5:
        notify("Access temporarily locked", "Too many failed attempts in this session. Refresh the app or contact your administrator.", "error")
        return

    with st.spinner("Verifying secure credentials..."):
        user = get_user(username)

    if user and verify_password(password, user.password):
        if not is_hashed_password(user.password):
            migrate_legacy_password(username, password)
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.edit_mode = False
        st.session_state.auth_failures = 0
        st.session_state.last_login = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.last_activity = datetime.now().isoformat(timespec="seconds")
        notify("Authentication successful", "Opening your secure analytics workspace.", "success")
        st.rerun()

    st.session_state.auth_failures += 1
    notify("Authentication failed", "Invalid credentials. Please verify your account details.", "error")


def render_signup_form() -> None:
    st.markdown('<div class="section-label">Enterprise Onboarding</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='color:white; margin-top:0;'>Create workspace</h2>", unsafe_allow_html=True)
    st.caption("Provision a secure analytics profile for your organization.")

    show_password = st.checkbox("Show password", key="signup_show_password")
    password_type = "default" if show_password else "password"

    with st.form("signup_form", clear_on_submit=False):
        username = st.text_input("Business email or username", placeholder="analyst@company.com")
        password = st.text_input("Password", type=password_type)
        if password:
            render_password_strength(password)
        company = st.text_input("Company name")
        role = st.text_input("Role")
        department = st.text_input("Department")
        location = st.text_input("Location")
        submitted = st.form_submit_button("Create Secure Account")

    if not submitted:
        return

    username = normalize_username(username)
    required_values = [username, company.strip(), role.strip(), department.strip(), location.strip()]
    issues = validate_account_fields(username, password, require_password=True)

    if not all(required_values):
        issues.append("Complete all company and profile fields.")

    if issues:
        notify("Account validation failed", " ".join(issues), "warning")
        return

    with st.spinner("Provisioning secure enterprise workspace..."):
        if get_user(username):
            notify("Duplicate account", "An account with this username already exists.", "error")
            return
        create_user(username, password, company, role, location, department)

    notify("Workspace created", "Enterprise account created. Sign in to open your analytics workspace.", "success")


def render_auth_gate() -> None:
    left, right = st.columns([1.12, 0.88], gap="large")

    with left:
        render_auth_visual()

    with right:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        auth = st.radio(
            "Authentication mode",
            ["Login", "Create Account"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if auth == "Login":
            render_login_form()
        else:
            render_signup_form()
        st.markdown("</div>", unsafe_allow_html=True)



# =====================================================
# DASHBOARD PAGE
# =====================================================

def render_dashboard() -> None:
    render_page_header(
        APP_TITLE,
        "Database-driven customer risk intelligence for retention, exposure, and operational forecasting.",
        "Executive Command Center",
    )

    with st.spinner("Loading live enterprise analytics..."):
        all_predictions = get_all_predictions()
        history_df = predictions_to_dataframe(all_predictions)
        metrics = get_dashboard_metrics(history_df)
        trend_df = build_monthly_trend(history_df)
        forecast = build_forecast_summary(trend_df)

    st.markdown(
        f"""
        <div class="card" style="margin-bottom:1.3rem;">
            <div class="section-label">Live Workspace</div>
            <h2 style="color:white; margin:0 0 0.4rem;">Welcome back, {sanitize(st.session_state.username)}</h2>
            <p class="subtitle">
                FOA is monitoring saved predictions, churn probability, retention posture,
                and revenue exposure from your operational history.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Model Runs", f"{metrics['total_predictions']:,}", f"{metrics['model_runs_30d']} in last 30 days")
    with col2:
        render_metric_card("Retention Probability", f"{metrics['retention_rate']:.1f}%", "Mean of saved predictions")
    with col3:
        render_metric_card("High Risk Accounts", f"{metrics['high_risk_count']:,}", "Priority retention queue")
    with col4:
        render_metric_card("Revenue Exposure", f"${metrics['revenue_exposure']:,.0f}", "Total charges under analysis")

    st.write("")
    chart_col1, chart_col2, chart_col3 = st.columns(3, gap="large")

    with chart_col1:
        if history_df.empty:
            render_empty_state("Retention analytics pending", "Run predictions to generate live retention distribution.")
        else:
            retention_df = pd.DataFrame(
                {
                    "Category": ["Expected Retained", "At Risk"],
                    "Share": [
                        history_df["Retention Probability"].mean(),
                        history_df["Probability"].mean(),
                    ],
                }
            )
            fig = px.pie(
                retention_df,
                names="Category",
                values="Share",
                hole=0.68,
                title="Retention Probability Mix",
                color="Category",
                color_discrete_map={"Expected Retained": "#10B981", "At Risk": "#EF4444"},
            )
            fig.update_traces(textinfo="percent", marker=dict(line=dict(color="#050816", width=2)))
            st.plotly_chart(plotly_layout(fig), use_container_width=True)

    with chart_col2:
        if trend_df.empty:
            render_empty_state("Trend analytics pending", "Trend forecasting activates once prediction dates are available.")
        else:
            fig = px.line(
                trend_df,
                x="Month",
                y="Predictions",
                markers=True,
                title="Prediction Volume Trend",
            )
            fig.update_traces(line=dict(color="#38BDF8", width=4), marker=dict(size=9))
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor="rgba(148, 163, 184, 0.18)")
            st.plotly_chart(plotly_layout(fig), use_container_width=True)

    with chart_col3:
        if history_df.empty:
            render_empty_state("Risk distribution pending", "Risk segmentation appears after the first saved prediction.")
        else:
            risk_counts = history_df["Risk"].value_counts().reindex(RISK_ORDER, fill_value=0)
            risk_df = pd.DataFrame({"Risk": risk_counts.index, "Accounts": risk_counts.values})
            fig = px.bar(
                risk_df,
                x="Risk",
                y="Accounts",
                title="Risk Distribution",
                color="Risk",
                color_discrete_map=RISK_COLORS,
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor="rgba(148, 163, 184, 0.18)")
            st.plotly_chart(plotly_layout(fig), use_container_width=True)

    st.subheader("Financial Exposure Intelligence")
    if trend_df.empty:
        render_empty_state("Exposure trend pending", "Saved prediction history will populate revenue exposure analytics.")
    else:
        exposure_fig = px.area(
            trend_df,
            x="Month",
            y="Revenue Exposure",
            title="Revenue Exposure Under Churn Analysis",
        )
        exposure_fig.update_traces(line=dict(color="#38BDF8", width=3), fillcolor="rgba(59, 130, 246, 0.22)")
        st.plotly_chart(plotly_layout(exposure_fig, height=380), use_container_width=True)

    render_executive_insights(metrics, forecast)


def render_executive_insights(metrics: dict, forecast: dict) -> None:
    if metrics["total_predictions"] == 0:
        risk_summary = "No saved predictions yet. Run the AI model to activate executive intelligence."
        retention_summary = "Retention baseline is not established until prediction history exists."
    else:
        risk_summary = (
            f"{metrics['high_risk_count']} of {metrics['total_predictions']} analyzed accounts "
            "are classified as high risk."
        )
        retention_summary = (
            f"Average retention probability is {metrics['retention_rate']:.1f}% "
            f"with {metrics['avg_confidence']:.1f}% mean model confidence."
        )

    left_panel, right_panel = st.columns([2, 1], gap="large")
    with left_panel:
        st.markdown(
            f"""
            <div class="card">
                <h2 style="color:white; margin-top:0;">Executive AI Insights</h2>
                <div class="insight-item">
                    <h4>Retention Intelligence</h4>
                    <p>{sanitize(retention_summary)}</p>
                </div>
                <div class="insight-item">
                    <h4>Risk Concentration</h4>
                    <p>{sanitize(risk_summary)}</p>
                </div>
                <div class="insight-item">
                    <h4>Forecast Signal</h4>
                    <p>{sanitize(forecast["direction"])} Next-period volume forecast: {forecast["next_volume"]} prediction records.</p>
                </div>
                <div class="insight-item">
                    <h4>Operating Recommendation</h4>
                    <p>Prioritize high-risk accounts first, then review medium-risk accounts with elevated monthly exposure.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_panel:
        st.markdown(
            f"""
            <div class="card">
                <h2 style="color:white; margin-top:0;">System Status</h2>
                <p><span class="status-dot" style="background:#22C55E;color:#22C55E;"></span>Database connected</p>
                <p><span class="status-dot" style="background:#3B82F6;color:#3B82F6;"></span>Model loaded</p>
                <p><span class="status-dot" style="background:#F59E0B;color:#F59E0B;"></span>{metrics['total_predictions']} audit records</p>
                <p><span class="status-dot" style="background:#A855F7;color:#A855F7;"></span>Forecast risk {forecast['next_risk']:.1%}</p>
                <hr style="border:1px solid rgba(148,163,184,0.18);">
                <p class="subtitle">Operational analytics are generated from live prediction history only.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =====================================================
# PREDICT CHURN PAGE
# =====================================================

def render_predict_churn(model) -> None:
    render_page_header(
        "Enterprise AI Prediction Workstation",
        "Score customer churn exposure, persist audit records, and generate retention action guidance.",
        "Prediction Engine",
    )

    st.markdown(
        """
        <div class="card" style="margin-bottom:1rem;">
            <div class="section-label">Model Input Console</div>
            <p class="subtitle">Enter customer billing and tenure signals. The model maps these inputs into its trained feature space.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("prediction_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            tenure = st.slider("Customer tenure", 0, 72, 12)
        with col2:
            monthly_charges = st.number_input("Monthly charges", min_value=0.0, max_value=200.0, value=70.0)
        with col3:
            total_charges = st.number_input("Total charges", min_value=0.0, max_value=10000.0, value=1000.0)

        submitted = st.form_submit_button("Run AI Risk Analysis")

    if not submitted:
        return

    if total_charges < monthly_charges and tenure > 1:
        notify("Billing validation warning", "Total charges are lower than monthly charges for this tenure. Review the billing input if this is unexpected.", "warning")

    try:
        with st.spinner("Running secured AI churn intelligence workflow..."):
            input_data = build_prediction_frame(model, tenure, monthly_charges, total_charges)
            prediction = int(model.predict(input_data)[0])
            probability = float(model.predict_proba(input_data)[0][1])
            risk = classify_risk(probability)
            confidence = confidence_score(probability)
            save_prediction(st.session_state.username, tenure, monthly_charges, total_charges, probability, risk)
    except Exception as exc:
        notify("Prediction failed", str(exc), "error")
        return

    metric1, metric2, metric3, metric4 = st.columns(4)
    with metric1:
        render_metric_card("Churn Probability", f"{probability:.2%}", "Model risk score")
    with metric2:
        render_metric_card("Risk Level", risk, "Retention priority")
    with metric3:
        render_metric_card("Retention Score", f"{(1 - probability):.2%}", "Probability of staying")
    with metric4:
        render_metric_card("Confidence", f"{confidence:.2%}", "Decision confidence")

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=probability * 100,
                title={"text": "Enterprise Churn Risk Score"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": RISK_COLORS[risk]},
                    "steps": [
                        {"range": [0, 40], "color": "rgba(16, 185, 129, 0.42)"},
                        {"range": [40, 70], "color": "rgba(245, 158, 11, 0.42)"},
                        {"range": [70, 100], "color": "rgba(239, 68, 68, 0.42)"},
                    ],
                },
            )
        )
        st.plotly_chart(plotly_layout(gauge, height=430), use_container_width=True)

    with right:
        outcome = "likely to churn" if prediction == 1 else "likely to stay"
        st.markdown(
            f"""
            <div class="card">
                <div class="section-label">Decision Intelligence</div>
                <h2 style="color:white; margin-top:0;">Customer is {sanitize(outcome)}</h2>
                <p class="subtitle">Prediction saved to the audit history for reporting and trend analysis.</p>
                <hr style="border:1px solid rgba(148,163,184,0.18);">
                <div class="recommendation-card">
                    <h4 style="color:white; margin-top:0;">Recommended Action</h4>
                    <p class="subtitle">{sanitize(recommendation_for_risk(risk, probability))}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =====================================================
# HISTORY PAGE
# =====================================================

def render_prediction_history() -> None:
    render_page_header(
        "Enterprise Reporting and Audit Center",
        "Filter prediction records, inspect risk exposure, and export operational analytics.",
        "Saved Intelligence",
    )

    with st.spinner("Loading audit-ready prediction history..."):
        user_history = get_prediction_history(st.session_state.username)
        df = predictions_to_dataframe(user_history)

    if df.empty:
        render_empty_state(
            "No prediction history available",
            "Run a churn prediction to start building the reporting ledger, executive trends, and exportable audit trail.",
            "Run First Prediction",
        )
        if st.button("Run First Prediction"):
            st.session_state.nav_override = "Predict Churn"
            st.rerun()
        return

    filters = st.columns([1, 1, 1])
    with filters[0]:
        risk_filter = st.multiselect("Risk segment", RISK_ORDER, default=RISK_ORDER)
    with filters[1]:
        min_probability = st.slider("Minimum churn probability", 0, 100, 0)
    with filters[2]:
        sort_direction = st.selectbox("Sort order", ["Newest first", "Highest risk first", "Largest exposure first"])

    filtered_df = df[df["Risk"].isin(risk_filter)].copy()
    filtered_df = filtered_df[filtered_df["Probability"] >= min_probability / 100]

    if sort_direction == "Highest risk first":
        filtered_df = filtered_df.sort_values("Probability", ascending=False)
    elif sort_direction == "Largest exposure first":
        filtered_df = filtered_df.sort_values("Total Charges", ascending=False)
    else:
        filtered_df = filtered_df.sort_values("Date", ascending=False, na_position="last")

    metrics = get_dashboard_metrics(filtered_df)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Filtered Records", f"{len(filtered_df):,}", "Current reporting view")
    with col2:
        render_metric_card("Average Churn Risk", f"{metrics['avg_probability']:.1%}", "Mean probability")
    with col3:
        render_metric_card("High Risk Records", f"{metrics['high_risk_count']:,}", "Priority segment")
    with col4:
        render_metric_card("Revenue Exposure", f"${metrics['revenue_exposure']:,.0f}", "Total charges")

    display_df = filtered_df.copy()
    display_df["Date"] = display_df["Date"].astype(str)
    display_df["Probability"] = display_df["Probability"].map(lambda value: f"{value:.2%}")
    display_df["Retention Probability"] = display_df["Retention Probability"].map(lambda value: f"{value:.2%}")
    display_df["Confidence"] = display_df["Confidence"].map(lambda value: f"{value:.2%}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button(
            "Download CSV Report",
            csv,
            file_name="prediction_history.csv",
            mime="text/csv",
        )
    with export_col2:
        try:
            excel_bytes = dataframe_to_excel_bytes(filtered_df)
            st.download_button(
                "Download Excel Report",
                excel_bytes,
                file_name="enterprise_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as exc:
            notify("Excel export unavailable", str(exc), "warning")

    chart_col1, chart_col2 = st.columns(2, gap="large")
    with chart_col1:
        risk_counts = filtered_df["Risk"].value_counts().reindex(RISK_ORDER, fill_value=0)
        risk_df = pd.DataFrame({"Risk": risk_counts.index, "Records": risk_counts.values})
        fig = px.bar(
            risk_df,
            x="Risk",
            y="Records",
            title="Risk Segment Distribution",
            color="Risk",
            color_discrete_map=RISK_COLORS,
        )
        st.plotly_chart(plotly_layout(fig, height=380), use_container_width=True)

    with chart_col2:
        trend_df = build_monthly_trend(filtered_df)
        if trend_df.empty:
            render_empty_state("Trend unavailable", "No dated records match the active filters.")
        else:
            fig = px.line(
                trend_df,
                x="Month",
                y="Average Churn Risk",
                title="Average Churn Risk Trend",
                markers=True,
            )
            fig.update_traces(line=dict(color="#38BDF8", width=4), marker=dict(size=9))
            fig.update_yaxes(tickformat=".0%", gridcolor="rgba(148, 163, 184, 0.18)")
            st.plotly_chart(plotly_layout(fig, height=380), use_container_width=True)


# =====================================================
# PROFILE PAGE
# =====================================================

def render_account_profile(current_user) -> None:
    render_page_header(
        "Enterprise Account Center",
        "Manage identity, security, workspace ownership, and prediction activity.",
        "User Workspace",
    )

    user_history = get_prediction_history(current_user.username)
    history_df = predictions_to_dataframe(user_history)
    metrics = get_dashboard_metrics(history_df)

    col1, col2 = st.columns([8, 1])
    with col1:
        initial = sanitize((current_user.username or "U")[0].upper())
        st.markdown(
            f"""
            <div class="profile-card" style="padding:1.5rem;">
                <div style="display:flex; align-items:center; gap:1.2rem; flex-wrap:wrap;">
                    <div style="
                        width:86px; height:86px; border-radius:50%;
                        background:linear-gradient(135deg,#2563EB,#0EA5E9);
                        display:flex; align-items:center; justify-content:center;
                        font-size:2rem; color:white; font-weight:850;">
                        {initial}
                    </div>
                    <div>
                        <div class="section-label">Verified Enterprise Identity</div>
                        <h2 style="color:white; margin:0;">{sanitize(current_user.username)}</h2>
                        <p class="subtitle">{sanitize(current_user.role or "Enterprise User")}</p>
                        <p style="color:#60A5FA; margin:0.25rem 0 0;">{sanitize(current_user.company or "Financial Operations")}</p>
                    </div>
                </div>
                <hr style="border:1px solid rgba(148,163,184,0.18); margin:1.4rem 0;">
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem;">
                    <div><p style="color:#94A3B8; margin:0;">Department</p><h3 style="color:white; margin:0.25rem 0;">{sanitize(current_user.department or "Not set")}</h3></div>
                    <div><p style="color:#94A3B8; margin:0;">Location</p><h3 style="color:white; margin:0.25rem 0;">{sanitize(current_user.location or "Not set")}</h3></div>
                    <div><p style="color:#94A3B8; margin:0;">Credential Storage</p><h3 style="color:white; margin:0.25rem 0;">{"PBKDF2 Secured" if is_hashed_password(current_user.password) else "Legacy - upgrades on login"}</h3></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        if st.button("Edit"):
            st.session_state.edit_mode = True
            st.rerun()

    metric1, metric2, metric3, metric4 = st.columns(4)
    with metric1:
        render_metric_card("Predictions Generated", f"{metrics['total_predictions']:,}", "Workspace activity")
    with metric2:
        render_metric_card("Retention Probability", f"{metrics['retention_rate']:.1f}%", "Account history average")
    with metric3:
        render_metric_card("High Risk Cases", f"{metrics['high_risk_count']:,}", "Saved records")
    with metric4:
        render_metric_card("Monthly Exposure", f"${metrics['monthly_exposure']:,.0f}", "Billing under analysis")

    if st.session_state.edit_mode:
        render_profile_form(current_user)


def render_profile_form(current_user) -> None:
    st.subheader("Edit Account Details")
    st.caption("Leave the password field blank to keep the current credential.")

    with st.form("profile_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            updated_username = st.text_input("Username / email", value=current_user.username or "")
            updated_company = st.text_input("Company name", value=current_user.company or "")
            updated_role = st.text_input("Role", value=current_user.role or "")
            updated_department = st.text_input("Department", value=current_user.department or "")
        with col2:
            updated_location = st.text_input("Location", value=current_user.location or "")
            updated_password = st.text_input("New password", value="", type="password")
            if updated_password:
                render_password_strength(updated_password)

        save_col, cancel_col = st.columns(2)
        with save_col:
            save_changes = st.form_submit_button("Save Secure Profile")
        with cancel_col:
            cancel = st.form_submit_button("Cancel")

    if cancel:
        st.session_state.edit_mode = False
        st.rerun()

    if not save_changes:
        return

    values = {
        "username": normalize_username(updated_username),
        "company": updated_company.strip(),
        "role": updated_role.strip(),
        "department": updated_department.strip(),
        "location": updated_location.strip(),
        "password": updated_password.strip(),
    }

    issues = validate_account_fields(values["username"], values["password"], require_password=False)
    if not all([values["username"], values["company"], values["role"], values["department"], values["location"]]):
        issues.append("All profile identity fields are required.")

    if issues:
        notify("Profile validation failed", " ".join(issues), "warning")
        return

    try:
        with st.spinner("Updating secure account profile..."):
            update_user_profile(current_user.id, current_user.username, values)
        st.session_state.username = values["username"]
        st.session_state.edit_mode = False
        notify("Profile updated", "Account updated successfully.", "success")
        st.rerun()
    except ValueError as exc:
        notify("Profile update blocked", str(exc), "error")
    except Exception as exc:
        notify("Profile update failed", str(exc), "error")


def render_admin_panel(current_user) -> None:
    """Render the enterprise Admin Panel.

    All admin UI logic is contained here. Only users with `role_type == 'Admin'`
    should see this page via the sidebar router.
    """

    render_page_header(
        "Admin Control Center",
        "Manage platform users, monitor analytics activity, and control enterprise-level permissions.",
        "Enterprise Administration",
    )

    # KPI cards
    total_users = get_total_users()
    total_predictions = get_total_predictions()
    high_risk = get_high_risk_predictions()
    admin_count = get_admin_count()

    col1, col2, col3, col4 = st.columns(4, gap="large")
    with col1:
        render_metric_card("Total Users", f"{total_users:,}", "Registered workspace accounts")
    with col2:
        render_metric_card("Total Predictions", f"{total_predictions:,}", "Saved audit records")
    with col3:
        render_metric_card("High Risk Predictions", f"{high_risk:,}", "Priority retention cases")
    with col4:
        render_metric_card("Admin Accounts", f"{admin_count:,}", "Users with admin privileges")

    st.write("")

    # User management section
    st.markdown(
        """
        <div class='section-card'>
            <h2 style='color:white;'>👥 User Management</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    users = get_all_users() or []

    if not users:
        render_empty_state("No users found", "There are no accounts in the workspace yet.")
        render_footer()
        return

    # Render list with actions
    for user in users:
        with st.container():
            col_u, col_r, col_d, col_action, col_delete = st.columns([3, 1.5, 1.5, 1.3, 1.3])

            with col_u:
                st.markdown(
                    f"""
                    <div class='glass-card'>
                        <b>{sanitize(user.username)}</b><br>
                        {sanitize(user.company or 'No Company')}<br>
                        <span style='color:#38BDF8;'>{sanitize(user.role_type)}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_r:
                st.write(sanitize(user.role or ""))

            with col_d:
                st.write(sanitize(user.department or ""))

            # Promote / Demote
            with col_action:
                if user.id == current_user.id:
                    st.caption("(You)")
                if user.role_type != "Admin":
                    if st.button("Promote", key=f"promote_{user.id}"):
                        promote_to_admin(user.id)
                        st.success("User promoted to Admin")
                        st.rerun()
                else:
                    if user.id != current_user.id:
                        if st.button("Demote", key=f"demote_{user.id}"):
                            demote_to_user(user.id)
                            st.warning("Admin demoted to User")
                            st.rerun()
                    else:
                        st.caption("Cannot demote yourself")

            # Delete action
            with col_delete:
                if user.id != current_user.id:
                    if st.button("Delete", key=f"delete_{user.id}"):
                        deleted = delete_user(user.id)
                        if deleted:
                            st.error("User deleted")
                        else:
                            notify("Delete failed", "Could not delete the selected user.", "error")
                        st.rerun()
                else:
                    st.caption("Cannot delete yourself")

            st.write("---")

    render_footer()


# =====================================================
# APP ROUTER
# =====================================================

def main() -> None:
    initialize_session_state()
    enforce_session_timeout()

    if not st.session_state.logged_in:
        render_auth_gate()
        st.stop()

    current_user = get_user(st.session_state.username)
    if current_user is None:
        st.session_state.logged_in = False
        st.session_state.username = ""
        notify("Session restore failed", "Your session could not be restored. Please log in again.", "warning")
        st.stop()

    try:
        model = load_model()
    except Exception as exc:
        notify("Model unavailable", f"Unable to load prediction model: {exc}", "error")
        st.stop()

    page = render_sidebar(current_user)
    render_app_header(current_user, page)

    if page == "Dashboard":
        render_dashboard()
    elif page == "Predict Churn":
        render_predict_churn(model)
    elif page == "Prediction History":
        render_prediction_history()
    elif page == "Account Profile":
        render_account_profile(current_user)
    elif page == "Admin Panel":
        render_admin_panel(current_user)


if __name__ == "__main__":
    main()
