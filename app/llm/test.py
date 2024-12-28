
def list_collections():
    "code to list all collections in ChromaDB"
    from chromadb import PersistentClient

    # Path to the ChromaDB persistent storage
    chromaDB_path = "/ChromaDBPersistent"

    # Initialize the ChromaDB client
    chroma_client = PersistentClient(path=chromaDB_path)

    # List all existing collections
    collections = chroma_client.list_collections()

    # Print the names of the collections
    print("Existing Collections in ChromaDB:")
    for collection in collections:
        print(f"Name: {collection.name}")
# *******************************************************************
#
# "code to delete a collection in ChromaDB"
# from chromadb import PersistentClient
# # # # Path to the ChromaDB persistent storage
# chromaDB_path = "/ChromaDBPersistent"
# #
# # # # Initialize the ChromaDB client
# chroma_client = PersistentClient(path=chromaDB_path)
# # #
# # # # List all existing collections
# collections = chroma_client.list_collections()
# # #
# # # # Delete each collection
# print("Deleting all collections...")
# for collection in collections:
#      collection_name = collection.name
#      chroma_client.delete_collection(collection_name)
#      print(f"Deleted collection: {collection_name}")
# #
# # # # Verify that all collections are deleted
# remaining_collections = chroma_client.list_collections()
# if not remaining_collections:
#      print("All collections have been successfully deleted.")
# else:
#      print("Some collections remain:", [c.name for c in remaining_collections])

#list_collections()

def list_collections_and_documents():
    from chromadb import PersistentClient

    chromaDB_path = "/ChromaDBPersistent"  # ChromaDB yolu
    chroma_client = PersistentClient(path=chromaDB_path)

    # Koleksiyonları listele
    collections = chroma_client.list_collections()
    print("Existing Collections in ChromaDB:")
    for collection in collections:
        print(f"Collection Name: {collection.name}")
        try:
            # Koleksiyonu al ve dökümanları listele
            current_collection = chroma_client.get_collection(name=collection.name)
            documents = current_collection.get()
            print("Documents in the Collection:")
            print(documents)  # Dökümanları yazdır
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")




# Call the function
list_collections_and_documents()
