import requests
import json
import feedgenerator
import xml.dom.minidom
import os
import datetime

# URL for fetching the documents
url = "https://ec.europa.eu/transparency/documents-request/api/portal/search/criteria"

# Query string for full access and partial documents
querystring = {
    "disclosureDepartments": "",
    "exceptionsInvolved": "",
    "associatedKeywords": "",
    "disclosureType": "FULL_ACCESS,PARTIAL",
    "isPartial": "true",
    "isFullAccess": "true",
    "page": "0",  # Start from page 0
    "size": "50",  # Number of documents per page
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

# Load previously fetched documents (to detect new submissions)
def load_existing_documents():
    if os.path.exists("processed_documents.json"):
        with open("processed_documents.json", "r") as f:
            return set(json.load(f))
    return set()

# Save new document information to prevent duplicates
def save_processed_documents(processed_documents):
    with open("processed_documents.json", "w") as f:
        json.dump(list(processed_documents), f)

# Create the RSS feed
def create_rss_feed(documents):
    feed = feedgenerator.Rss201rev2Feed(
        title="EU Documents RSS Feed",
        link="https://github.com/rkoens/ease",  # Replace with your repository link
        description="Latest documents from the EU Transparency Portal"
    )
    
    # Add new items at the top by reversing the list
    for doc in reversed(documents):  # Reverse the order to add new items first
        doc_link = f"https://ec.europa.eu/transparency/documents-request/search/document-details/{doc['publishedDocumentId']}"
        
        try:
            disclosure_date = datetime.datetime.strptime(doc['disclosureDate'], "%Y-%m-%d").date()
        except ValueError:
            disclosure_date = datetime.datetime.now().date()

        feed.add_item(
            title=doc['documentTitle'],
            link=doc_link,
            description=doc['documentTitle'],
            pubdate=disclosure_date,
            unique_id=doc['publishedDocumentId'],
            categories=[doc['disclosureType']],
        )

    xml_str = feed.writeString("utf-8")
    xml_str_pretty = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

    with open("feed.xml", "w") as f:
        f.write(xml_str_pretty)

# Fetch data and process pagination
def fetch_data():
    existing_documents = load_existing_documents()  # Set of processed documents
    new_documents = []
    last_processed_doc_id = None

    # Get total pages dynamically (fetch only the first few pages initially)
    response = requests.get(url, headers=headers, params=querystring)
    total_pages = response.json().get("totalPages", 0)
    
    # For testing purposes, limit to 2 pages
    max_pages_to_check = 5
    page_num = 0

    while page_num < max_pages_to_check:
        querystring['page'] = str(page_num)
        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code == 200:
            data = response.json()
            documents = data['content']
            
            for doc in documents:
                unique_key = (doc['publishedDocumentId'], doc['disclosureDate'], doc['disclosureType'])
                
                # Stop if we encounter a document that's already in the feed
                if unique_key in existing_documents:
                    print(f"Found existing document: {doc['documentTitle']}. Stopping.")
                    break
                
                # Add new document to list if it's not in the feed
                new_documents.append(doc)
                existing_documents.add(unique_key)

            # If we've encountered an existing document, stop checking
            if len(documents) == 0 or unique_key in existing_documents:
                break

            page_num += 1  # Move to the next page

        else:
            print(f"Failed to fetch page {page_num}, Status Code: {response.status_code}")
            break  # Exit the loop on error

    # Create or update the RSS feed with new documents
    if new_documents:
        create_rss_feed(new_documents)

    # Save updated document information to prevent re-processing
    save_processed_documents(existing_documents)

# Run the script to fetch and update the RSS feed
if __name__ == "__main__":
    fetch_data()








