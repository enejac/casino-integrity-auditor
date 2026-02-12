import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main() -> None:
    # --- Config ---
    n_spins = 100_000
    base_rtp_mean = 0.96          # 96%
    base_rtp_std = 0.15           # normal-distribution noise
    fraud_start = 50_000          # inclusive, 0-based index
    fraud_end = 50_200            # exclusive
    fraud_rtp_mean = 2.00         # 200%
    fraud_rtp_std = 0.20
    bet_per_spin = 1.0

    rolling_window = 500
    anomaly_threshold = 1.10      # 110%

    rng = np.random.default_rng(42)

    # --- Simulate per-spin RTP ratios ---
    rtp_ratio = rng.normal(loc=base_rtp_mean, scale=base_rtp_std, size=n_spins)
    rtp_ratio = np.clip(rtp_ratio, 0, None)  # RTP can't be negative

    # --- Inject fraud window with huge RTP ---
    fraud_len = fraud_end - fraud_start
    fraud_rtp = rng.normal(loc=fraud_rtp_mean, scale=fraud_rtp_std, size=fraud_len)
    fraud_rtp = np.clip(fraud_rtp, 0, None)
    rtp_ratio[fraud_start:fraud_end] = fraud_rtp

    # --- Build data ---
    df = pd.DataFrame(
        {
            "spin": np.arange(1, n_spins + 1),
            "bet": bet_per_spin,
            "payout": bet_per_spin * rtp_ratio,
        }
    )
    df["rtp"] = df["payout"] / df["bet"]

    # Rolling Average RTP (window=500 spins)
    df["rolling_rtp"] = df["rtp"].rolling(window=rolling_window, min_periods=rolling_window).mean()

    # Flag anomalies where Rolling RTP > 110%
    df["anomaly"] = df["rolling_rtp"] > anomaly_threshold

    # --- Plot (in %) ---
    df["rolling_rtp_pct"] = df["rolling_rtp"] * 100.0
    threshold_pct = anomaly_threshold * 100.0

    plt.figure(figsize=(12, 6))
    plt.plot(df["spin"], df["rolling_rtp_pct"], linewidth=1.2, label="Rolling RTP (window=500)")

    # Threshold line at 110%
    plt.axhline(threshold_pct, color="red", linestyle="--", linewidth=2, label="Threshold (110%)")

    # Optional: highlight anomaly points
    anomalies = df[df["anomaly"] & df["rolling_rtp_pct"].notna()]
    if not anomalies.empty:
        plt.scatter(anomalies["spin"], anomalies["rolling_rtp_pct"], s=8, color="red", alpha=0.6, label="ANOMALY")

    plt.title("Rolling RTP Surveillance (Injected Fraud Window)")
    plt.xlabel("Spin")
    plt.ylabel("Rolling RTP (%)")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()

    plt.savefig("anomaly_report.png", dpi=200)
    plt.close()

    # Console summary
    if anomalies.empty:
        print("No anomalies detected (rolling RTP never exceeded 110%).")
    else:
        first_spin = int(anomalies["spin"].iloc[0])
        print(f"Anomalies detected: {len(anomalies)} points. First anomaly at spin {first_spin}.")
        print("Saved plot: anomaly_report.png")


if __name__ == "__main__":
    main()