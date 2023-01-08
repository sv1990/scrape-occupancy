#!/usr/bin/env python

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Generator

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
    output_folder = (
        output_folder
        / "raw"
        / datetime.fromisoformat(str(result["timestamp"])).strftime("%Y-%m-%d")
    )
    output_folder.mkdir(exist_ok=True, parents=True)
    filename = output_folder / f"percentages_{result['timestamp']}.json"
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(result, file)
        print(f"Stored occupancies in {filename.resolve()}")


def get_percentages(driver: Chrome, urls: dict[str, str]) -> dict[str, str | float]:
    result: dict[str, str | float] = {
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    for name, url in urls.items():
        driver.get(url)
        percentage = get_percentage(driver)
        result[name] = percentage
        print(f"{name}: {percentage}%")
    return result


def get_percentage(driver: Chrome) -> float:
    wait = WebDriverWait(driver, 10)
    item = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, """//*[@class=\"chartbar__percentage\"]""")
        )
    )
    return float(item.text.rstrip("%").strip())


def accept_cookies(driver: Chrome) -> None:
    sleep(10)

    item = driver.execute_script(
        """selector = document.querySelector('#usercentrics-root');
           if (selector) {
               return selector.shadowRoot.querySelector("[data-testid='uc-accept-all-button']")}
           else {
               return null
           }
        """
    )
    if item is not None:
        item.click()


@contextmanager
def get_driver() -> Generator[Chrome, None, None]:
    options = Options()
    options.headless = True
    driver = Chrome(options=options)
    driver.maximize_window()
    driver.implicitly_wait(10)
    try:
        yield driver
    finally:
        driver.close()


if __name__ == "__main__":
    main()
