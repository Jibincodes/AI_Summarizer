import string
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, \
    QMessageBox, QRadioButton, QHBoxLayout, QButtonGroup
import requests
from bs4 import BeautifulSoup
from transformers import BartForConditionalGeneration, BartTokenizer, BertTokenizer, BertForQuestionAnswering, LongformerTokenizer, LongformerModel
import torch
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from textwrap import wrap
# for extracting from PDF
import fitz
import re
#------------------------------------
#from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain_community.document_loaders import PyPDFLoader
#import pypdf
#import sentencepiece
#----------------------------------------------------------------
# for extractive summarization
import numpy as np
import networkx as nx
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
import nltk
nltk.download('punkt')
nltk.download('stopwords')
#---------------------------------------------------------------
# using the BART model for summarization
# according to huggingface documentation, the BART model is one of the best for summarization tasks
# the model is trained on CNN/DailyMail dataset
model_name = 'facebook/bart-large-cnn'
tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)
#----------------------------------------
# using the Longformer model for handling longer texts
longformer_model_name = 'allenai/longformer-base-4096'
longformer_tokenizer = LongformerTokenizer.from_pretrained(longformer_model_name)
longformer_model = LongformerModel.from_pretrained(longformer_model_name)

# using the BERT model for question answering
#bert_model_name = 'distilbert-base-uncased-distilled-squad'
bert_model_name = 'bert-large-uncased-whole-word-masking-finetuned-squad'
bert_tokenizer = BertTokenizer.from_pretrained(bert_model_name)
bert_model = BertForQuestionAnswering.from_pretrained(bert_model_name)
#----------------------------------------

class SummarizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.pdf_text = ""

    # Setting up the UI components
    def initUI(self):
        self.setWindowTitle('AI Summarizer')

        layout = QVBoxLayout()
        #---------------------------------------
        # adding radio buttons to choose between summarization feature for url or pdf
        self.url_radio = QRadioButton('URL')
        self.pdf_radio = QRadioButton('PDF')
        self.url_radio.setChecked(True)

        self.radio_layout = QHBoxLayout()
        self.radio_layout.addWidget(self.url_radio)
        self.radio_layout.addWidget(self.pdf_radio)

        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.url_radio)
        self.radio_group.addButton(self.pdf_radio)

        layout.addLayout(self.radio_layout)

        # adding new buttons to choose between abstractive and extractive summarization
        self.abstractive_radio = QRadioButton('Abstractive')
        self.extractive_radio = QRadioButton('Extractive')
        self.abstractive_radio.setChecked(True)

        self.summarization_radio_layout = QHBoxLayout()
        self.summarization_radio_layout.addWidget(self.abstractive_radio)
        self.summarization_radio_layout.addWidget(self.extractive_radio)

        self.summarization_radio_group = QButtonGroup()
        self.summarization_radio_group.addButton(self.abstractive_radio)
        self.summarization_radio_group.addButton(self.extractive_radio)

        layout.addLayout(self.summarization_radio_layout)
        #---------------------------------------
        self.url_label = QLabel('Enter the news Article URL:')
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit(self)
        layout.addWidget(self.url_input)

        self.upload_button = QPushButton('Upload PDF', self)
        self.upload_button.clicked.connect(self.upload_pdf)
        layout.addWidget(self.upload_button)

        self.summarize_button = QPushButton('Summarize', self)
        self.summarize_button.clicked.connect(self.summarize_article)
        layout.addWidget(self.summarize_button)

        self.summary_label = QLabel('Summary:')
        layout.addWidget(self.summary_label)

        self.summary_output = QTextEdit(self)
        self.summary_output.setReadOnly(True)
        layout.addWidget(self.summary_output)

        #decided to add a question answering feature
        self.question_label = QLabel('Enter the question:')
        layout.addWidget(self.question_label)

        self.question_input = QLineEdit(self)
        layout.addWidget(self.question_input)

        self.answer_button = QPushButton('To Answer', self)
        self.answer_button.clicked.connect(self.answer_question)
        layout.addWidget(self.answer_button)

        self.answer_label = QLabel('Answer:')
        layout.addWidget(self.answer_label)

        self.answer_output = QTextEdit(self)
        self.answer_output.setReadOnly(True)
        layout.addWidget(self.answer_output)

        #new export to pdf button
        self.export_button = QPushButton('Export as PDF', self)
        self.export_button.clicked.connect(self.export_to_pdf)
        layout.addWidget(self.export_button)
        #-------------------------------------------
        self.setLayout(layout)

    def summarize_article(self):
     if self.url_radio.isChecked():
        url = self.url_input.text()
        article_text = self.get_article_text(url)
        if article_text:
            summary = self.summarize_text(article_text)
            self.summary_output.setText(summary)
        else:
            self.summary_output.setText("Could not fetch article text. Please check the URL and try again.")
     elif self.pdf_radio.isChecked():
         if self.pdf_text:
             summary = self.summarize_text(self.pdf_text)
             #summary = self.summarize_text_with_gemini(self.pdf_text)
             self.summary_output.setText(summary)
         else:
             self.summary_output.setText("Please upload a PDF file to summarize.")


    # Function to fetch the article text from the URL using paragraph tags
    def get_article_text(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            article_text = ' '.join([para.get_text() for para in paragraphs])
            return article_text
        except Exception as e:
            print(f"Error fetching article: {e}")
            return None

    def summarize_text(self, text):
        if self.abstractive_radio.isChecked():
            return self.abstractive_summarize(text)
        else:
            #return self.extractive_summarize(text, num_sentences=10)
            return self.extractive_summary_textrank(text, num_sentences=10)
            #return self.extractive_summary_tfidf(text, num_sentences=10)

    def abstractive_summarize(self, text):
        #-----------------------------------------------
        #spliting the text into chunks of 4096 tokens
        chunk_size = 4096
        overlap = 512 #to maintain the context
        tokens = longformer_tokenizer.encode(text)
        chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size - overlap)]

        summaries = []
        for chunk in chunks:
            #convert the chunk to a tensor
            #inputs = torch.tensor(chunk).unsqueeze(0)
            #with torch.no_grad():
            #    outputs = longformer_model(inputs)

            #-----------------------------------------------
            #get the summary using BART model
            chunk_text = longformer_tokenizer.decode(chunk, skip_special_tokens=True)
            bart_inputs = tokenizer.encode("summarize: " + chunk_text, return_tensors='pt', max_length=1024, truncation=True)
            #inputs = t5_tokenizer.encode("summarize: " + chunk_text, return_tensors='pt', max_length=1024, truncation=True)
             # generate the summary output using beam search
            summary_ids = model.generate(bart_inputs, max_length=600, min_length=300, length_penalty=2.0, num_beams=4,
                                     early_stopping=True)
            #summary_ids = t5_model.generate(inputs, max_length=600, min_length=300, length_penalty=2.0, num_beams=4, early_stopping=True)

            # decode the summary output and remove the special tokens
            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            #summary = t5_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            summaries.append(summary)

        combined_summary = ' '.join(summaries)
        # Now summarize the combined summary text
        #bart_inputs = tokenizer.encode("summarize: " + combined_summary, return_tensors='pt', max_length=1024,
        #                               truncation=True)
        #summary_ids = model.generate(bart_inputs, max_length=600, min_length=300, length_penalty=2.0, num_beams=8,
        #                             early_stopping=True)
        #final_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return combined_summary

    #-------------------------------------------------------
    #this is the extractive summarization using the textrank algorithm
    def sentence_similarity(self, sent1, sent2, stopwords=None):
        if stopwords is None:
            stopwords = []

        sent1 = [w.lower() for w in word_tokenize(sent1) if w.lower() not in stopwords and w not in string.punctuation]
        sent2 = [w.lower() for w in word_tokenize(sent2) if w.lower() not in stopwords and w not in string.punctuation]

        all_words = list(set(sent1 + sent2))

        vector1 = [0] * len(all_words)
        vector2 = [0] * len(all_words)

        for w in sent1:
            vector1[all_words.index(w)] += 1

        for w in sent2:
            vector2[all_words.index(w)] += 1

        return cosine_similarity([vector1], [vector2])[0][0]

    def build_similarity_matrix(self, sentences, stop_words):
        similarity_matrix = np.zeros((len(sentences), len(sentences)))

        for idx1 in range(len(sentences)):
            for idx2 in range(len(sentences)):
                if idx1 != idx2:
                    similarity_matrix[idx1][idx2] = self.sentence_similarity(sentences[idx1], sentences[idx2],
                                                                             stop_words)

        return similarity_matrix

    def extractive_summary_textrank(self, text, num_sentences=10):
        stop_words = stopwords.words('english')
        sentences = sent_tokenize(text)

        sentence_similarity_matrix = self.build_similarity_matrix(sentences, stop_words)
        sentence_similarity_graph = nx.from_numpy_array(sentence_similarity_matrix)
        scores = nx.pagerank(sentence_similarity_graph)

        ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)

        summarize_text = [ranked_sentences[i][1] for i in range(min(num_sentences, len(ranked_sentences)))]
        return " ".join(summarize_text)
    #this is the end of extractive summarization

    # Function to answer the question based on the article text
    def answer_question(self):
        #url = self.url_input.text()
        #article_text = self.get_article_text(url)
        question = self.question_input.text()
        context = self.summary_output.toPlainText()
        if question and context:
        #if question and article_text:
            #answer = self.get_answer(question, article_text)
            answer = self.get_answer(question, context)
            self.answer_output.setText(answer)
        else:
            self.answer_output.setText("Please provide a valid question.")

    # Function to get the answer using the BERT model
    def get_answer(self, question, context):
     try:
        # encode the question and context using the BERT tokenizer
        inputs = bert_tokenizer.encode_plus(question, context, add_special_tokens=True, return_tensors='pt', max_length=512, truncation=True)
        #convert the input ids to a list and to get the tokens
        input_ids = inputs['input_ids'].tolist()[0]
        text_tokens = bert_tokenizer.convert_ids_to_tokens(input_ids)

        #getting the answer with the help of the BERT model (using attention mask and feed forward)
        outputs = bert_model(**inputs)
        answer_start_scores = outputs.start_logits
        answer_end_scores = outputs.end_logits
        # get the answer by finding the tokens with the highest start and end scores
        answer_start = torch.argmax(answer_start_scores)
        answer_end = torch.argmax(answer_end_scores) + 1

        answer = bert_tokenizer.convert_tokens_to_string(bert_tokenizer.convert_ids_to_tokens(input_ids[answer_start:answer_end]))
        return answer
     except Exception as e:
        print(f"Error getting answer: {e}")
        return "Sorry, I could not find an answer to your question. Please try again."

    #function to export the summary to a pdf file
    def export_to_pdf(self):
        summary = self.summary_output.toPlainText()
        if summary:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Summary as PDF", "",
                                                       "PDF Files (*.pdf);;All Files (*)", options=options)
            if file_path:
                self.save_pdf(file_path, summary)
        else:
            self.answer_output.setText("No summary to export.")
    def save_pdf(self, file_path, summary):
     try:
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        c.drawString(100, height - 100, "Summary:")
        text = c.beginText(100, height - 120)
        text.setFont("Times-Roman", 12)
        wrapped_text = wrap(summary, 80)  # Wrap text at 80 characters
        for line in wrapped_text:
            text.textLine(line)
        c.drawText(text)
        c.save()
        QMessageBox.information(self, "PDF Saved", "The summary has been successfully saved as a PDF.")
     except Exception as e:
        QMessageBox.critical(self, "Error", f"Error saving PDF: {e}")

    #function to upload the pdf file and extract the text
    def upload_pdf(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_path:
            #self.pdf_text = self.file_preprocessing(file_path)
            self.pdf_text = self.get_pdf_text(file_path)
            if self.pdf_text:
                self.summary_output.setText("PDF uploaded successfully. Click 'Summarize' to get the summary.")
            else:
                self.summary_output.setText("Could not extract text from PDF. Please try again.")

    #function to clean the text
    def clean_text(self, text):
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    #function to extract the text from the PDF file
    def get_pdf_text(self, file_path):
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("blocks")  # Get text blocks

                # Sorting the blocks by their vertical and then horizontal positions
                blocks.sort(key=lambda b: (b[1], b[0]))

                for block in blocks:
                    text += block[4]  # Extract the actual text from the block
                    text += "\n"  # newline to separate blocks

                text += "\n"  # newline to separate pages

            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None

    #function is not used, this is an alternative to the get_pdf_text function
    """def file_preprocessing(self, file):
        try:
            # Load PDF file
            print(f"Loading PDF file: {file}")
            loader = PyPDFLoader(file)
            pages = loader.load_and_split()
            print(f"Number of pages extracted: {len(pages)}")

            # Initializing the text splitter with the decided chunk size and overlap
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

            # Split documents into chunks
            texts = text_splitter.split_documents(pages)
            print(f"Number of text chunks created: {len(texts)}")

            # Combine chunks into a single string
            final_texts = ""
            for text in texts:
                final_texts += text.page_content
                # just printing the length of the chunk
                print(f"Chunk length: {len(text.page_content)}")

            if not final_texts.strip():
                print("Warning: Extracted text is empty.")

            return final_texts

        except FileNotFoundError:
            print(f"Error: File not found {file}.")
            return ""
        except Exception as e:
            print(f"Error processing file {file}: {e}")
            return "" """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SummarizerApp()
    ex.resize(1000, 800)
    ex.show()
    sys.exit(app.exec_())
