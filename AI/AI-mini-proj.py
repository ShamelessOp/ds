import tkinter as tk
from tkinter import messagebox, scrolledtext
import yfinance as yf


class StockExpertSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Expert System: Stock Market Trader")
        # Increased height slightly to accommodate the footer
        self.root.geometry("600x580")
        self.root.configure(padx=20, pady=20, bg="#f4f4f9")

        # --- Fonts & Styles ---
        self.title_font = ("Helvetica", 16, "bold")
        self.label_font = ("Helvetica", 12)
        self.text_font = ("Consolas", 11)
        self.footer_font = ("Helvetica", 9, "italic")

        # --- UI Elements ---
        tk.Label(root, text="Rule-Based Stock Trading Expert System", font=self.title_font, bg="#f4f4f9").pack(
            pady=(0, 15))

        # Input Frame
        input_frame = tk.Frame(root, bg="#f4f4f9")
        input_frame.pack(fill="x", pady=5)

        tk.Label(input_frame, text="Enter Stock Ticker (e.g., TCS.NS, AAPL):", font=self.label_font, bg="#f4f4f9").pack(
            side="left")

        self.ticker_entry = tk.Entry(input_frame, font=self.label_font, width=15)
        self.ticker_entry.insert(0, "TCS.NS")  # Default to Indian market stock
        self.ticker_entry.pack(side="left", padx=10)

        self.analyze_btn = tk.Button(input_frame, text="Analyze Live Data", font=self.label_font, bg="#4CAF50",
                                     fg="white", command=self.run_analysis)
        self.analyze_btn.pack(side="left", padx=5)

        # Output Display
        tk.Label(root, text="Expert System Analysis & Reasoning:", font=self.label_font, bg="#f4f4f9").pack(anchor="w",
                                                                                                            pady=(15,
                                                                                                                  5))

        self.output_area = scrolledtext.ScrolledText(root, font=self.text_font, width=65, height=18, bg="#ffffff",
                                                     state='disabled')
        self.output_area.pack(fill="both", expand=True, pady=(0, 10))

        # --- Team Footer ---
        team_names = "Project By: Prathamesh Tikle | Bhavesh Patil | Sakshi Yadav | Siddhi Wani | Aakanksha Zope"
        tk.Label(root, text=team_names, font=self.footer_font, bg="#f4f4f9", fg="#555555").pack(side="bottom")

    def calculate_rsi(self, data, periods=14):
        """Calculates the Relative Strength Index (RSI)."""
        close_delta = data['Close'].diff()

        up = close_delta.clip(lower=0)
        down = -1 * close_delta.clip(upper=0)

        ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
        ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()

        rs = ma_up / ma_down
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def log_output(self, message):
        """Helper to write to the GUI text area."""
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, message + "\n")
        self.output_area.see(tk.END)
        self.output_area.config(state='disabled')

    def run_analysis(self):
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            messagebox.showwarning("Input Error", "Please enter a stock ticker.")
            return

        self.output_area.config(state='normal')
        self.output_area.delete(1.0, tk.END)
        self.output_area.config(state='disabled')

        self.log_output(f"[*] Fetching live data for {ticker} from Yahoo Finance...")
        self.root.update()

        try:
            # Fetch 1 year of data to calculate Moving Averages properly
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")

            if df.empty:
                self.log_output(f"[!] Error: Could not retrieve data for {ticker}. Check the symbol.")
                return

            self.log_output("[*] Data fetched successfully. Calculating technical indicators...")

            # Calculate Indicators
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = self.calculate_rsi(df)

            # Get latest values
            latest = df.iloc[-1]
            current_price = latest['Close']
            sma_50 = latest['SMA_50']
            sma_200 = latest['SMA_200']
            rsi = latest['RSI']

            self.log_output("-" * 50)
            self.log_output(f"CURRENT METRICS FOR {ticker}:")
            self.log_output(
                f"Current Price: ₹{current_price:.2f}" if ".NS" in ticker or ".BO" in ticker else f"Current Price: ${current_price:.2f}")
            self.log_output(f"50-Day Moving Average: {sma_50:.2f}")
            self.log_output(f"200-Day Moving Average: {sma_200:.2f}")
            self.log_output(f"RSI (14-Day): {rsi:.2f}")
            self.log_output("-" * 50)

            # ---------------------------------------------------------
            # EXPERT SYSTEM KNOWLEDGE BASE (RULES ENGINE)
            # ---------------------------------------------------------
            self.log_output("\n[*] Triggering Inference Engine...")
            decision = "HOLD"
            reasoning = []

            # Rule 1: Extreme Oversold
            if rsi < 30:
                decision = "STRONG BUY"
                reasoning.append("RSI is below 30, indicating the stock is heavily oversold and undervalued.")

            # Rule 2: Extreme Overbought
            elif rsi > 70:
                decision = "STRONG SELL"
                reasoning.append(
                    "RSI is above 70, indicating the stock is overbought and a price correction is likely.")

            # Rule 3: Golden Cross (Uptrend)
            elif sma_50 > sma_200:
                decision = "BUY"
                reasoning.append(
                    "50-day SMA is above 200-day SMA (Golden Cross), indicating a long-term bullish upward trend.")
                if rsi > 60:
                    reasoning.append("However, RSI is getting high. Buy with caution.")

            # Rule 4: Death Cross (Downtrend)
            elif sma_50 < sma_200:
                decision = "SELL"
                reasoning.append(
                    "50-day SMA is below 200-day SMA (Death Cross), indicating a long-term bearish downward trend.")

            # Rule 5: Default state
            else:
                reasoning.append("Indicators do not show a strong trend. Market is consolidating.")

            # Print Decision
            self.log_output("\n" + "=" * 50)
            self.log_output(f"FINAL DECISION: {decision}")
            self.log_output("=" * 50)
            self.log_output("REASONING:")
            for rule in reasoning:
                self.log_output(f" -> {rule}")

        except Exception as e:
            self.log_output(f"\n[!] An error occurred during analysis: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StockExpertSystem(root)
    root.mainloop()