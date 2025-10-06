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
def save_processed_documents(processed_documents):
    # Save as list of tuples: (id, date, type, title)
    to_save = []
    for doc in processed_documents:
        if isinstance(doc, tuple) and len(doc) == 4:
            to_save.append(doc)
        else:
            # Fallback for existing tuples with 3 items
            to_save.append(doc + ("No title",))
    with open("processed_documents.json", "w") as f:
        json.dump(to_save, f)

    # Loop through the documents in the order they are fetched
    for doc in documents:
        # Generate the document link using the publishedDocumentId
        doc_link = f"https://ec.europa.eu/transparency/documents-request/search/document-details/{doc['publishedDocumentId']}"
        
        # Use the disclosureDate if you want to display it, but keep the original order
        try:
            disclosure_date = datetime.datetime.strptime(doc['disclosureDate'], "%Y-%m-%d").date()
        except ValueError:
            disclosure_date = datetime.datetime.now().date()  # Default to current date if parsing fails

        # Add each document as an RSS feed item
        feed.add_item(
            title=doc['documentTitle'],
            link=doc_link,
            description=doc['documentTitle'],
            pubdate=disclosure_date,
            unique_id=doc['publishedDocumentId'],
            categories=[doc['disclosureType']],
        )

    # Generate RSS feed XML as a string
    xml_str = feed.writeString("utf-8")

    # Pretty-print the XML with indentation
    xml_str_pretty = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

    # Save the formatted XML to the file
    with open("feed.xml", "w") as f:
        f.write(xml_str_pretty)

# Fetch data and process pagination
def fetch_data():
    existing_documents = load_existing_documents()  # Set of tuples
    new_documents = []

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

                if unique_key in existing_documents:
                    # Stop if we reach an already processed document
                    break

                new_documents.append(doc)
                existing_documents.add(unique_key)

            if len(documents) == 0 or unique_key in existing_documents:
                break

            page_num += 1

        else:
            print(f"Failed to fetch page {page_num}, Status Code: {response.status_code}")
            break

    # Combine existing documents (from JSON) and new ones
    all_docs = list(new_documents)

    # Load previously saved documents (for building the feed)
    try:
        with open("processed_documents.json", "r") as f:
            prev_docs = json.load(f)
            # Convert back to dict format if needed
            for doc_tuple in prev_docs:
                doc_dict = {
                    "publishedDocumentId": doc_tuple[0],
                    "disclosureDate": doc_tuple[1],
                    "disclosureType": doc_tuple[2],
                    "documentTitle": doc_tuple[3] if len(doc_tuple) > 3 else "No title"
                }
                all_docs.append(doc_dict)
    except FileNotFoundError:
        pass

    # Keep only the last 250 entries
    all_docs = all_docs[:250]

    # Create or update RSS feed
    if all_docs:
        create_rss_feed(all_docs)

    # Save updated document info
    save_processed_documents(existing_documents)










