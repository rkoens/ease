import requests
import json
import os

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
            return set(json.load(f))  # A set of tuples (publishedDocumentId, disclosureDate, disclosureType)
    return set()

# Save new document information to prevent duplicates
def save_processed_documents(processed_documents):
    with open("processed_documents.json", "w") as f:
        json.dump(list(processed_documents), f)

# Fetch data and process pagination
def fetch_data():
    existing_documents = load_existing_documents()  # Set of processed documents
    new_documents = []
    last_processed_doc_id = None

    # Get total pages dynamically (fetch only the first page initially)
    response = requests.get(url, headers=headers, params=querystring)
    total_pages = response.json().get("totalPages", 0)
    
    # Start from the most recent documents
    page_num = 0
    while True:
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

    # Save updated document information to prevent re-processing
    save_processed_documents(existing_documents)

# Run the script to fetch and update the RSS feed
if __name__ == "__main__":
    fetch_data()