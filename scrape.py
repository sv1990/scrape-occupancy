#!/usr/bin/env python

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Generator

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tap import Tap


class Args(Tap):
    output_folder: Path = Path("out")
    once: bool = False
    sleep: int = 60

    def configure(self) -> None:
        self.add_argument("--output_folder", "-o")


def main() -> None:
    args = Args().parse_args()

    urls = {
        "stephansplatz": "https://www.fitnessfirst.de/clubs/hamburg-stephansplatz",
        "eppendorf": "https://www.fitnessfirst.de/clubs/hamburg-eppendorf",
        "wandsbek": "https://www.fitnessfirst.de/clubs/hamburg-wandsbek",
        "altona": "https://www.fitnessfirst.de/clubs/hamburg-altona",
        "st-georg": "https://www.fitnessfirst.de/clubs/hamburg-st-georg-hbf",
        "niendorf": "https://www.fitnessfirst.de/clubs/hamburg-niendorf",
        "jungfernstieg": "https://www.fitnessfirst.de/clubs/hamburg-mitte-jungfernstieg",
        "neustadt": "https://www.fitnessfirst.de/clubs/hamburg-neustadt-roedingsmarkt",
    }

    output_folder = args.output_folder
    output_folder.mkdir(exist_ok=True, parents=True)

    with get_driver() as driver:

        driver.get(next(iter(urls.values())))
        accept_cookies(driver)

        while True:
            result = get_percentages(driver, urls)

            store_json(result, output_folder)

            if args.once:
                break

            sleep(60 * args.sleep)


def store_json(result: dict[str, str | float], output_folder: Path) -> None:
    filename = output_folder / f"percentages_{result['timestamp']}.json"
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(result, file)
        print(f"Stored occupations in {filename.resolve()}")


def get_percentages(driver: Firefox, urls: dict[str, str]) -> dict[str, str | float]:
    result: dict[str, str | float] = {
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    for name, url in urls.items():
        driver.get(url)
        percentage = get_percentage(driver)
        result[name] = percentage
        print(f"{name}: {percentage}%")
    return result


def get_percentage(driver: Firefox) -> float:
    wait = WebDriverWait(driver, 10)
    item = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, """//*[@class=\"chartbar__percentage\"]""")
        )
    )
    return float(item.text.rstrip("%").strip())


def accept_cookies(driver: Firefox) -> None:
    sleep(10)

    item = driver.execute_script(
        """return document.querySelector('#usercentrics-root')"""
        """.shadowRoot.querySelector("[data-testid='uc-accept-all-button']")"""
    )
    if item is not None:
        item.click()


@contextmanager
def get_driver() -> Generator[Firefox, None, None]:
    options = Options()
    options.headless = True
    try:
        driver = Firefox(options=options)
        driver.maximize_window()
        driver.implicitly_wait(10)
        yield driver
    finally:
        driver.close()  # type: ignore


if __name__ == "__main__":
    main()
