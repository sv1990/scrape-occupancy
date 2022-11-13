#!/usr/bin/env python


import json
from pathlib import Path

import pandas as pd
from tap import Tap


class Args(Tap):
    input_folder: Path = Path("out")
    output_folder: Path = Path("out")
    once: bool = False
    sleep: int = 60

    def configure(self) -> None:
        self.add_argument("--output_folder", "-o")


def main() -> None:
    args = Args().parse_args()

    output_folder = args.output_folder / "formatted"
    output_folder.mkdir(parents=True, exist_ok=True)

    df = read_folder(args.input_folder)
    df.to_csv(output_folder / "formatted.csv")


def read_folder(input_folder: Path) -> pd.DataFrame:
    def read_data(filename: Path) -> pd.DataFrame:
        with open(filename, encoding="utf-8") as file:
            data = json.load(file)
            return pd.json_normalize(data)

    df = pd.concat(
        (read_data(file) for file in input_folder.glob("raw/*/*.json")),
        ignore_index=True,
    )
    df.timestamp = pd.to_datetime(df.timestamp)
    df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/Berlin")
    df = df.set_index("timestamp").sort_index()
    df.columns.name = "studio"
    return df


if __name__ == "__main__":
    main()
