import feedgenerator
import json
import os

# Create the RSS feed
def create_rss_feed(documents):
    feed = feedgenerator.Rss201rev2Feed(
        title="EU Documents RSS Feed",
        link="https://github.com/username/repository",
        description="Latest documents from the EU Transparency Portal"
    )
    
    for doc in documents:
        # Generate the document link using the publishedDocumentId
        doc_link = f"https://ec.europa.eu/transparency/documents-request/search/document-details/{doc['publishedDocumentId']}"
        
        feed.add_item(
            title=doc['documentTitle'],
            link=doc_link,
            description=doc['documentTitle'],
            pubdate=doc['disclosureDate'],
            unique_id=doc['publishedDocumentId'],
            categories=[doc['disclosureType']],
        )

    # Save the RSS feed to a file
    with open("feed.xml", "w") as f:
        f.write(feed.writeString("utf-8"))
