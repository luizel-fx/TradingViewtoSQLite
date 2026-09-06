"""
contracts.py
============
Predefined dictionary of standard futures contracts across CME, CBOT, NYMEX, and BMFBOVESPA.
"""

contracts = {
    "CCM": [
        "BMFBOVESPA",
        ["F", "H", "K", "N", "U", "X"],               # Jan, Mar, Mai, Jul, Set, Nov
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "BGI": [
        "BMFBOVESPA",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "DI1": [
        "BMFBOVESPA",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "DOL": [
        "BMFBOVESPA",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "ZS": [
        "CBOT",
        ["F", "H", "K", "N", "Q", "U", "X"],          # Jan, Mar, Mai, Jul, Ago, Set, Nov
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "ZC": [
        "CBOT",
        ["H", "K", "N", "U", "Z"],                    # Mar, Mai, Jul, Set, Dez
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "LE": [
        "CME",
        ["G", "J", "M", "Q", "V", "Z"],               # Fev, Abr, Jun, Ago, Out, Dez
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "SJC": [
        "BMFBOVESPA",
        ["F", "H", "K", "N", "Q", "U", "X"],          # Jan, Mar, Mai, Jul, Ago, Set, Nov
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "ZW": [
        "CBOT",
        ["H", "K", "N", "U", "Z"],                    # Mar, Mai, Jul, Set, Dez
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "HE": [
        "CME",
        ["G", "J", "M", "N", "Q", "V", "Z"],          # Fev, Abr, Jun, Jul, Ago, Out, Dez
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "CL": [
        "NYMEX",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses (WTI Crude Oil)
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "BZ": [
        "NYMEX",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses (Brent Crude Oil)
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "ZN": [
        "CBOT",
        ["H", "M", "U", "Z"],                         # Mar, Jun, Set, Dez (10-Year T-Note)
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "ZQ": [
        "CBOT",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses (30-Day Federal Funds)
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
}

DEFAULT_CONTRACTS = contracts
