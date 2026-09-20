from __future__ import annotations

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

F2 = lambda v: f"{v:,.2f}"


def _fig_price(dates, close, title, currency="INR") -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.plot(range(len(close)), close, linewidth=1.2)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("Trading day"); ax.set_ylabel(f"Close ({currency})")
    ax.grid(alpha=0.25)
    buf = io.BytesIO(); fig.tight_layout(); fig.savefig(buf, format="png", dpi=150)
    plt.close(fig); buf.seek(0); return buf


def _fig_regression(close, fitted, currency="INR") -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.scatter(range(len(close)), close, s=6, alpha=0.6, label="Actual")
    ax.plot(range(len(fitted)), fitted, linewidth=1.4, label="Regression")
    ax.legend(fontsize=8); ax.set_xlabel("Trading day (X)"); ax.set_ylabel(f"Close ({currency})")
    ax.grid(alpha=0.25)
    buf = io.BytesIO(); fig.tight_layout(); fig.savefig(buf, format="png", dpi=150)
    plt.close(fig); buf.seek(0); return buf


def _fig_indexed(s_idx, n_idx) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.plot(s_idx, linewidth=1.3, label="Stock (base=100)")
    ax.plot(n_idx, linewidth=1.3, label="NIFTY 50 (base=100)")
    ax.legend(fontsize=8); ax.set_xlabel("Trading day"); ax.set_ylabel("Indexed value")
    ax.grid(alpha=0.25)
    buf = io.BytesIO(); fig.tight_layout(); fig.savefig(buf, format="png", dpi=150)
    plt.close(fig); buf.seek(0); return buf


def build_pdf(bundle: dict) -> bytes:
    buf = io.BytesIO()
    ccy = bundle.get("currency", "INR")
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    el: list = []
    s, n, r, p, h = (bundle["statistics"], bundle["nifty_statistics"], bundle["regression"],
                     bundle["probability"], bundle["hypothesis"])
    el += [Paragraph("STATISTICS AND PROBABILITY ANALYSIS", styles["Title"]),
           Paragraph(f"{bundle['stock_name']} ({bundle['symbol']}) — {bundle['start']} to {bundle['end']}", styles["Normal"]),
           Paragraph(f"Data source: {bundle['provider']}. Retrieved: {bundle['retrieved_at']}. Observations: {bundle['n']} trading days.", styles["Normal"]),
           Spacer(1, 6)]

    def stat_table(d: dict, title: str):
        rows = [["Metric", "Value"]] + [
            ["n", str(d["n"])], ["Mean", F2(d["mean"])], ["Median", F2(d["median"])],
            ["Mode", F2(d["mode"])], ["Min", F2(d["min"])], ["Max", F2(d["max"])],
            ["Range", F2(d["range"])], ["Variance (sample)", F2(d["variance_sample"])],
            ["Std dev (sample)", F2(d["std_sample"])],
            ["Q1/Q2/Q3", f"{F2(d['q1'])} / {F2(d['q2'])} / {F2(d['q3'])}"],
            ["IQR", F2(d["iqr"])], ["CV", f"{d['cv_percent']:.2f}%"]]
        t = Table(rows, colWidths=[70 * mm, 70 * mm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111113")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        return [Paragraph(title, styles["Heading2"]), t, Spacer(1, 6)]

    el += [Paragraph("1. Descriptive statistics (sample statistics, ddof=1; price field = Close)", styles["Heading1"])]
    el += stat_table(s, "Stock")
    el += stat_table(n, "NIFTY 50")
    el.append(Paragraph(f"CV = s/x̄ × 100. Stock CV = {s['cv_percent']:.2f}% (mean {F2(s['mean'])}, s {F2(s['std_sample'])}). "
                        f"NIFTY CV = {n['cv_percent']:.2f}%. Lower CV = lower relative dispersion. Academic comparison only — not investment advice.", styles["Normal"]))
    el.append(Image(_fig_indexed(bundle["indexed_stock"], bundle["indexed_nifty"]), width=150 * mm, height=58 * mm))
    el += [Paragraph("2. Regression of price on trading day", styles["Heading1"]),
           Paragraph(f"X = trading-day number (1..{r['n']}), Y = close. {r['equation']}; R² = {r['r_squared']:.4f}; r = {r['r']:.4f}; SE(estimate) = {r['std_err_estimate']:.4f}.", styles["Normal"])]
    el.append(Image(_fig_regression(bundle["close"], r["fitted"], ccy), width=150 * mm, height=58 * mm))
    el.append(Image(_fig_price(bundle["dates"], bundle["close"], f"Historical closing price ({ccy})", ccy), width=150 * mm, height=58 * mm))
    el += [Paragraph("3. Probability (one-week horizon)", styles["Heading1"]),
           Paragraph(f"Method: {p['method']} Observations={p['observations']}, positive={p['positive']}, negative={p['negative']}, flat={p['flat']}. "
                     f"P(increase)={p['p_positive']:.4f}, P(decrease)={p['p_negative']:.4f}, P(flat)={p['p_flat']:.4f}. Historical estimate only — not a prediction.", styles["Normal"]),
           Paragraph("4. Hypothesis test (one-sample t-test)", styles["Heading1"]),
           Paragraph(f"H0: μ = {h['mu0']}, H1: μ {'≠' if h['alternative']=='two-sided' else '>' if h['alternative']=='greater' else '<'} {h['mu0']}; α = {h['alpha']}. "
                     f"t = {h['t_statistic']:.4f}, p = {h['p_value']:.6f}, critical = {h['critical_value']:.4f}, df = {h['df']}. Decision: {h['decision']}.", styles["Normal"]),
           Paragraph("5. Conclusion", styles["Heading1"]),
           Paragraph("All figures are computed deterministically from fetched OHLCV data (sample statistics). "
                     "Academic analysis only. This application is not investment advice and statistical results do not guarantee future market performance.", styles["Normal"])]
    doc.build(el)
    return buf.getvalue()
