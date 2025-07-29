import gradio as gr
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os
import pandas as pd

# (Apenas para testes locais)
from dotenv import load_dotenv
load_dotenv()

# 🛡️ Ler credenciais (variáveis de ambiente)
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# 🔹 Ler o Excel com os alojamentos
try:
    df = pd.read_excel("alojamentos.xlsx")
except FileNotFoundError:
    raise RuntimeError("❌ Ficheiro 'alojamentos.xlsx' não encontrado.")

# 🔎 Obter nome a partir do registo
def obter_nome_do_registo(registo):
    resultado = df[df['Registo'].astype(str).str.strip() == str(registo).strip()]
    if not resultado.empty:
        return str(resultado.iloc[0]['Nome'])
    return "Desconhecido"

# 🧾 Gerar PDF personalizado
def gerar_pdf(email, registo, nome):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    imagem_path = "logo.png"
    if os.path.exists(imagem_path):
        pdf.image(imagem_path, x=10, y=8, w=50)
        pdf.ln(40)
    else:
        pdf.cell(200, 10, txt="BILHETE DIGITAL", ln=True, align="C")
        pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="FICA QUE COMPENSA", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"NOME DO ESTABELECIMENTO: {nome}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Email: {email}", ln=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="TERRAS DE BOURO", ln=True)
    pdf.set_font("Arial", 'I', 11)
    pdf.cell(200, 10, txt="NO CORAÇÃO DA NATUREZA", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Este bilhete dá desconto em:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="* Museu do Geira - Entrada Grátis", ln=True)
    pdf.cell(200, 10, txt="* Museu de Vilarinho da Furna - Entrada Grátis", ln=True)
    pdf.cell(200, 10, txt="* Embarcação Rio Caldo - 50% (sujeito a reserva e disponibilidade)", ln=True)

    os.makedirs("pdfs", exist_ok=True)
    registo_limpo = "".join(c for c in registo if c.isalnum() or c in ('-_'))
    email_limpo = email.replace('@', '_').replace('.', '_')
    caminho_pdf = f"pdfs/checkin_{email_limpo}_{registo_limpo}.pdf"
    pdf.output(caminho_pdf)
    return caminho_pdf

# 📧 Enviar e-mail
def enviar_email(email_destino, caminho_pdf):
    msg = EmailMessage()
    msg['Subject'] = 'Confirmação de Check-in'
    msg['From'] = EMAIL_USER
    msg['To'] = email_destino
    msg.set_content("Olá!\n\nEm anexo segue o comprovativo da tua visita ao local.\n\nCumprimentos.")

    with open(caminho_pdf, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(caminho_pdf))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

# 🎯 Função principal chamada pela interface
def checkin(email, registo):
    if "@" not in email:
        return "❌ Email inválido. Tenta novamente."

    nome = obter_nome_do_registo(registo)
    caminho_pdf = gerar_pdf(email, registo, nome)

    try:
        enviar_email(email, caminho_pdf)
        return f"✅ PDF enviado para {email} com sucesso!"
    except Exception as e:
        return f"❌ Erro ao enviar o e-mail: {e}"

# 🌐 Interface Gradio
with gr.Blocks(title="Check-in no Local 📍") as demo:
    gr.HTML("""
        <style>
            footer {display: none !important;}
            .svelte-1ipelgc {display: none !important;} /* botão "Usar via API" */
            .svelte-1f354aw {display: none !important;} /* botão "Configurações" (⚙️) */
        </style>
    """)
    gr.Markdown("## 📍 Check-in no Local")
    registo_input = gr.Textbox(label="🔑 Código de Registo (do QR Code)", placeholder="ex: 12345")
    email_input = gr.Textbox(label="✉️ E-mail", placeholder="ex: nome@email.com")
    resultado = gr.Textbox(label="Resultado", interactive=False)
    enviar = gr.Button("📨 Enviar Comprovativo por E-mail")
    enviar.click(fn=checkin, inputs=[email_input, registo_input], outputs=resultado)

# 🚀 Lançar app (usar share=True localmente se quiseres partilhar temporariamente)
demo.launch()  # ou demo.launch(share=True)
