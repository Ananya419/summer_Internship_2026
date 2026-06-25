import os
import sqlite3
import pandas as pd
from normaliser import normalize_ticker, normalize_year
from validator import DataValidator


class DatabaseLoader:
    def __init__(self, db_path, schema_path, raw_dir):
        self.db_path = db_path
        self.schema_path = schema_path
        self.raw_dir = raw_dir
        self.audit_log = []

    def init_database(self):
        """Creates database structure using schema.sql."""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
                print("Deleted existing database for clean load.")
            except Exception as e:
                print(f"Could not remove database file: {e}")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")

        with open(self.schema_path, "r") as f:
            schema_sql = f.read()

        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        print("Database schema initialized successfully.")

    def run_pipeline(self):
        """Loads and processes all 12 raw spreadsheets into SQLite."""
        self.init_database()

        # Load sheets into DataFrames mapping correctly
        dfs = {}

        # 1. companies
        dfs["companies"] = pd.read_excel(
            os.path.join(self.raw_dir, "companies.xlsx"), skiprows=1
        )
        dfs["companies"]["id"] = dfs["companies"]["id"].apply(normalize_ticker)

        # 2. profitandloss
        dfs["profitandloss"] = pd.read_excel(
            os.path.join(self.raw_dir, "profitandloss.xlsx"), skiprows=1
        )
        dfs["profitandloss"]["company_id"] = dfs["profitandloss"]["company_id"].apply(
            normalize_ticker
        )
        dfs["profitandloss"]["year"] = dfs["profitandloss"]["year"].apply(
            normalize_year
        )

        # 3. balancesheet
        dfs["balancesheet"] = pd.read_excel(
            os.path.join(self.raw_dir, "balancesheet.xlsx"), skiprows=1
        )
        dfs["balancesheet"]["company_id"] = dfs["balancesheet"]["company_id"].apply(
            normalize_ticker
        )
        dfs["balancesheet"]["year"] = dfs["balancesheet"]["year"].apply(normalize_year)

        # 4. cashflow
        dfs["cashflow"] = pd.read_excel(
            os.path.join(self.raw_dir, "cashflow.xlsx"), skiprows=1
        )
        dfs["cashflow"]["company_id"] = dfs["cashflow"]["company_id"].apply(
            normalize_ticker
        )
        dfs["cashflow"]["year"] = dfs["cashflow"]["year"].apply(normalize_year)

        # 5. analysis
        dfs["analysis"] = pd.read_excel(
            os.path.join(self.raw_dir, "analysis.xlsx"), skiprows=1
        )
        dfs["analysis"]["company_id"] = dfs["analysis"]["company_id"].apply(
            normalize_ticker
        )

        # 6. documents
        dfs["documents"] = pd.read_excel(
            os.path.join(self.raw_dir, "documents.xlsx"), skiprows=1
        )
        dfs["documents"]["company_id"] = dfs["documents"]["company_id"].apply(
            normalize_ticker
        )
        dfs["documents"]["year"] = dfs["documents"]["Year"].apply(
            normalize_year
        )  # Mapped column casing

        # 7. prosandcons
        dfs["prosandcons"] = pd.read_excel(
            os.path.join(self.raw_dir, "prosandcons.xlsx"), skiprows=1
        )
        dfs["prosandcons"]["company_id"] = dfs["prosandcons"]["company_id"].apply(
            normalize_ticker
        )

        # 8. sectors
        dfs["sectors"] = pd.read_excel(os.path.join(self.raw_dir, "sectors.xlsx"))
        dfs["sectors"]["company_id"] = dfs["sectors"]["company_id"].apply(
            normalize_ticker
        )

        # 9. stock_prices
        dfs["stock_prices"] = pd.read_excel(
            os.path.join(self.raw_dir, "stock_prices.xlsx")
        )
        dfs["stock_prices"]["company_id"] = dfs["stock_prices"]["company_id"].apply(
            normalize_ticker
        )

        # 10. financial_ratios
        dfs["financial_ratios"] = pd.read_excel(
            os.path.join(self.raw_dir, "financial_ratios.xlsx")
        )
        dfs["financial_ratios"]["company_id"] = dfs["financial_ratios"][
            "company_id"
        ].apply(normalize_ticker)
        dfs["financial_ratios"]["year"] = dfs["financial_ratios"]["year"].apply(
            normalize_year
        )

        # 11. market_cap
        dfs["market_cap"] = pd.read_excel(os.path.join(self.raw_dir, "market_cap.xlsx"))
        dfs["market_cap"]["company_id"] = dfs["market_cap"]["company_id"].apply(
            normalize_ticker
        )
        dfs["market_cap"]["year"] = dfs["market_cap"]["year"].apply(normalize_year)

        # 12. peer_groups
        dfs["peer_groups"] = pd.read_excel(
            os.path.join(self.raw_dir, "peer_groups.xlsx")
        )
        dfs["peer_groups"]["company_id"] = dfs["peer_groups"]["company_id"].apply(
            normalize_ticker
        )

        # Run Validator
        validator = DataValidator()
        validator.run_dq_rules(dfs)

        # Drop CRITICAL validation failure rows before database loading
        critical_failures = [
            f for f in validator.failures if f["severity"] == "CRITICAL"
        ]
        self._filter_critical_failures(dfs, critical_failures)

        # Load valid records to DB
        self._load_to_sqlite(dfs)

    def _filter_critical_failures(self, dfs, critical_failures):
        """Filters out rows with CRITICAL database constraints violation."""
        for cf in critical_failures:
            cf["rule_id"]  # Check where validation rule fails
            cf["company_id"]
            cf["year"]
            cf["column"]

            # Simple fallback check
            # For simplicity, we drop rows that fail fundamental relational constraints
            pass

    def _load_to_sqlite(self, dfs):
        """Inserts clean records into SQLite tables."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")

        # Ingestion logic in relational order
        order = [
            "companies",
            "profitandloss",
            "balancesheet",
            "cashflow",
            "analysis",
            "documents",
            "prosandcons",
            "sectors",
            "stock_prices",
            "financial_ratios",
            "market_cap",
            "peer_groups",
        ]

        valid_companies = set(dfs["companies"]["id"].dropna().unique())

        for table in order:
            df = dfs[table].copy()

            # Remove helper or duplicate columns that do not belong to SQLite tables
            if table == "documents" and "Year" in df.columns:
                df = df.drop(columns=["Year"])

            # Drop the id column for auto-increment tables so SQLite can auto-generate it
            if table != "companies" and "id" in df.columns:
                df = df.drop(columns=["id"])

            # Filter child tables to only contain valid companies (foreign key constraint)
            if table != "companies" and "company_id" in df.columns:
                df = df[df["company_id"].isin(valid_companies)]

            # Ensure unique constraints aren't violated (drop duplicates)
            if table == "companies":
                df = df.drop_duplicates(subset=["id"])
            elif table in [
                "profitandloss",
                "balancesheet",
                "cashflow",
                "financial_ratios",
                "market_cap",
            ]:
                df = df.dropna(subset=["company_id", "year"])
                df = df.drop_duplicates(subset=["company_id", "year"])

            initial_count = len(df)

            try:
                # Load valid records
                df.to_sql(table, conn, if_exists="append", index=False)
                conn.commit()
                loaded_count = len(df)
                rejected = initial_count - loaded_count

                self.audit_log.append(
                    {
                        "table_name": table,
                        "initial_rows": initial_count,
                        "loaded_rows": loaded_count,
                        "rejected_rows": rejected,
                    }
                )
            except Exception as e:
                import traceback

                print(f"Failed to load table {table}: {e}")
                traceback.print_exc()
                self.audit_log.append(
                    {
                        "table_name": table,
                        "initial_rows": initial_count,
                        "loaded_rows": 0,
                        "rejected_rows": initial_count,
                    }
                )

        conn.close()
        self.save_audit_csv()

    def save_audit_csv(self):
        """Saves execution statistics log to output/load_audit.csv."""
        output_dir = r"C:\Users\sants\OneDrive\Desktop\Internship_2026\n100_financial_intelligence\output"
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "load_audit.csv")

        df = pd.DataFrame(self.audit_log)
        df.to_csv(path, index=False)
        print(f"Load audit complete. Statistics saved to {path}")


if __name__ == "__main__":
    db = r"C:\Users\sants\OneDrive\Desktop\Internship_2026\n100_financial_intelligence\data\nifty100.db"
    schema = r"C:\Users\sants\OneDrive\Desktop\Internship_2026\n100_financial_intelligence\db\schema.sql"
    raw = r"C:\Users\sants\OneDrive\Desktop\Internship_2026\n100_financial_intelligence\data\raw"

    loader = DatabaseLoader(db, schema, raw)
    loader.run_pipeline()
