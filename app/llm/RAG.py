import chromadb
import google.generativeai as genai
import textwrap
from IPython.display import display
from IPython.display import Markdown
from fpdf import FPDF
from docx import Document
import os
import comtypes.client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from chromadb import Client, PersistentClient
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from chromadb import Client, PersistentClient
from chromadb.utils import embedding_functions
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_community.document_loaders import PyPDFLoader

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class ChromaDBManager:
    def __init__(self, chromaDB_path, collection_name, model_name):
        # self.chromaDB_path = chromaDB_path
        self.chromaDB_path = os.path.abspath(chromaDB_path)
        self.collection_name = collection_name
        self.model_name = model_name
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.model_name
        )
        self.chroma_client, self.chroma_collection = self.create_chroma_client()

    def create_chroma_client(self):
        if self.chromaDB_path is not None:
            chroma_client = PersistentClient(
                path=self.chromaDB_path,
                settings=Settings(),
                tenant=DEFAULT_TENANT,
                database=DEFAULT_DATABASE,
            )
        else:
            chroma_client = Client()

        chroma_collection = chroma_client.get_or_create_collection(
            self.collection_name, embedding_function=self.embedding_function
        )

        return chroma_client, chroma_collection

    def add_document_to_collection(self, ids, metadatas, text_chunksinTokens):
        print("Before inserting, the size of the collection: ", self.chroma_collection.count())
        self.chroma_collection.add(ids=ids, metadatas=metadatas, documents=text_chunksinTokens)
        print("After inserting, the size of the collection: ", self.chroma_collection.count())
        return self.chroma_collection

    def retrieve_docs(self, query, n_results=7, return_only_docs=False):
        results = self.chroma_collection.query(
            query_texts=[query],
            include=["documents", "metadatas", 'distances'],
            n_results=n_results
        )


        if return_only_docs:
            return results['documents'][0]
        else:
            return results


class FileConverter:
    def convert_to_pdf(self, file):
        name, extension = os.path.splitext(file)
        if extension == '.pdf':
            return file
        if extension == '.txt':
            print(f'Converting {file} to PDF...')
            return self.txt_to_pdf(file, f"{name}.pdf")
        elif extension == '.docx':
            print(f'Converting {file} to PDF...')
            return self.docx_to_pdf(file, f"{name}.pdf")
        elif extension == '.pptx':
            print(f'Converting {file} to PDF...')
            return self.pptx_to_pdf(file, f"{name}.pdf")
        else:
            print(f'Unsupported file format: {extension}')
            return None

    def txt_to_pdf(self, input_file, output_file):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        try:
            with open(input_file, 'r', encoding='utf-8') as file:
                for line in file:
                    pdf.cell(200, 10, txt=line.strip(), ln=True)
            pdf.output(output_file)
            print(f'TXT file converted to PDF: {output_file}')
            return output_file
        except Exception as e:
            print(f"Error converting TXT to PDF: {e}")
            return None

    def docx_to_pdf(self, input_file, output_file):
        try:
            document = Document(input_file)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            for paragraph in document.paragraphs:
                pdf.multi_cell(0, 10, paragraph.text)

            pdf.output(output_file)
            print(f'DOCX file converted to PDF: {output_file}')
            return output_file
        except Exception as e:
            print(f"Error converting DOCX to PDF: {e}")
            return None

    def pptx_to_pdf(self, input_file, output_file):
        try:
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            powerpoint.Visible = 1
            presentation = powerpoint.Presentations.Open(input_file)
            presentation.SaveAs(output_file, 32)  # 32 = PDF format
            presentation.Close()
            powerpoint.Quit()
            print(f'PPTX file converted to PDF: {output_file}')
            return output_file
        except Exception as e:
            print(f"Error converting PPTX to PDF: {e}")
            return None


class TextProcessor:
    @staticmethod
    def convert_page_chunk_in_char(pdf_file, chunk_size=1500, chunk_overlap=0):
        loader = PyPDFLoader(pdf_file)
        pdf_texts = loader.load()

        character_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " ", ""],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        pdf_text_content = '\n\n'.join([doc.page_content for doc in pdf_texts])
        character_split_texts = character_splitter.split_text(pdf_text_content)

        print(f"\nTotal number of chunks (document split by max char = {chunk_size}): {len(character_split_texts)}")
        return character_split_texts

    @staticmethod
    def convert_chunk_token(text_chunksinChar, sentence_transformer_model, chunk_overlap=0, tokens_per_chunk=128):
        token_splitter = SentenceTransformersTokenTextSplitter(
            chunk_overlap=chunk_overlap,
            model_name=sentence_transformer_model,
            tokens_per_chunk=tokens_per_chunk
        )

        text_chunksinTokens = []
        for text in text_chunksinChar:
            text_chunksinTokens += token_splitter.split_text(text)
        print(f"\nTotal number of chunks (document split by 128 tokens per chunk): {len(text_chunksinTokens)}")
        return text_chunksinTokens

    @staticmethod
    def add_meta_data(text_chunksinTokens, title, category, initial_id):
        ids = [str(i + initial_id) for i in range(len(text_chunksinTokens))]
        metadata = {
            'document': title,
            'category': category
        }
        metadatas = [metadata for _ in range(len(text_chunksinTokens))]
        return ids, metadatas

class RetrieveDocuments:
    def __init__(self, chromaDB_path: str, collection_name: str, model_name: str):
        """
        Initialize the retrieval process with ChromaDB.
        """
        self.chroma_manager = ChromaDBManager(
            chromaDB_path=chromaDB_path,
            collection_name=collection_name,
            model_name=model_name
        )

    def retrieve_documents(self, query: str, n_results: int = 5):
        """
        Retrieve documents using a given query.

        Args:
            query (str): The user query to perform semantic search.
            n_results (int): Number of top results to retrieve.

        Returns:
            list: Retrieved documents.
        """
        try:
            # Retrieve documents based on the query
            retrieved_docs = self.chroma_manager.retrieve_docs(query, n_results=n_results, return_only_docs=True)
            print(f"\nRetrieved {len(retrieved_docs)} documents for query: '{query}'")
            for idx, doc in enumerate(retrieved_docs):
                print(f"Document {idx + 1}: {doc[:100]}...")  # Print a snippet of each document

            return retrieved_docs

        except Exception as e:
            print(f"An error occurred during retrieval: {str(e)}")
            return []

class GeminiManager:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def chat(self, query, retrieved_documents):
        context = "\n".join(retrieved_documents['documents'][0])
        prompt = f"Based on the following context, answer the query:\n\nContext:\n{context}\n\nQuery:\n{query}"
        response = self.model.generate_content(prompt)
        return response.text


"""
if __name__ == "__main__":
    chromaDB_path = '/ChromaDBPersistent'
    collection_name= "econ_collection"
    sentence_transformer_model = "distiluse-base-multilingual-cased-v1"

    chroma_manager = ChromaDBManager(chromaDB_path, collection_name, sentence_transformer_model)
    text_processor = TextProcessor()

    pdf_file = "note.pdf"
    chunk_size = 1500
    chunk_overlap = 0

    text_chunksinChar = text_processor.convert_page_chunk_in_char(pdf_file, chunk_size, chunk_overlap)
    text_chunksinTokens = text_processor.convert_chunk_token(text_chunksinChar, sentence_transformer_model)
    ids, metadatas = text_processor.add_meta_data(text_chunksinTokens, title="Chapter 1", category="PDF", initial_id=0)
    chroma_collection = chroma_manager.add_document_to_collection(ids, metadatas, text_chunksinTokens)
"""
# def create_embedding_collection(
#         input_file: str,
#         collection_name: str,
#         chunk_size: int = 1500,
#         chunk_overlap: int = 0,
#         title: str = "Untitled",
#         category: str = "PDF",
#         initial_id: int = 0,
#         chromaDB_path: str = "/ChromaDBPersistent",
#         sentence_transformer_model: str = "distiluse-base-multilingual-cased-v1"
# ):
#     """
#     Processes a PDF file to create text embeddings and store them in a ChromaDB collection.
#
#     Args:
#         input_file (str): Path to the PDF file.
#         chromaDB_path (str): Path to the ChromaDB storage.
#         collection_name (str): Name of the ChromaDB collection.
#         sentence_transformer_model (str): Sentence transformer model for embeddings.
#         chunk_size (int): Maximum size of each text chunk (in characters). Default is 1500.
#         chunk_overlap (int): Number of overlapping characters between chunks. Default is 0.
#         title (str): Title metadata for the document. Default is "Untitled".
#         category (str): Category metadata for the document. Default is "PDF".
#         initial_id (int): Starting ID for the document chunks. Default is 0.
#
#     Returns:
#         ChromaDB collection object after adding the processed document.
#     """
#     converter = FileConverter()
#     converted_pdf_file = converter.convert_to_pdf(input_file)
#
#     # Initialize ChromaDB manager and text processor
#     chroma_manager = ChromaDBManager(chromaDB_path, collection_name, sentence_transformer_model)
#     text_processor = TextProcessor()
#
#     # Step 1: Split PDF content into character chunks
#     text_chunksinChar = text_processor.convert_page_chunk_in_char(converted_pdf_file, chunk_size, chunk_overlap)
#
#     # Step 2: Convert character chunks into token-based chunks
#     text_chunksinTokens = text_processor.convert_chunk_token(text_chunksinChar, sentence_transformer_model)
#
#     # Step 3: Add metadata to the chunks
#     ids, metadatas = text_processor.add_meta_data(text_chunksinTokens, title=title, category=category, initial_id=initial_id)
#
#     # Step 4: Add processed chunks to ChromaDB collection
#     chroma_collection = chroma_manager.add_document_to_collection(ids, metadatas, text_chunksinTokens)
#
#     return chroma_collection

def create_embedding_collection(
        input_files: list,
        collection_name: str,
        chunk_size: int = 1500,
        chunk_overlap: int = 0,
        chromaDB_path: str = "/ChromaDBPersistent",
        sentence_transformer_model: str = "distiluse-base-multilingual-cased-v1"
):
    """
    Processes multiple input files to create text embeddings and store them in a ChromaDB collection.

    Args:
        input_files (list): List of file paths.
        collection_name (str): Name of the ChromaDB collection.
        chunk_size (int): Maximum size of each text chunk (in characters). Default is 1500.
        chunk_overlap (int): Overlap between text chunks. Default is 0.
        chromaDB_path (str): Path to the ChromaDB storage.
        sentence_transformer_model (str): Model used for creating embeddings.

    Returns:
        ChromaDB collection object.
    """
    converter = FileConverter()
    chroma_manager = ChromaDBManager(chromaDB_path, collection_name, sentence_transformer_model)
    text_processor = TextProcessor()

    all_ids, all_metadatas, all_text_chunksinTokens = [], [], []
    current_id = 0

    for file in input_files:
        pdf_file = converter.convert_to_pdf(file)
        if pdf_file is not None:
            text_chunks = text_processor.convert_page_chunk_in_char(pdf_file, chunk_size, chunk_overlap)
            token_chunks = text_processor.convert_chunk_token(text_chunks, sentence_transformer_model)

            ids, metadatas = text_processor.add_meta_data(
                token_chunks,
                title=file.split('/')[-1],
                category="Document",
                initial_id=current_id
            )

            all_ids.extend(ids)
            all_metadatas.extend(metadatas)
            all_text_chunksinTokens.extend(token_chunks)
            current_id += len(ids)

    return chroma_manager.add_document_to_collection(all_ids, all_metadatas, all_text_chunksinTokens)


"""
if __name__ == "__main__":
    # Parametreler
    pdf_file = "note.pdf"
    chromaDB_path = "/ChromaDBPersistent"
    collection_name = "econ_collection"
    sentence_transformer_model = "distiluse-base-multilingual-cased-v1"
    chunk_size = 1500
    chunk_overlap = 0
    title = "Chapter 1"
    category = "PDF"
    initial_id = 0

    # Fonksiyon çağrısı
    chroma_collection = create_embedding_collection(
        pdf_file=pdf_file,
        chromaDB_path=chromaDB_path,
        collection_name=collection_name,
        sentence_transformer_model=sentence_transformer_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        title=title,
        category=category,
        initial_id=initial_id
    )

    print(f"Collection created successfully with {chroma_collection.count()} documents!")
"""