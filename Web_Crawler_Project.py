from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import time
import argparse

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def is_valid_domain(link, base_domain):
    parsed_link = urlparse(link)
    link_domain = parsed_link.netloc
    return link_domain == base_domain or link_domain.endswith("." + base_domain)

def load_adblock_rules(adblock_rules_input):
    if is_valid_url(adblock_rules_input):
        response = requests.get(adblock_rules_input)
        response.raise_for_status()
        return response.text.splitlines()
    else:
        with open(adblock_rules_input, 'r', encoding='utf-8') as file:
            return file.read().splitlines()

def process_input(input_value, adblock_rules_input, allowed_domains, user_keywords=None):
    base_domain = urlparse(input_value).netloc
    if is_valid_url(input_value):
        print(f"\nProcessing Website: {input_value}")
        website_crawler_with_adblocker(input_value, adblock_rules_input, base_domain, allowed_domains=allowed_domains, user_keywords=user_keywords)
    else:
        process_websites_from_file(input_value, adblock_rules_input, allowed_domains, user_keywords=user_keywords)

def process_websites_from_file(file_path, adblock_rules_input, allowed_domains, user_keywords=None):
    with open(file_path, 'r') as file:
        websites = file.read().splitlines()

    for website in websites:
        print(f"\nProcessing Website: {website}")
        base_domain = urlparse(website).netloc
        website_crawler_with_adblocker(website, adblock_rules_input, base_domain, allowed_domains=allowed_domains, user_keywords=user_keywords)

def website_crawler_with_adblocker(URL, adblock_rules_input, base_domain, allowed_domains, user_keywords=None):
    try:
        options = webdriver.FirefoxOptions()
        prefs = {
            'profile.managed_default_content_settings.images': 2,
            'profile.managed_default_content_settings.javascript': 2
        }
        options.add_argument('--devtools')
        options.add_argument('--headless')
        driver = webdriver.Firefox(options=options)

        driver.get(URL)
        time.sleep(5)

        links = driver.find_elements(By.TAG_NAME, 'a')
        adblock_rules = load_adblock_rules(adblock_rules_input)

        original_links_count = 0
        filtered_links_count = 0
        third_party_links_count = 0
        relevant_count = 0
        non_accessible_links_count = 0
        relevant_links = []  # New list to store relevant links

        print(f"\nWebsite Link: {URL}")
        for link in links:
            link_url = link.get_attribute('href')
            if link_url is not None:
                print(f"Processing Link: {link_url}")

                is_allowed = any(is_valid_domain(link_url, domain) for domain in allowed_domains)
                should_block = any(keyword in link_url for keyword in adblock_rules)

                if is_allowed:
                    if not should_block:
                        original_links_count += 1
                        print(f"Original Link #{original_links_count}: {link_url}")

                        if user_keywords and any(keyword in link_url for keyword in user_keywords):
                            relevant_count += 1
                            relevant_links.append(link_url)  # Add relevant link to the list
                            print(f"Relevant Link #{relevant_count}: {link_url}")

                    elif should_block:
                        filtered_links_count += 1
                        print(f"Filtered Link #{filtered_links_count}: {link_url}")

                    else:
                        is_third_party = not is_valid_domain(link_url, base_domain)
                        if is_third_party:
                            third_party_links_count += 1
                            print(f"Third-Party Link #{third_party_links_count}: {link_url}")

                            # Check if the third-party link is relevant
                            if user_keywords and any(keyword in link_url for keyword in user_keywords):
                                relevant_count += 1
                                relevant_links.append(link_url)  # Add relevant link to the list
                                print(f"Relevant Third-Party Link #{relevant_count}: {link_url}")

                else:
                    is_third_party = not is_valid_domain(link_url, base_domain)
                    if is_third_party:
                        third_party_links_count += 1
                        print(f"Third-Party Link #{third_party_links_count}: {link_url}")
                        
                        if user_keywords and any(keyword in link_url for keyword in user_keywords):
                                relevant_count += 1
                                relevant_links.append(link_url)  # Add relevant link to the list
                                print(f"Relevant Third-Party Link #{relevant_count}: {link_url}")
                    else:
                        non_accessible_links_count += 1
                        print(f"Non-Accessible Link #{non_accessible_links_count}: {link_url}")

            else:
                print("Skipping Link as it is None.")

        print(f"Total Original Links: {original_links_count}")
        print(f"Total Filtered Links: {filtered_links_count}")
        print(f"Total Non-Accessible Links: {non_accessible_links_count}")
        print(f"Total Third-Party Links: {third_party_links_count}")
        print(f"Total Relevant Links: {relevant_count}")

        # Print relevant links
        if relevant_links:
            print("\nRelevant Links:")
            for idx, link in enumerate(relevant_links, start=1):
                print(f"Relevant Link #{idx}: {link}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture and filter links from a website or a list of websites with an adblocker.")
    parser.add_argument("input_value", help="URL of the website or path to the file containing the list of websites", default=None)
    parser.add_argument("--adblock_input", help="URL or file path of the adblock rules", default='https://easylist.to/easylist/easylist.txt')
    parser.add_argument("--user_keywords", help="Comma-separated list of user keywords for relevance", default=None)
    args = parser.parse_args()

    allowed_domains = [urlparse(args.input_value).netloc] if args.input_value and is_valid_url(args.input_value) else []
    user_keywords = [keyword.strip() for keyword in args.user_keywords.split(',')] if args.user_keywords else None

    process_input(args.input_value, args.adblock_input, allowed_domains=allowed_domains, user_keywords=user_keywords)
