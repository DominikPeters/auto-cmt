import os
import requests
import json
from rich.prompt import Prompt
from rich.console import Console
from pathlib import Path

def login_to_cmt(conference_id, username, password):
    login_url = 'https://cmt3.research.microsoft.com/api/odata/Users/Login?ReturnUrl=%2F'
    headers = {
        'Accept': 'application/json;odata.metadata=full',
        'Content-Type': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Origin': 'https://cmt3.research.microsoft.com',
        'Prefer': 'return=representation'
    }
    data = {"Request": {"Email": username, "Password": password}}
    response = requests.post(login_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.cookies
    else:
        raise Exception('Login failed')

def get_paper_ids(conference_id, cookies, is_meta_reviewer):
    url = f'https://cmt3.research.microsoft.com/api/odata/{conference_id}/$batch'
    headers = {
        'Accept': 'application/json;odata.metadata=full',
        'Content-Type': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Origin': 'https://cmt3.research.microsoft.com',
        'Prefer': 'return=representation'
    }
    models = "MetaReviewModels" if is_meta_reviewer else "ReviewModels"
    data = {"requests": [{"url": f"/api/odata/{conference_id}/{models}?$count=true&$orderby=Id&$top=50","method": "GET","headers": {"Accept": "application/json"}}]}
    response = requests.post(url, headers=headers, cookies=cookies, json=data)
    paper_ids = [item['Id'] for item in response.json()['responses'][0]['body']['value']]
    # save response to file
    with open(f'data/{conference_id}/paper_ids.json', 'w') as file:
        file.write(json.dumps(paper_ids))
    return paper_ids

def fetch_and_save(conference_id, paper_id, data_type, cookies):
    base_url = f'https://cmt3.research.microsoft.com/api/odata/{conference_id}'
    url_map = {
        'Reviews': f'{base_url}/Submissions({paper_id})/Reviews',
        'MetaReviews': f'{base_url}/Submissions({paper_id})/MetaReviews',
        'DiscussionMessages': f'{base_url}/DiscussionMessages?id={paper_id}&$orderby=Date desc',
        'AuthorFeedback': f'{base_url}/AuthorFeedbackViews/GetBySubmissionId'
    }

    headers = {
        'Accept': 'application/json;odata.metadata=full',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Prefer': 'return=representation'
    }
    
    if data_type == 'AuthorFeedback':
        data = {'Id': paper_id}
        response = requests.post(url_map[data_type], headers=headers, cookies=cookies, json=data)
    else:
        response = requests.get(url_map[data_type], headers=headers, cookies=cookies)
    
    if response.status_code == 200:
        data_folder = f'data/{conference_id}/{paper_id}'
        os.makedirs(data_folder, exist_ok=True)
        file_path = f'{data_folder}/{data_type}.json'
        with open(file_path, 'w') as file:
            file.write(response.text)
        
        # Special handling for author feedback files
        if data_type == 'AuthorFeedback':
            feedback_data = response.json()
            if feedback_data and "Files" in feedback_data and feedback_data["Files"]:
                pdf_path = f'{data_folder}/AuthorFeedback.pdf'
                if not os.path.exists(pdf_path):
                    download_link = feedback_data["Files"][0]["DownloadLink"]
                    file_url = f'https://cmt3.research.microsoft.com{download_link}'
                    file_response = requests.get(file_url, cookies=cookies)
                    if file_response.status_code == 200:
                        with open(pdf_path, 'wb') as pdf_file:
                            pdf_file.write(file_response.content)
    else:
        print(f"Failed to fetch {data_type} for paper {paper_id}")

def main(conference_id, username, password, is_meta_reviewer):
    print("Logging in...")
    cookies = login_to_cmt(conference_id, username, password)
    print("Get paper IDs...")
    paper_ids = get_paper_ids(conference_id, cookies, is_meta_reviewer)
    for num, paper_id in enumerate(paper_ids):
        print(f"{num+1}/{len(paper_ids)} Fetching paper {paper_id}...")
        print("   Reviews")
        fetch_and_save(conference_id, paper_id, 'Reviews', cookies)
        print("   MetaReviews")
        fetch_and_save(conference_id, paper_id, 'MetaReviews', cookies)
        print("   DiscussionMessages")
        fetch_and_save(conference_id, paper_id, 'DiscussionMessages', cookies)
        print("   AuthorFeedback")
        fetch_and_save(conference_id, paper_id, 'AuthorFeedback', cookies)

console = Console()

def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return None

def write_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def get_credentials():
    credentials_path = Path('credentials.json')
    credentials = read_json_file(credentials_path)

    if credentials:
        use_saved = Prompt.ask(f"Do you want to login with username {credentials['username']}?", default="Y", choices=["Y", "N"])
        if use_saved.upper() == "Y":
            return credentials
    else:
        credentials = {}

    credentials['username'] = Prompt.ask("Enter your username (email)")
    credentials['password'] = Prompt.ask("Enter your password", password=True)
    write_json_file(credentials_path, credentials)
    return credentials

def get_conference_info():
    conference_path = Path('last_conference.json')
    conference_info = read_json_file(conference_path)

    if conference_info:
        role = "meta reviewer" if conference_info.get("is_meta_reviewer", False) else "reviewer"
        use_saved = Prompt.ask(f"Do you want to fetch {conference_info['conference_id']} in role {role}?", default="Y", choices=["Y", "N"])
        if use_saved.upper() == "Y":
            return conference_info
    else:
        conference_info = {}

    conference_info['conference_id'] = Prompt.ask("Enter the conference ID")
    is_meta_reviewer = Prompt.ask("Are you a meta reviewer?", default="N", choices=["Y", "N"])
    conference_info['is_meta_reviewer'] = True if is_meta_reviewer.upper() == "Y" else False
    write_json_file(conference_path, conference_info)
    return conference_info

if __name__ == "__main__":
    credentials = get_credentials()
    conference_info = get_conference_info()

    console.print(f"Processing conference {conference_info['conference_id']} as {'meta reviewer' if conference_info['is_meta_reviewer'] else 'reviewer'}...", style="bold green")
    main(conference_info['conference_id'], credentials['username'], credentials['password'], conference_info['is_meta_reviewer'])
