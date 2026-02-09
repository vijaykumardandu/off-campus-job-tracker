import requests
from bs4 import BeautifulSoup

def fetch_jobs(keyword, location, max_jobs=5):
    url = f"https://www.indeed.com/jobs?q={keyword}&l={location}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = []
    for i, job_card in enumerate(soup.find_all('div', class_='job_seen_beacon')):
        if i >= max_jobs:
            break
        title = job_card.find('h2').text.strip()
        company_tag = job_card.find('span', class_='companyName')
        company = company_tag.text.strip() if company_tag else 'N/A'
        link_tag = job_card.find('a')
        link = 'https://www.indeed.com' + link_tag['href'] if link_tag else ''
        jobs.append({'title': title, 'company': company, 'link': link})
    return jobs

# Test
if __name__ == "__main__":
    jobs = fetch_jobs("Software Engineer", "Bangalore")
    for job in jobs:
        print(job)
