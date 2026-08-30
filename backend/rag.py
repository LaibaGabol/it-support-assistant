# backend/rag.py
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os

#code connecting to Azure AI search
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)
#find 3 most relevant pieces of information
def retrieve_context(query: str, top_k: int = 3):
    results = search_client.search(
        search_text=query,
        top=top_k,
        select=["chunk", "title"]
    )
    return [
        {"content": r["chunk"], "source": r.get("title")}
        for r in results
    ]