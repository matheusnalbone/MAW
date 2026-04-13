import streamlit as st
import requests
import base64
import urllib.parse
import time
import tempfile
import os
from io import BytesIO
from PIL import Image

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E CSS SINESTÉSICO
# ==========================================
st.set_page_config(page_title="Marlon Artworks | Studio Elite", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@400;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0A0A0A; color: #F7F7F7; font-family: 'Josefin Sans', sans-serif;
    }
    h1, h2, h3 { font-family: 'Josefin Sans', sans-serif !important; text-transform: uppercase; letter-spacing: 0.05em; }
    
    .stButton>button {
        background-color: #F7F7F7 !important; color: #0A0A0A !important; border: none !important;
        border-bottom: 4px solid #D91414 !important; border-radius: 0px !important; padding: 1rem !important;
        font-family: 'Josefin Sans', sans-serif !important; text-transform: uppercase; font-weight: 700;
        letter-spacing: 0.1em; width: 100%; transition: all 0.2s ease-in-out;
    }
    .stButton>button:active { transform: scale(0.98); border-bottom: 1px solid #D91414 !important; }

    .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div>div {
        background-color: #0A0A0A !important; color: #F7F7F7 !important; border: 1px solid rgba(247,247,247,0.15) !important;
        border-radius: 0px !important; font-family: 'Josefin Sans', sans-serif !important;
    }

    .tech-label { color: #D91414; font-size: 0.8rem; letter-spacing: 0.3em; text-transform: uppercase; font-weight: 800; margin-bottom: 0.5rem; }
    .book-container { border-left: 2px solid #D91414; padding: 20px; background: rgba(255,255,255,0.02); font-size: 1rem; line-height: 1.6; }
    
    /* CSS SINESTÉSICO DO QUIZ */
    .quiz-container {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        padding: 40px; margin-top: 20px; border-radius: 12px;
        background: linear-gradient(145deg, rgba(20,20,20,1) 0%, rgba(10,10,10,1) 100%);
        border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        min-height: 350px;
    }
    .quiz-fase-mcq { border-top: 3px solid #D91414; }
    .quiz-fase-escala { border-top: 3px solid #6366F1; }
    .quiz-fase-texto { border-top: 3px solid #F7F7F7; }
    
    .quiz-tema { font-size: 0.75rem; letter-spacing: 0.4em; color: #888; text-transform: uppercase; margin-bottom: 10px; }
    .quiz-pergunta { font-size: 1.8rem; font-weight: 700; text-align: center; margin-bottom: 30px; line-height: 1.3; }
    
    div[role="radiogroup"] { align-items: flex-start; justify-content: center; width: 100%; gap: 15px; flex-direction: column; }
    @media (min-width: 768px) { div[role="radiogroup"] { flex-direction: column; align-items: center; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SISTEMA DE COFRE (PROTEÇÃO CONTRA ERRO 403)
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # Se você for rodar no seu computador (sem ser na nuvem), cole a chave nova aqui dentro das aspas:
    API_KEY = "COLE_SUA_CHAVE_AQUI_SE_FOR_RODAR_LOCAL"

URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + API_KEY

# ==========================================
# ESTRUTURA PSICOLÓGICA DO QUIZ
# ==========================================
QUIZ_DATA = [
    {"fase": "mcq", "tema": "🔥 O RECARGA (MBTI)", "q": "Como você recarrega sua energia mental após uma semana exaustiva?", "opts": [
        "Isolamento total na natureza ou no silêncio profundo.", 
        "Criando algo, desenhando ou construindo com as mãos.", 
        "Saindo sem rumo, buscando estímulos e aventuras.", 
        "Rodeado de pessoas íntimas, em conversas profundas.", 
        "Praticando esportes extremos ou atividades intensas.", 
        "Organizando minha vida, limpando e planejando o futuro."]},
    {"fase": "mcq", "tema": "🛡️ CONFLITO (ENEAGRAMA)", "q": "Diante de uma crise inevitável, qual o seu instinto primitivo?", "opts": [
        "Analisar friamente a situação antes de tomar qualquer atitude.", 
        "Partir para o confronto imediato, com força e dominação.", 
        "Encontrar uma brecha no sistema e agir pelas sombras.", 
        "Tentar apaziguar os ânimos e buscar o equilíbrio.", 
        "Usar o humor e o sarcasmo como escudo psicológico.", 
        "Agir pela intuição pura, deixando o instinto guiar o caminho."]},
    {"fase": "mcq", "tema": "✒️ MOTIVAÇÃO", "q": "O que a tatuagem representa no seu corpo físico?", "opts": [
        "Uma armadura psicológica que me protege do mundo.", 
        "Um diário gravado na pele com minhas cicatrizes e memórias.", 
        "Um ato de rebeldia, retomando o controle do meu próprio corpo.", 
        "Uma expressão pura de estética, simetria e apreciação visual.", 
        "Um rito de passagem marcando minha evolução pessoal.", 
        "Uma forma de me conectar com meus ancestrais ou minhas raízes."]},
    {"fase": "mcq", "tema": "🎨 PALETA", "q": "Qual atmosfera visual mais atrai sua mente subconsciente?", "opts": [
        "Breu absoluto, sombras densas e contrastes dramáticos.", 
        "Vermelho sangue, fogo e cores quentes que pulsam vida.", 
        "Tons frios, névoa, azul profundo e melancolia invernal.", 
        "Cores elétricas, neon, vibrações caóticas e sintéticas.", 
        "Geometria pura, simetria em preto e branco absoluto.", 
        "Tons terrosos, orgânicos, madeira e natureza crua."]},
    {"fase": "mcq", "tema": "🧭 ARQUÉTIPO (JUNG)", "q": "Se sua vida fosse guiada por um único arquétipo, qual seria o seu condutor?", "opts": [
        "O Mago: Focado em transformar a realidade e entender o universo.", 
        "O Guerreiro: Focado na superação, na disciplina e na vitória.", 
        "O Amante: Guiado pela paixão, pela intimidade e pelos sentidos.", 
        "O Sábio: Em busca da verdade absoluta, livre de ilusões.", 
        "O Rebelde: Disposto a destruir o que não funciona para recriar as regras.", 
        "O Criador: Obcecado em deixar um legado estruturado e inovador."]},
    {"fase": "mcq", "tema": "⏳ TEMPO", "q": "Como você enxerga a passagem do tempo e o futuro?", "opts": [
        "O passado é um fantasma que me ensina e às vezes me assombra.", 
        "O presente é uma urgência, só existe o agora (Carpe Diem).", 
        "O futuro é um tabuleiro de xadrez que estou organizando.", 
        "O tempo é uma ilusão, vivo focado no fluxo contínuo.", 
        "Sinto que estou correndo contra o relógio para construir minha obra.", 
        "Sou indiferente ao tempo, as coisas acontecem quando têm que acontecer."]},
    {"fase": "mcq", "tema": "🌌 AMBIENTE MENTAL", "q": "Qual dessas paisagens mentais te traz mais conforto e pertencimento?", "opts": [
        "Uma metrópole chuvosa à noite, iluminada por neon (Cyberpunk).", 
        "Uma floresta densa e úmida, onde a natureza engoliu as ruínas.", 
        "Uma biblioteca antiga e infinita, cheia de mistérios e poeira.", 
        "O topo de uma montanha gélida e solitária, acima das nuvens.", 
        "Um templo esquecido, com incensos e monges silenciosos.", 
        "Um campo de batalha recém-terminado, sentindo o alívio da vitória."]},
    {"fase": "mcq", "tema": "🚫 A SOMBRA OPOSTA", "q": "O que te causa mais aversão ou repulsa no mundo atual?", "opts": [
        "A superficialidade e o vazio das relações modernas.", 
        "A falta de liberdade e a imposição de regras inúteis.", 
        "A fraqueza de caráter e a covardia diante de injustiças.", 
        "O excesso de barulho, o caos urbano e a falta de propósito.", 
        "A padronização, onde todos são forçados a ser e pensar igual.", 
        "A ignorância e a recusa da sociedade em enxergar a verdade."]},
    {"fase": "mcq", "tema": "📐 FORMA (TRADUÇÃO MOTORA)", "q": "Se sua mente fosse um tipo de linha, como ela seria desenhada?", "opts": [
        "Linhas orgânicas, sinuosas, como raízes que se espalham sem fim.", 
        "Formas geométricas perfeitas, ângulos retos e cálculos matemáticos.", 
        "Traços pesados, grossos, marcantes e indestrutíveis (Bold).", 
        "Pontos microscópicos que juntos formam um todo complexo (Pontilhismo).", 
        "Pinceladas caóticas, manchas expressivas e respingos violentos (Trash Polka).", 
        "Linhas extremamente finas, quase invisíveis, frágeis e detalhistas."]},
    {"fase": "mcq", "tema": "👁️ O EGO", "q": "Como você prefere que o mundo enxergue a sua tatuagem?", "opts": [
        "Como um manifesto agressivo: quero que vejam quem eu sou de longe.", 
        "Como uma obra de arte: quero que elogiem a estética antes do significado.", 
        "Escondida, como um segredo só meu e de quem eu permitir ver.", 
        "Como um mistério: que gere perguntas, mas sem eu dar as respostas.", 
        "Como um detalhe elegante que complementa minha aura e meu estilo.", 
        "Nem ligo se olham, fiz para lembrar a mim mesmo da minha jornada."]},
    {"fase": "mcq", "tema": "🐺 SIMBOLISMO DA SOMBRA", "q": "Escolha o animal que mais ecoa com o lado que você esconde do mundo:", "opts": [
        "O Lobo Negro: A raiva reprimida e o instinto silenciado.", 
        "A Serpente: A astúcia, a frieza e a troca constante de pele.", 
        "O Corvo: A observação distante, o contato com o mórbido e a morte.", 
        "O Dragão: O orgulho territorial, a ambição e a fúria adormecida.", 
        "A Fênix: O ciclo de se autossabotar/destruir para poder renascer.", 
        "O Cervo Místico: A vulnerabilidade, a fuga rápida e a introversão profunda."]},
    {"fase": "mcq", "tema": "⚡ GATILHO DE MUDANÇA", "q": "Qual é o seu gatilho mental mais forte para buscar evolução e superação?", "opts": [
        "A dor de uma traição ou de um coração partido.", 
        "A sensação sufocante de estagnação, de estar preso no mesmo lugar.", 
        "O choque de encarar a mortalidade e o fim iminente.", 
        "Uma revelação espiritual, psíquica ou intelectual repentina.", 
        "O desejo de provar a alguém (ou a si mesmo) que você é capaz e implacável.", 
        "A necessidade de criar um legado que sobreviva à minha própria morte."]},
    {"fase": "mcq", "tema": "📖 VISÃO DE MUNDO", "q": "Qual dessas filosofias de vida guia suas decisões invisíveis?", "opts": [
        "Estoicismo: Aceitar o que não posso mudar e dominar minha própria mente.", 
        "Niilismo Positivo: Nada tem um sentido inerente, então sou livre para criar o meu.", 
        "Existencialismo: Sou o único responsável por construir minha própria essência.", 
        "Romantismo Obscuro: A vida é trágica, mas é na dor que mora a verdadeira poesia.", 
        "Taoísmo: O caminho é o fluxo. Resistir cria dor, adaptar-se traz poder absoluto.", 
        "Pragmatismo: Ação e reação. Apenas o que posso tocar e conquistar é real."]},
    {"fase": "mcq", "tema": "🩸 PERCEPÇÃO SOMÁTICA", "q": "O que a dor do processo da tatuagem significa pra você na maca?", "opts": [
        "Um preço necessário e puramente físico para se obter a arte final.", 
        "Um ritual terapêutico de cura: a dor externa silencia o caos interno.", 
        "Uma provação de resistência mental, um teste de força e limite.", 
        "Um momento meditativo e forçado para me desconectar do mundo lá fora.", 
        "É uma adrenalina viciante que me faz lembrar que estou vivo.", 
        "Odeio a dor, faria anestesiado se não comprometesse o resultado da arte."]},
    {"fase": "mcq", "tema": "⚖️ OPOSIÇÃO JUNGUIANA", "q": "Qual desses cenários paradoxais mais fascina a sua imaginação?", "opts": [
        "A Máquina e a Carne (Fusão do biológico com o tecnológico / Biomecânico).", 
        "A Morte e a Flor (A beleza nascendo da decadência / Crânio com Rosas).", 
        "A Ordem e o Caos (Anjos armados, santidade com estética sombria e bélica).", 
        "O Cosmos e o Abismo (A imensidão esmagadora do espaço sideral ou do oceano).", 
        "A Tradição e a Ruptura (Estátuas clássicas vandalizadas com pichações urbanas).", 
        "A Ciência e o Ocultismo (Anatomia médica misturada com geometria sagrada)."]},
    
    {"fase": "escala", "tema": "⚖️ ESCALA DE INTENSIDADE 1", "q": "A ordem, a geometria e a simetria me trazem mais paz e conforto do que a imprevisibilidade e o caos livre das manchas.", "opts": ["1 - Discordo Totalmente", "2 - Discordo Fortemente", "3 - Discordo Levemente", "4 - Concordo Levemente", "5 - Concordo Fortemente", "6 - Concordo Totalmente"]},
    {"fase": "escala", "tema": "⚖️ ESCALA DE INTENSIDADE 2", "q": "Eu prefiro que minha dor e minhas cicatrizes sejam vistas e eternizadas como um troféu orgulhoso, do que escondidas do mundo.", "opts": ["1 - Discordo Totalmente", "2 - Discordo Fortemente", "3 - Discordo Levemente", "4 - Concordo Levemente", "5 - Concordo Fortemente", "6 - Concordo Totalmente"]},
    {"fase": "escala", "tema": "⚖️ ESCALA DE INTENSIDADE 3", "q": "Sinto uma conexão muito mais magnética com temas espirituais, mitológicos e invisíveis do que com a realidade material e concreta.", "opts": ["1 - Discordo Totalmente", "2 - Discordo Fortemente", "3 - Discordo Levemente", "4 - Concordo Levemente", "5 - Concordo Fortemente", "6 - Concordo Totalmente"]},
    {"fase": "escala", "tema": "⚖️ ESCALA DE INTENSIDADE 4", "q": "A estética brutal, visceral e agressiva reflete a realidade do mundo de forma muito mais honesta do que a beleza clássica e polida.", "opts": ["1 - Discordo Totalmente", "2 - Discordo Fortemente", "3 - Discordo Levemente", "4 - Concordo Levemente", "5 - Concordo Fortemente", "6 - Concordo Totalmente"]},
    {"fase": "escala", "tema": "⚖️ ESCALA DE INTENSIDADE 5", "q": "Minha tatuagem não tem nenhuma obrigação de ser 'bonita' ou 'agradável' para os outros, ela só precisa transbordar a minha verdade.", "opts": ["1 - Discordo Totalmente", "2 - Discordo Fortemente", "3 - Discordo Levemente", "4 - Concordo Levemente", "5 - Concordo Fortemente", "6 - Concordo Totalmente"]},

    {"fase": "texto", "tema": "🧠 MEMÓRIA", "q": "Qual é a memória ou momento exato da sua vida que você nunca quer esquecer?"},
    {"fase": "texto", "tema": "🧬 ESSÊNCIA", "q": "Se você pudesse resumir sua essência em uma única palavra, frase ou citação, qual seria?"},
    {"fase": "texto", "tema": "⚔️ CICATRIZ", "q": "Existe algum obstáculo insuperável, perda ou trauma que você precisou vencer e que te transformou?"},
    {"fase": "texto", "tema": "👁️ ARTE", "q": "Por que você decidiu marcar a pele permanentemente agora? O que isso significa pra você hoje?"},
    {"fase": "texto", "tema": "🔮 O AMULETO", "q": "Se essa tatuagem funcionasse como um feitiço de poder, o que ela atrairia para a sua vida ou o que ela repeliria?"}
]

CATALOGO_ESTILOS = [
    "Blackwork (Trabalho em Preto Focadão)", "Fine Line (Linhas Finas e Delicadas)", "Realismo P&B (Sombras Clássicas)", 
    "Irezumi (Japonês Tradicional Colorido)", "Oriental P&B (Japonês apenas Preto e Cinza)", "Realismo Colorido (Cores Vivas)", 
    "Watercolor (Aquarela Colorida)", "Neo-Traditional (Neo-Tradicional Colorido)", "Cyberpunk / Biomechanical (Biomecânico)", 
    "Geometric (Geometria Sagrada P&B)", "Trash Polka (Preto, Branco e Vermelho)", "Old School (Tradicional Colorido)"
]
CATALOGO_TONS = [
    "Sombrio (Misterioso e Fechado)", "Empoderador (Força e Superação)", "Contemplativo (Reflexivo e Calmo)", 
    "Enérgico (Dinâmico e Agressivo)", "Melancólico (Saudade e Profundidade)", "Etéreo (Místico e Leve)",
    "Brutal (Cru e Impactante)", "Minimalista (Silencioso e Sutil)"
]

# ==========================================
# FUNÇÕES CORE (HTML, MOTOR IA, REFINAMENTO)
# ==========================================
with st.sidebar:
    st.markdown("<div class='tech-label'>SETUP DO ESTÚDIO</div>", unsafe_allow_html=True)
    logo_upload = st.file_uploader("Logo Marlon Artworks (PNG)", type=['png'])

def gerar_html_book(img_b64, manifesto_txt, logo_file):
    logo_html = f'<img src="data:image/png;base64,{base64.b64encode(logo_file.getvalue()).decode("utf-8")}" class="logo">' if logo_file else '<h1 class="logo-text">MARLON ARTWORKS</h1>'
    texto_limpo = manifesto_txt.replace('**', '').replace('\n', '<br><br>')
    html_content = f"""
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>The Tattoo Book - Marlon Artworks</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@400;600;700&display=swap');
            @page {{ size: A4 landscape; margin: 0; }}
            body {{ margin: 0; padding: 0; background-color: #0A0A0A; color: #F7F7F7; font-family: 'Josefin Sans', sans-serif; width: 297mm; height: 210mm; display: flex; flex-direction: row; box-sizing: border-box; overflow: hidden; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .left-panel {{ width: 50%; height: 100%; padding: 40px; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; border-right: 1px solid rgba(255,255,255,0.05); }}
            .right-panel {{ width: 50%; height: 100%; padding: 60px 80px 60px 40px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; }}
            .header-container {{ position: absolute; top: 40px; left: 40px; }}
            .logo {{ max-height: 40px; }}
            .logo-text {{ font-size: 24px; color: #D91414; margin: 0; font-weight: 700; letter-spacing: 2px; }}
            .subtitle {{ font-size: 12px; color: #888; letter-spacing: 3px; margin-top: 5px; text-transform: uppercase; }}
            .tattoo-img {{ max-width: 90%; max-height: 75%; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); margin-top: 60px; }}
            .manifesto-title {{ color: #D91414; font-size: 16px; letter-spacing: 5px; text-transform: uppercase; margin-bottom: 30px; font-weight: 700; border-bottom: 2px solid #D91414; padding-bottom: 10px; display: inline-block; }}
            .manifesto-text {{ font-size: 15px; line-height: 1.8; color: #D0D0D0; text-align: justify; }}
        </style>
    </head><body>
        <div class="left-panel"><div class="header-container">{logo_html}<div class="subtitle">The Tattoo Book &bull; Manifesto Conceitual</div></div><img src="data:image/png;base64,{img_b64}" class="tattoo-img"></div>
        <div class="right-panel"><div class="manifesto-title">A OBRA</div><div class="manifesto-text">{texto_limpo}</div></div>
    </body></html>
    """
    return html_content

def gerar_imagem(prompt_ingles, estilo):
    permite_cor = any(c in estilo for c in ["Colorido", "Aquarela", "Trash Polka", "Old School", "Irezumi", "New School"]) if estilo else False
    master_quality = "masterpiece, 8k UHD, photorealistic line structure, flawless anatomy, perfectly centered composition, ensure full element integrity, wide visual margins on all sides, no cropping of extremeties, ultra-detailed textures, no artifacts, crisp precision, high contrast lighting. "
    
    if permite_cor:
        img_prompt_final = master_quality + "Professional tattoo design, " + prompt_ingles + ", isolated on absolute white background, vivid ink colors, clean execution, no shading outside the main design, ready to tattoo."
    else:
        img_prompt_final = master_quality + "Professional tattoo stencil, " + prompt_ingles + ", isolated on absolute white background, bold black outlines, clean linework, thermal transfer paper style, pure black ink, no background, ready to tattoo."
    
    try:
        url_imagen = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key=" + API_KEY
        payload_img = {"instances": [{"prompt": img_prompt_final}], "parameters": {"sampleCount": 1}}
        r_img = requests.post(url_imagen, json=payload_img)
        if r_img.status_code == 200: return r_img.json()['predictions'][0]['bytesBase64Encoded']
    except: pass

    prompt_safe = urllib.parse.quote(img_prompt_final)
    r_fb = requests.get(f"https://image.pollinations.ai/prompt/{prompt_safe}?width=2048&height=2048&nologo=true")
    if r_fb.status_code == 200: return base64.b64encode(r_fb.content).decode('utf-8')
    return None

def processar_briefing(dados, modo):
    regra_traducao = "CRITICAL RULE FOR IMAGE PROMPT: Translate specific biological species and elements LITERALLY from Portuguese to English. If the user asks for 'Jaguatirica' -> use 'Ocelot'. 'Onça' -> 'Jaguar'. DO NOT generalize to 'Tiger' or 'Lion'. If they ask for 'Carpa' -> 'Koi'. NEVER alter the requested species or elements."

    if modo == "Quiz":
        nivel_book = "Este é o modo QUIZ GUIADO SINESTÉSICO. Leia atentamente as 25 escolhas psicológicas do cliente. DEDUZA o melhor conceito visual, os elementos, o estilo e o tom."
        contexto_cliente = f"RESPOSTAS DO QUIZ:\n{dados['respostas_quiz']}"
        formato_extra = "Inicie o manifesto explicando de forma imersiva POR QUE este desenho e estilo traduzem a mente e a história do cliente."
    elif modo == "Completo":
        nivel_book = "Este é um modo de IMERSÃO. Use o perfil psicológico para criar um texto profundo."
        contexto_cliente = f"- Conceito: {dados['conceito']}\n- Elementos: {dados['elementos']}\n- Perfil: {dados['perfil']}"
        formato_extra = ""
    else:
        nivel_book = "Este é um modo EXPRESSO. Crie um texto poético focado na estética."
        contexto_cliente = f"- Conceito: {dados['conceito']}\n- Elementos: {dados['elementos']}"
        formato_extra = ""

    prompt_mestre = (
        "Crie um 'Tattoo Book' e um prompt de imagem. "
        "DIRETRIZ ABSOLUTA: O CLIENTE É O PROTAGONISTA. Não mencione o estúdio. O texto deve ser em PORTUGUÊS DO BRASIL. "
        f"{regra_traducao}\n"
        f"{nivel_book} "
        f"Estilo Solicitado: '{dados.get('estilo', 'Deduza do Quiz')}'. Tom: '{dados.get('tom', 'Deduza do Quiz')}'. "
        f"DADOS DO CLIENTE:\n{contexto_cliente}\n"
        "FORMATO DE RESPOSTA OBRIGATÓRIO:\n"
        "PROMPT: [Instrução técnica para gerar a imagem em INGLÊS. Cumpra a regra de tradução literal. Descreva APENAS a arte visual centrada.]\n"
        f"BOOK: [Manifesto em 3 partes curtas. {formato_extra} MÁXIMO 180 PALAVRAS para caber perfeitamente no PDF HTML.]"
    )
    
    # BYPASS DE CENSURA DO GOOGLE
    payload = {
        "contents": [{"parts": [{"text": prompt_mestre}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    ultimo_erro = ""
    for tentativa in range(3):
        r = requests.post(URL_GEMINI, json=payload)
        
        if r.status_code == 200:
            dados_json = r.json()
            if 'promptFeedback' in dados_json and 'blockReason' in dados_json['promptFeedback']:
                return None, None, None, f"⚠️ Censura do Google: Bloqueado por {dados_json['promptFeedback']['blockReason']}"
                
            try:
                res_text = dados_json['candidates'][0]['content']['parts'][0]['text']
                res_text = res_text.replace("**PROMPT:**", "PROMPT:").replace("**BOOK:**", "BOOK:")
                
                if "BOOK:" in res_text:
                    partes = res_text.split("BOOK:")
                    prompt_raw = partes[0].replace("PROMPT:", "").strip()
                    book_content = partes[1].strip()
                    img_b64 = gerar_imagem(prompt_raw, dados.get('estilo', 'Blackwork'))
                    return img_b64, book_content, prompt_raw, None
                else:
                    ultimo_erro = "A IA não enviou a palavra 'BOOK:' no formato exigido."
            except KeyError:
                if 'finishReason' in str(dados_json):
                     motivo = dados_json['candidates'][0].get('finishReason', 'Desconhecido')
                     if motivo != "STOP":
                         return None, None, None, f"⚠️ A IA recusou gerar a arte (Motivo: {motivo})."
                ultimo_erro = "Erro interno ao ler a resposta da IA."
        else:
            ultimo_erro = f"Erro {r.status_code} na API. (Pode ser erro 403 se a chave não estiver no Secrets)"
            
        time.sleep(2)
        
    return None, None, None, f"Falha após 3 tentativas. Detalhe: {ultimo_erro}"

def refinar_prompt_correcao(prompt_atual, correcao_usuario):
    prompt_refinamento = (
        "Take this tattoo prompt: '" + prompt_atual + "'. "
        "Apply this user requested change, maintaining strict anatomical perfection, centered composition, and wide margins: '" + correcao_usuario + "'. "
        "Translate biological species literally (Jaguatirica -> Ocelot, Onça -> Jaguar, do NOT use Tiger). Return ONLY the updated english prompt."
    )
    r = requests.post(URL_GEMINI, json={"contents": [{"parts": [{"text": prompt_refinamento}]}]})
    return r.json()['candidates'][0]['content']['parts'][0]['text'] if r.status_code == 200 else prompt_atual

# ==========================================
# MÁQUINA DE ESTADOS E INTERFACE
# ==========================================
if 'res_img' not in st.session_state:
    st.session_state.res_img = None
    st.session_state.res_book = None
    st.session_state.prompt_interno = None
    st.session_state.estilo_atual = None
    st.session_state.tom_atual = None
    st.session_state.dados_originais = {}
    st.session_state.quiz_step = 0
    st.session_state.quiz_answers = {}

st.markdown("<div class='tech-label'>CONSULTORIA CRIATIVA DE ALTA PERFORMANCE</div>", unsafe_allow_html=True)
st.markdown("<h1>MARLON ARTWORKS</h1>", unsafe_allow_html=True)
st.markdown("---")

if st.session_state.res_img is None:
    modo_briefing = st.radio("MÉTODO DE ATENDIMENTO", ["Expresso (Tenho a Ideia)", "Imersão (Tenho a História)", "Quiz Guiado (Estou em Branco)"], horizontal=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    dados_briefing = {}
    
    # ---------------------------------------------------------
    # FLUXO DO QUIZ SINESTÉSICO
    # ---------------------------------------------------------
    if modo_briefing == "Quiz Guiado (Estou em Branco)":
        total_q = len(QUIZ_DATA)
        step = st.session_state.quiz_step
        
        progresso = int((step / total_q) * 100) if step < total_q else 100
        st.progress(progresso / 100.0)
        st.markdown(f"<p style='text-align:right; font-size:12px; color:#666; font-weight:bold;'>ESTÁGIO {step + 1} DE {total_q}</p>", unsafe_allow_html=True)
        
        if step < total_q:
            q_atual = QUIZ_DATA[step]
            css_class = f"quiz-fase-{q_atual['fase']}"
            
            st.markdown(f"""
                <div class='quiz-container {css_class}'>
                    <div class='quiz-tema'>{q_atual['tema']}</div>
                    <div class='quiz-pergunta'>{q_atual['q']}</div>
                </div>
                <br>
            """, unsafe_allow_html=True)
            
            resposta_atual = None
            if q_atual['fase'] in ['mcq', 'escala']:
                resposta_atual = st.radio("Selecione sua resposta:", q_atual['opts'], label_visibility="collapsed")
            elif q_atual['fase'] == 'texto':
                resposta_atual = st.text_area("Descreva com profundidade:", height=150, placeholder="O que a sua mente revela sobre isso?", label_visibility="collapsed")
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            c_back, c_space, c_next = st.columns([1, 2, 1])
            with c_back:
                if step > 0 and st.button("⬅️ VOLTAR"):
                    st.session_state.quiz_step -= 1
                    st.rerun()
            with c_next:
                if st.button("AVANÇAR ➡️"):
                    if q_atual['fase'] == 'texto' and not resposta_atual.strip():
                        st.warning("O mergulho é necessário. Escreva algo para continuarmos.")
                    else:
                        st.session_state.quiz_answers[q_atual['q']] = resposta_atual
                        st.session_state.quiz_step += 1
                        st.rerun()
        else:
            st.success("Ritual de Mapeamento Concluído.")
            st.markdown("### A MATRIZ ESTÁ PRONTA PARA SER REVELADA")
            st.info("A Inteligência Psicanalítica do estúdio vai ler todas as suas 25 respostas para deduzir o conceito, o traço e o sentimento da tatuagem perfeita.")
            
            if st.button("PROCESSAR ALQUIMIA VISUAL (GERAR TATTOO)"):
                with st.spinner("CRUZANDO DADOS PSICOLÓGICOS, RENDERIZANDO ARTE EM 8K..."):
                    resumo_quiz = "\n".join([f"[{q['fase'].upper()}] P: {q['q']} | R: {st.session_state.quiz_answers.get(q['q'], '')}" for q in QUIZ_DATA])
                    dados_briefing = { 'respostas_quiz': resumo_quiz }
                    st.session_state.dados_originais = dados_briefing.copy()
                    
                    img, book, prompt_cru, erro = processar_briefing(dados_briefing, "Quiz")
                    if erro: st.error(erro)
                    else:
                        st.session_state.res_img = img
                        st.session_state.res_book = book
                        st.session_state.prompt_interno = prompt_cru
                        st.rerun()

    # ---------------------------------------------------------
    # FLUXO TRADICIONAL
    # ---------------------------------------------------------
    else:
        col_e, col_t = st.columns(2)
        with col_e: estilo = st.selectbox("CATÁLOGO DE ESTILOS", CATALOGO_ESTILOS)
        with col_t: tom = st.selectbox("TOM DA OBRA (A VIBE)", CATALOGO_TONS)
        
        st.markdown("---")
        conceito = st.text_area("CONCEITO", placeholder="Sua ideia exata (A IA fará a tradução biológica fiel)")
        elementos = st.text_input("ELEMENTOS VISUAIS", placeholder="Ex: Jaguatirica caminhando, folhas de carvalho...")
        
        dados_briefing = {'estilo': estilo, 'tom': tom, 'conceito': conceito, 'elementos': elementos}
        
        if "Imersão" in modo_briefing:
            st.markdown("### PERFIL DO CLIENTE (IMERSÃO)")
            dados_briefing['perfil'] = f"{st.text_input('Profissão/Paixão:')} | {st.text_input('Desafio superado:')} | {st.text_input('Traço de personalidade:')}"
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("GERAR ARTE E TATTOO BOOK"):
            if conceito:
                with st.spinner("RENDERIZANDO EM ALTA DEFINIÇÃO E ENQUADRAMENTO ABSOLUTO..."):
                    modo_str = "Completo" if "Imersão" in modo_briefing else "Simples"
                    st.session_state.dados_originais = dados_briefing.copy()
                    st.session_state.estilo_atual = estilo
                    st.session_state.tom_atual = tom
                    
                    img, book, prompt_cru, erro = processar_briefing(dados_briefing, modo_str)
                    if erro: st.error(erro)
                    else:
                        st.session_state.res_img = img
                        st.session_state.res_book = book
                        st.session_state.prompt_interno = prompt_cru
                        st.rerun()
            else:
                st.warning("Preencha o Conceito para iniciar.")

else:
    # ---------------------------------------------------------
    # RESULTADO E EXPORTAÇÃO
    # ---------------------------------------------------------
    raw_img = base64.b64decode(st.session_state.res_img)
    st.image(raw_img, caption="ARTE MATRIZ (ENQUADRAMENTO PROTEGIDO & FIDELIDADE EXTREMA)", use_container_width=True)
    
    with st.expander("🛠️ CORRIGIR UM DETALHE NA ARTE ATUAL"):
        correcao = st.text_input("O que deseja alterar na arte?")
        if st.button("REFINAR DESENHO"):
            if correcao:
                with st.spinner("ATUALIZANDO MATRIZ COM MÁXIMA PRECISÃO..."):
                    novo_prompt = refinar_prompt_correcao(st.session_state.prompt_interno, correcao)
                    nova_img = gerar_imagem(novo_prompt, st.session_state.estilo_atual)
                    if nova_img:
                        st.session_state.prompt_interno = novo_prompt
                        st.session_state.res_img = nova_img
                        st.rerun()

    with st.expander("🔄 GERAR VERSÃO ALTERNATIVA (MUDAR ESTILO OU TOM)"):
        idx_estilo = CATALOGO_ESTILOS.index(st.session_state.estilo_atual) if st.session_state.estilo_atual in CATALOGO_ESTILOS else 0
        idx_tom = CATALOGO_TONS.index(st.session_state.tom_atual) if st.session_state.tom_atual in CATALOGO_TONS else 0
        
        novo_estilo = st.selectbox("TESTAR NOVO ESTILO", CATALOGO_ESTILOS, index=idx_estilo)
        novo_tom = st.selectbox("TESTAR NOVA VIBE", CATALOGO_TONS, index=idx_tom)
        
        if st.button("GERAR NOVA VERSÃO"):
            with st.spinner("RECRIANDO O PROJETO COM A NOVA DIREÇÃO..."):
                dados_alt = st.session_state.dados_originais.copy()
                dados_alt['estilo'] = novo_estilo
                dados_alt['tom'] = novo_tom
                modo_str = "Quiz" if 'respostas_quiz' in dados_alt else ("Completo" if dados_alt.get('perfil') else "Simples")
                
                img_alt, book_alt, prompt_alt, erro_alt = processar_briefing(dados_alt, modo_str)
                if not erro_alt:
                    st.session_state.res_img = img_alt
                    st.session_state.res_book = book_alt
                    st.session_state.prompt_interno = prompt_alt
                    st.session_state.estilo_atual = novo_estilo
                    st.session_state.tom_atual = novo_tom
                    st.rerun()
                else: st.error(erro_alt)
    
    st.markdown("---")
    st.markdown("<div class='tech-label'>THE TATTOO BOOK</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='book-container'>{st.session_state.res_book}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button("BAIXAR IMAGEM", raw_img, "marlon_tattoo.png", "image/png")
    with col_b:
        html_code = gerar_html_book(st.session_state.res_img, st.session_state.res_book, logo_upload)
        st.download_button("EXPORTAR BOOK (HTML)", data=html_code, file_name="Tattoo_Book_Marlon.html", mime="text/html")
    with col_c:
        if st.button("COMEÇAR DO ZERO"):
            st.session_state.res_img = None
            st.session_state.res_book = None
            st.session_state.quiz_step = 0
            st.session_state.quiz_answers = {}
            st.rerun()
