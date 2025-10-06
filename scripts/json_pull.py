import requests
import json
import feedgenerator
import xml.dom.minidom
import os
import datetime

# URL for fetching the documents
url = "https://ec.europa.eu/transparency/documents-request/api/portal/search/criteria"

# Query string
querystring = {
    "disclosureDepartments": "",
    "exceptionsInvolved": "",
    "associatedKeywords": "",
    "disclosureType": "FULL_ACCESS,PARTIAL",
    "isPartial": "true",
    "isFullAccess": "true",
    "page": "0",
    "size": "50",
    "sort": "publishedOn,DESC"
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Cache-Control": "No-Cache",
    "Connection": "keep-alive",
    "Referer": "https://ec.europa.eu/transparency/documents-request/search",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest"
}

# Load previously fetched documents
def load_existing_documents():
    if os.path.exists("processed_documents.json"):
        with open("processed_documents.json", "r") as f:
            return json.load(f)  # List of dicts
    return []

# Save processed documents
def save_processed_documents(documents):
    # Keep only last 250
    documents = documents[:250]
    with open("processed_documents.json", "w") as f:
        json.dump(documents, f)

# Create RSS feed from a list of document dicts
def create_rss_feed(documents):
    feed = feedgenerator.Rss201rev2Feed(
        title="EU Documents RSS Feed",
        link="https://github.com/rkoens/ease",
        description="Latest documents from the EU Transparency Portal"
    )

    for doc in documents:
        doc_link = f"https://ec.europa.eu/transparency/documents-request/search/document-details/{doc['publishedDocumentId']}"
        try:
            disclosure_date = datetime.datetime.strptime(doc['disclosureDate'], "%Y-%m-%d").date()
        except ValueError:
            disclosure_date = datetime.datetime.now().date()

        feed.add_item(
            title=doc.get('documentTitle', 'No title'),
            link=doc_link,
            description=doc.get('documentTitle', 'No title'),
            pubdate=disclosure_date,
            unique_id=doc['publishedDocumentId'],
            categories=[doc['disclosureType']],
        )

    xml_str = feed.writeString("utf-8")
    xml_str_pretty = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")
    with open("feed.xml", "w") as f:
        f.write(xml_str_pretty)

# Fetch new data and update master list
def fetch_data():
    existing_documents = load_existing_documents()  # List of dicts
    seen_keys = set((d['publishedDocumentId'], d['disclosureDate'], d['disclosureType']) for d in existing_documents)

    new_documents = []
    max_pages_to_check = 5
    page_num = 0

    while page_num < max_pages_to_check:
        querystring['page'] = str(page_num)
        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code != 200:
            print(f"Failed to fetch page {page_num}, Status Code: {response.status_code}")
            break

        data = response.json()
        documents = data['content']
        if not documents:
            break

        for doc in documents:
            key = (doc['publishedDocumentId'], doc['disclosureDate'], doc['disclosureType'])
            if key in seen_keys:
                # Stop at first existing document
                continue
            new_documents.append(doc)
            seen_keys.add(key)

        page_num += 1

    # Prepend new documents so newest are first
    updated_documents = new_documents + existing_documents
    # Keep only last 250 entries
    updated_documents = updated_documents[:250]

    # Save master list and update RSS
    save_processed_documents(updated_documents)
    if updated_documents:
        create_rss_feed(updated_documents)

if __name__ == "__main__":
    fetch_data()
