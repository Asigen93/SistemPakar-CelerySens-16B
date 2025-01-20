from flask import Flask, render_template, request, session, redirect, url_for
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import re
from datetime import datetime

# Memuat variabel lingkungan
load_dotenv()

# Inisialisasi aplikasi Flask
app = Flask(__name__)
app.secret_key = "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"
app.config["SESSION_PERMANENT"] = True

# Inisialisasi model untuk pertanyaan dan jawaban
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, max_tokens=None, timeout=None)

# Prompt template untuk sistem
prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            "Anda adalah CelerySens, sebuah Asisten tanaman seledri yang siap membantu Anda merawat tanaman seledri dengan solusi yang tepat dan efektif. Tugas Anda adalah mendiagnosa gejala yang disebutkan dengan cepat dan jelas, termasuk menyebutkan nama ilmiah penyakit jika relevan sesuai dataset"
            "Anda menjelaskan penyebab masalah tanaman dengan cara yang mudah dipahami."
            "Jawaban Anda harus ringkas, langsung ke inti dan tidak butuh data berupa gambar."
            "Anda berkomunikasi dengan ramah dan memberikan motivasi agar Anda semangat merawat tanaman Anda."
            "Anda akan mengingat detail yang Anda sebutkan di percakapan kita."
            "Anda dikembangkan oleh Tirta Romadhon Cipta Saputra dan Billy Jes, mahasiswa Universitas Muhammadiyah Sorong Program Studi Teknik Informatika."
            "Sumber data yang digunakan berasal dari seorang pakar bernama Han Aldianova, mahasiswa Universitas Brawijaya yang telah tersertifikasi BNSP di bidang Pertanian."
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
)

# Menggunakan ConversationBufferMemory untuk menyimpan percakapan
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Membuat LLMChain dengan memory
conversation_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True,
    memory=memory
)

# Format waktu
def get_current_time():
    return datetime.now().strftime("%H:%M")

# Format respon sebagai daftar
def format_response_as_list(text):
    if not text:
        return "<p>Jawaban tidak tersedia.</p>"

    text = re.sub(r"(\d+)\.\s", r"<li>\1. ", text)
    if "<li>" in text:
        text = "<ul>" + text + "</ul>"
    return text

# Menghasilkan jawaban dari inputan
def dapatkan_jawaban(pertanyaan):
    try:
        hasil = conversation_chain.run(question=pertanyaan)
        return f"<p>{hasil.strip()}</p>"
    except Exception as e:
        error_message = f"Terjadi kesalahan: {str(e)}"
        return f"<p>{error_message}</p>"

# Rute Flask
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    session.permanent = True
    if "history" not in session:
        session["history"] = []
    if request.method == "POST":
        pertanyaan = request.form.get("pertanyaan", "").strip()
        if pertanyaan:
            jawaban = dapatkan_jawaban(pertanyaan)
            session["history"].append({"role": "user", "text": pertanyaan, "time": get_current_time()})
            session["history"].append({"role": "bot", "text": jawaban, "time": get_current_time()})
            session.modified = True
            # Kembalikan jawaban dalam format JSON
            return {"jawaban": jawaban}
    return render_template("chat.html", history=session["history"])

@app.route("/clear_history", methods=["POST"])
def clear_history():
    session.pop("history", None)
    memory.clear()  # Bersihkan memory LangChain
    return redirect(url_for("chat"))

@app.before_request
def check_history_length():
    if len(session.get("history", [])) > 50:
        session.pop("history", None)
        memory.clear()  # Bersihkan memory LangChain jika riwayat terlalu panjang

# Menjalankan aplikasi
if __name__ == "__main__":
    app.run(debug=True)
