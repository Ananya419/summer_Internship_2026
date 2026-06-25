import os
import re
import pandas as pd


class DataValidator:
    def __init__(self):
        # We will collect all failures inside a list of dicts
        self.failures = []

    def log_failure(
        self, rule_id, company_id, year, column, value, message, severity="WARNING"
    ):
        """Logs a validation failure."""
        self.failures.append(
            {
                "rule_id": rule_id,
                "company_id": company_id,
                "year": year,
                "column": column,
                "value": str(value),
                "message": message,
                "severity": severity,
            }
        )

    def _check_pk_uniqueness(self, df, pk_col, table_name, rule_id):
        """Helper to verify primary key uniqueness."""
        if pk_col not in df.columns:
            return
        duplicates = df[df.duplicated(subset=[pk_col], keep=False)]
        for idx, row in duplicates.iterrows():
            pk_val = row[pk_col]
            self.log_failure(
                rule_id,
                row.get("company_id", pk_val),
                row.get("year", None),
                pk_col,
                pk_val,
                f"Duplicate primary key {pk_val} in table {table_name}",
                "CRITICAL",
            )

    def _check_composite_pk(self, df, cols, table_name, rule_id):
        """Helper to verify composite unique constraints."""
        missing = [c for c in cols if c not in df.columns]
        if missing:
            return
        duplicates = df[df.duplicated(subset=cols, keep=False)]
        for idx, row in duplicates.iterrows():
            comp_val = "-".join([str(row[c]) for c in cols])
            self.log_failure(
                rule_id,
                row.get("company_id", "UNKNOWN"),
                row.get("year", None),
                str(cols),
                comp_val,
                f"Duplicate composite key {comp_val} in table {table_name}",
                "CRITICAL",
            )

    def run_dq_rules(self, dfs):
        """
        Runs the 16 DQ rules across the tables dataset dict.
        dfs keys: 'companies', 'profitandloss', 'balancesheet', 'cashflow', 'analysis', 'documents', 'prosandcons', 'sectors', 'stock_prices', 'financial_ratios', 'peer_groups'
        """
        # --- DQ-01: Primary Key Uniqueness ---
        self._check_pk_uniqueness(dfs["companies"], "id", "companies", "DQ-01")
        self._check_pk_uniqueness(dfs["peer_groups"], "id", "peer_groups", "DQ-01")
        self._check_pk_uniqueness(dfs["sectors"], "id", "sectors", "DQ-01")
        self._check_pk_uniqueness(dfs["stock_prices"], "id", "stock_prices", "DQ-01")

        # --- DQ-02: Composite Key (company_id, year) Unique ---
        self._check_composite_pk(
            dfs["profitandloss"], ["company_id", "year"], "profitandloss", "DQ-02"
        )
        self._check_composite_pk(
            dfs["balancesheet"], ["company_id", "year"], "balancesheet", "DQ-02"
        )
        self._check_composite_pk(
            dfs["cashflow"], ["company_id", "year"], "cashflow", "DQ-02"
        )
        self._check_composite_pk(
            dfs["financial_ratios"], ["company_id", "year"], "financial_ratios", "DQ-02"
        )
        self._check_composite_pk(
            dfs["market_cap"], ["company_id", "year"], "market_cap", "DQ-02"
        )

        # --- DQ-03: Foreign Key Integrity (Checks company_id matches companies.id) ---
        valid_companies = set(dfs["companies"]["id"].dropna().unique())
        for table_name in [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
            "sectors",
            "peer_groups",
            "documents",
            "prosandcons",
            "stock_prices",
        ]:
            df = dfs[table_name]
            if "company_id" in df.columns:
                for idx, row in df.iterrows():
                    comp = row["company_id"]
                    if pd.notna(comp) and comp not in valid_companies:
                        self.log_failure(
                            "DQ-03",
                            comp,
                            row.get("year", None),
                            "company_id",
                            comp,
                            f"Foreign Key violation in table {table_name}: company does not exist in master list",
                            "CRITICAL",
                        )

        # --- DQ-04: Balance Sheet assets vs liabilities balance check (<1% tolerance) ---
        bs_df = dfs["balancesheet"]
        for idx, row in bs_df.iterrows():
            comp = row["company_id"]
            yr = row["year"]
            equity = row.get("equity_capital", 0)
            reserves = row.get("reserves", 0)
            borrowings = row.get("borrowings", 0)
            liabilities = row.get("other_liabilities", 0)

            fixed = row.get("fixed_assets", 0)
            cwip = row.get("cwip", 0)
            investments = row.get("investments", 0)
            other_assets = row.get("other_asset", 0)

            total_l = row.get(
                "total_liabilities", equity + reserves + borrowings + liabilities
            )
            total_a = row.get("total_assets", fixed + cwip + investments + other_assets)

            # Recalculate components to cross-verify sheet sums
            calc_l = (
                float(equity) + float(reserves) + float(borrowings) + float(liabilities)
            )
            calc_a = (
                float(fixed) + float(cwip) + float(investments) + float(other_assets)
            )

            abs(total_l - calc_l)
            abs(total_a - calc_a)
            diff_net = abs(total_l - total_a)

            # Check if assets equal liabilities (within 1% tolerance of total assets)
            if total_a > 0 and (diff_net / total_a) > 0.01:
                self.log_failure(
                    "DQ-04",
                    comp,
                    yr,
                    "total_assets",
                    total_a,
                    f"Balance sheet equation mismatch: total assets {total_a} vs total liabilities {total_l}",
                    "WARNING",
                )

        # --- DQ-05: OPM (Operating Profit Margin) cross-check ---
        pl_df = dfs["profitandloss"]
        for idx, row in pl_df.iterrows():
            comp = row["company_id"]
            yr = row["year"]
            sales = row.get("sales", 0)
            expenses = row.get("expenses", 0)
            op = row.get("operating_profit", 0)
            opm = row.get("opm_percentage", 0)

            # Sales - Expenses must equal Operating Profit
            calc_op = float(sales) - float(expenses)
            if abs(op - calc_op) > 2.0:  # Allow slight rounding tolerance of 2 Cr
                self.log_failure(
                    "DQ-05",
                    comp,
                    yr,
                    "operating_profit",
                    op,
                    f"OPM calculation discrepancy: sales {sales} - expenses {expenses} = {calc_op} (Excel shows {op})",
                    "WARNING",
                )

            # Check margin percentage
            if sales > 0:
                calc_opm = (op / sales) * 100
                if abs(opm - calc_opm) > 1.5:
                    self.log_failure(
                        "DQ-05",
                        comp,
                        yr,
                        "opm_percentage",
                        opm,
                        f"OPM % mismatch: calculated {calc_opm:.2f}% vs sheet {opm}%",
                        "WARNING",
                    )

        # --- DQ-06: Positive Sales Check ---
        for idx, row in pl_df.iterrows():
            comp = row["company_id"]
            yr = row["year"]
            sales = row.get("sales", 0)
            if pd.notna(sales) and sales < 0:
                self.log_failure(
                    "DQ-06",
                    comp,
                    yr,
                    "sales",
                    sales,
                    f"Negative sales reported: {sales}",
                    "CRITICAL",
                )

        # --- DQ-07: Cash Flow Statement Net Cash Check ---
        cf_df = dfs["cashflow"]
        for idx, row in cf_df.iterrows():
            comp = row["company_id"]
            yr = row["year"]
            op_cf = row.get("operating_activity", 0)
            inv_cf = row.get("investing_activity", 0)
            fin_cf = row.get("financing_activity", 0)
            net_cf = row.get("net_cash_flow", 0)

            calc_net = float(op_cf) + float(inv_cf) + float(fin_cf)
            if abs(net_cf - calc_net) > 2.0:
                self.log_failure(
                    "DQ-07",
                    comp,
                    yr,
                    "net_cash_flow",
                    net_cf,
                    f"Net cash flow {net_cf} does not equal sum of operations, investing, and financing ({calc_net})",
                    "WARNING",
                )

        # --- DQ-08: Tax Rate limit check (<100%) ---
        for idx, row in pl_df.iterrows():
            comp = row["company_id"]
            yr = row["year"]
            tax = row.get("tax_percentage", 0)
            if pd.notna(tax) and (tax < 0 or tax > 100):
                self.log_failure(
                    "DQ-08",
                    comp,
                    yr,
                    "tax_percentage",
                    tax,
                    f"Tax rate out of bounds (0-100%): {tax}%",
                    "WARNING",
                )

        # --- DQ-09: Dividend Payout percentage validation ---
        for idx, row in pl_df.iterrows():
            comp = row["company_id"]
            yr = row["year"]
            div = row.get("dividend_payout", 0)
            if pd.notna(div) and (
                div < 0 or div > 200
            ):  # Allow up to 200% for special reserve dividends
                self.log_failure(
                    "DQ-09",
                    comp,
                    yr,
                    "dividend_payout",
                    div,
                    f"Dividend payout ratio out of range (0-200%): {div}%",
                    "WARNING",
                )

        # --- DQ-10: EPS sign validation against Net Profit ---
        for idx, row in pl_df.iterrows():
            comp = row["company_id"]
            yr = row["year"]
            eps = row.get("eps", 0)
            np_val = row.get("net_profit", 0)
            if pd.notna(eps) and pd.notna(np_val):
                if (eps < 0 and np_val > 0) or (eps > 0 and np_val < 0):
                    self.log_failure(
                        "DQ-10",
                        comp,
                        yr,
                        "eps",
                        eps,
                        f"EPS sign mismatch with net profit: EPS={eps}, Net Profit={np_val}",
                        "WARNING",
                    )

        # --- DQ-11: BSE Balance Check (Liabilities = Assets verification) ---
        # Included in DQ-04 check for assets vs liabilities logic

        # --- DQ-12: Stock Price Out-of-bounds Check ---
        prices_df = dfs["stock_prices"]
        for idx, row in prices_df.iterrows():
            comp = row["company_id"]
            dt = row["date"]
            open_p = row.get("open_price", 0)
            high_p = row.get("high_price", 0)
            low_p = row.get("low_price", 0)
            close_p = row.get("close_price", 0)
            adj_p = row.get("adjusted_close", 0)

            # High must be the maximum value, Low must be the minimum value
            if pd.notna(high_p) and pd.notna(low_p) and high_p < low_p:
                self.log_failure(
                    "DQ-12",
                    comp,
                    dt,
                    "high_price",
                    high_p,
                    f"Stock High price {high_p} is less than Low price {low_p}",
                    "CRITICAL",
                )

            for col_name, price in [
                ("open_price", open_p),
                ("high_price", high_p),
                ("low_price", low_p),
                ("close_price", close_p),
                ("adjusted_close", adj_p),
            ]:
                if pd.notna(price) and price < 0:
                    self.log_failure(
                        "DQ-12",
                        comp,
                        dt,
                        col_name,
                        price,
                        f"Negative stock price found: {price}",
                        "CRITICAL",
                    )

        # --- DQ-13: Missing Critical Fields ---
        for table_name in [
            "companies",
            "profitandloss",
            "balancesheet",
            "cashflow",
            "stock_prices",
        ]:
            df = dfs[table_name]
            critical_cols = [
                "id",
                "company_id",
                "year",
                "date",
                "sales",
                "total_assets",
                "net_cash_flow",
                "close_price",
            ]
            for col in df.columns:
                if col in critical_cols:
                    nulls = df[df[col].isna()]
                    for idx, row in nulls.iterrows():
                        self.log_failure(
                            "DQ-13",
                            row.get("company_id", row.get("id", "UNKNOWN")),
                            row.get("year", row.get("date", None)),
                            col,
                            "NULL",
                            f"Missing critical value in column {col} for table {table_name}",
                            "CRITICAL",
                        )

        # --- DQ-14: Financial ratios consistency check ---
        ratio_df = dfs["financial_ratios"]
        for idx, row in ratio_df.iterrows():
            comp = row["company_id"]
            yr = row["year"]
            npm = row.get("net_profit_margin_pct", 0)
            row.get("return_on_equity_pct", 0)

            if pd.notna(npm) and (npm < -200 or npm > 100):
                self.log_failure(
                    "DQ-14",
                    comp,
                    yr,
                    "net_profit_margin_pct",
                    npm,
                    f"Suspicious Net Profit Margin values: {npm}%",
                    "WARNING",
                )

        # --- DQ-15: URL Validation (Format validation for logo, charts) ---
        comp_df = dfs["companies"]
        url_regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        for idx, row in comp_df.iterrows():
            comp = row["id"]
            for url_col in [
                "company_logo",
                "chart_link",
                "website",
                "nse_profile",
                "bse_profile",
            ]:
                url = row.get(url_col, "")
                if (
                    pd.notna(url)
                    and str(url).strip() != ""
                    and not url_regex.match(str(url))
                ):
                    self.log_failure(
                        "DQ-15",
                        comp,
                        None,
                        url_col,
                        url,
                        f"Malformed URL string in {url_col}: {url}",
                        "WARNING",
                    )

        # --- DQ-16: Historical Coverage Check (At least 3 years check) ---
        pl_year_counts = pl_df.groupby("company_id")["year"].nunique().to_dict()
        for comp, count in pl_year_counts.items():
            if count < 3:
                self.log_failure(
                    "DQ-16",
                    comp,
                    None,
                    "year_coverage",
                    count,
                    f"Insufficient historical coverage: only {count} years of record (Minimum 3 required)",
                    "WARNING",
                )

        # Save to output CSV
        self.save_failures_csv()

    def save_failures_csv(self):
        """Saves logs to output/validation_failures.csv."""
        output_dir = r"C:\Users\sants\OneDrive\Desktop\Internship_2026\n100_financial_intelligence\output"
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "validation_failures.csv")

        df = pd.DataFrame(self.failures)
        if df.empty:
            df = pd.DataFrame(
                columns=[
                    "rule_id",
                    "company_id",
                    "year",
                    "column",
                    "value",
                    "message",
                    "severity",
                ]
            )

        df.to_csv(path, index=False)
        print(
            f"Validation failures logged successfully: {len(df)} cases saved to {path}"
        )
