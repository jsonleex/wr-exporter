import os
import re
import shutil
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def parse_url(url: str) -> tuple[str, str]:
    match = re.search(r"https:\/\/.*\/web\/reader\/(\w{23})\/?", url)

    if not match:
        raise ValueError(f"Invalid url: {url}")

    return (url, match.group(1))


def get_chrome_driver(
    dev: bool = False,
    window_size: str = "1920,1080",
    user_data_dir: str = "./cache/default",
) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()

    if not dev:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")

    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={window_size}")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")

    return webdriver.Chrome(
        options=options,
        service=Service(ChromeDriverManager().install()),
    )


def ensure_logged(driver: webdriver.Chrome) -> None:
    if len(driver.find_elements(By.CLASS_NAME, "wr_avatar_img")) > 0:
        print("🟢 Already logged in.")
    else:
        print("🔴 Please login with WeChat.")
        print("🟣 Use `--dev` option to disable headless mode for login.")
        driver.quit()
        exit(1)


def yes_or_no(question: str, default: bool = True) -> bool:
    prompt = f"{question} [{'Y/n' if default else 'y/N'}] "
    while True:
        answer = input(prompt).strip().lower()

        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False

        print("🔴 Invalid input. Please try again.")


def ensure_output(output: str) -> str:
    output = os.path.abspath(output)

    if not os.path.exists(output):
        os.makedirs(output)

    elif os.listdir(output):
        if yes_or_no("🟣 Output is not empty. Overwrite it?"):
            shutil.rmtree(output)
            os.makedirs(output)
        else:
            raise ValueError("Output directory is not empty.")

    return output


def inject_custom_styles(driver: webdriver.Chrome, style_path: str = "override.css"):
    with open(style_path, "r") as f:
        style = f.read()

    driver.execute_script(
        script=f"""
        const style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = `{style}`;
        document.head.appendChild(style);
        """
    )


def is_empty_screenshot(fpath: str) -> bool:
    if not os.path.exists(fpath):
        raise ValueError(f"File not found: {fpath}")

    return os.path.getsize(fpath) <= 10763  # 10663 + 100


def export_book(driver: webdriver.Chrome, book_url: str, output: str):
    if driver.current_url != book_url:
        driver.get(book_url)
        driver.implicitly_wait(10)

    time.sleep(6)

    # inject custom styles
    inject_custom_styles(driver)

    # Resize window
    driver.set_window_size(540, 960)  # Screenshot => 1080x1920

    count = 0
    empty_count = 0

    while True:
        try:
            time.sleep(3)
            filename = f"{time.strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(output, filename)

            count += 1
            print(f"⏳ Exporting... {count}", end="\r")

            driver.save_screenshot(filepath)

            if is_empty_screenshot(filepath):
                empty_count += 1
            else:
                empty_count = max(0, empty_count - 1)

            if empty_count >= 5:
                print(f"🟣 Too many empty pages. Maybe the book is finished.")
                break

            next_button = driver.find_element(
                By.XPATH,
                "/html/body/div[1]/div/div/div[1]/div[2]/div/div[2]/div[4]/div[2]/button",
            )
            # Next Page
            next_button.click()

            # TODO watch title change for new chapter

            time.sleep(3)

        except KeyboardInterrupt:
            print("----------------")
            print("🔴 User Cancelled.")
            break

    print(f"✅ Exported {count} images (empty {empty_count})")


def main(args):
    dev = args.dev
    url, book_id = parse_url(args.url[0])

    if dev:
        print("🛠️ Running in dev mode.")
        output = "No Output."
    else:
        output = ensure_output(args.output or f"./{book_id}")

    print(f"📁 {output}")
    print(f"🔗 {url}")

    driver = get_chrome_driver(dev)
    driver.get(url)
    driver.implicitly_wait(10)

    ensure_logged(driver)

    # Show book info
    info = driver.title.split(" - ")
    print(f"📖 {info[0]}")

    if not dev:
        export_book(driver, url, output)

    print("")
    input("Press Enter to exit...")
    driver.quit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="wre",
        description="Simple Exporter for WeRead.",
    )

    parser.add_argument(
        "url",
        nargs=1,
        help="The URL of the book to export",
    )

    parser.add_argument(
        "-o",
        dest="output",
        type=str,
        help="Output directory for the exported files",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Disable headless mode for debugging/login",
    )

    args = parser.parse_args()

    main(args)
