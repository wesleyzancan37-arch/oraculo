import streamlit as st
import os
import subprocess
import tempfile
from pathlib import Path
import sys

# Configuração da página
st.set_page_config(
    page_title="Downloader de Vídeos",
    page_icon="🎬",
    layout="wide"
)

# Verificar se yt-dlp está instalado
def check_ytdlp_installed():
    try:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], 
                      capture_output=True, check=True)
        return True
    except:
        return False

# Função para instalar yt-dlp
def install_ytdlp():
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], 
                      capture_output=True, check=True)
        return True
    except:
        return False

# Função para obter informações do vídeo
def get_video_info(url):
    try:
        cmd = [sys.executable, "-m", "yt_dlp", "-j", "--no-warnings", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        return None
    except:
        return None

# Função para baixar vídeo
def download_video(url, download_path, format_code=None, audio_only=False):
    try:
        cmd = [sys.executable, "-m", "yt_dlp"]
        
        # Adicionar opções baseadas nas escolhas
        if audio_only:
            cmd.extend(["-x", "--audio-format", "mp3"])
        elif format_code:
            cmd.extend(["-f", format_code])
        else:
            cmd.extend(["-f", "best"])
        
        # Adicionar caminho de saída
        cmd.extend(["-o", os.path.join(download_path, "%(title)s.%(ext)s")])
        
        # Adicionar URL
        cmd.append(url)
        
        # Executar download
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output_lines = []
        
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for line in process.stdout:
            if "ETA" in line or "%" in line:
                # Tentar extrair porcentagem
                import re
                match = re.search(r'(\d+\.?\d*)%', line)
                if match:
                    percent = float(match.group(1))
                    progress_bar.progress(min(percent / 100, 1.0))
                    status_text.text(f"Progresso: {percent:.1f}% - {line.strip()}")
            output_lines.append(line)
        
        process.wait()
        
        if process.returncode == 0:
            return True, "Download concluído com sucesso!"
        else:
            error_msg = process.stderr.read()
            return False, f"Erro no download: {error_msg}"
            
    except Exception as e:
        return False, f"Erro: {str(e)}"

# Título da aplicação
st.title("🎬 Downloader de Vídeos")
st.markdown("---")

# Verificar/instalar yt-dlp
if not check_ytdlp_installed():
    st.warning("📦 yt-dlp não está instalado. Instalando...")
    if install_ytdlp():
        st.success("✅ yt-dlp instalado com sucesso!")
        st.rerun()
    else:
        st.error("❌ Falha ao instalar yt-dlp. Verifique sua conexão com a internet.")
        st.stop()

# Barra lateral para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Selecionar diretório de download
    st.subheader("📁 Local de Download")
    
    # Opção 1: Diretório padrão
    download_dir = st.text_input(
        "Caminho para salvar os vídeos:",
        value=os.path.join(str(Path.home()), "Downloads")
    )
    
    # Opção 2: Selecionar diretório (se suportado)
    st.caption("Ou use um diretório temporário:")
    if st.button("📂 Usar Diretório Temporário"):
        download_dir = tempfile.mkdtemp()
        st.success(f"Diretório temporário criado: {download_dir}")
    
    # Verificar se diretório existe
    if not os.path.exists(download_dir):
        st.warning("⚠️ Diretório não existe. Criando...")
        os.makedirs(download_dir, exist_ok=True)
    
    st.info(f"**Vídeos serão salvos em:**\n`{download_dir}`")
    
    st.markdown("---")
    
    # Opções avançadas
    st.subheader("🎛️ Opções Avançadas")
    audio_only = st.checkbox("Baixar apenas áudio (MP3)")
    
    st.markdown("---")
    st.caption("Feito com Streamlit e yt-dlp")

# Área principal
col1, col2 = st.columns([2, 1])

with col1:
    # Entrada da URL
    st.subheader("🔗 Cole a URL do Vídeo")
    url = st.text_input(
        "URL:",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed"
    )
    
    # Botão para colar da área de transferência
    if st.button("📋 Colar da Área de Transferência"):
        try:
            import pyperclip
            clipboard_content = pyperclip.paste()
            if clipboard_content and ("youtube.com" in clipboard_content or "youtu.be" in clipboard_content):
                st.session_state.url_input = clipboard_content
                st.rerun()
        except:
            st.warning("Não foi possível acessar a área de transferência")
    
    if url:
        # Obter informações do vídeo
        with st.spinner("Obtendo informações do vídeo..."):
            video_info = get_video_info(url)
        
        if video_info:
            # Exibir informações do vídeo
            st.success("✅ URL válida detectada!")
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.metric("Título", video_info.get('title', 'N/A'))
                st.metric("Duração", f"{video_info.get('duration', 0) // 60}:{video_info.get('duration', 0) % 60:02d}")
            
            with col_info2:
                st.metric("Autor", video_info.get('uploader', 'N/A'))
                st.metric("Visualizações", f"{video_info.get('view_count', 0):,}")
            
            # Formato de download
            st.subheader("📥 Opções de Download")
            
            if not audio_only:
                # Obter formatos disponíveis
                try:
                    formats = video_info.get('formats', [])
                    if formats:
                        format_options = {}
                        for f in formats:
                            if f.get('format_note') and f.get('ext') in ['mp4', 'webm']:
                                quality = f"{f.get('format_note', '')} ({f.get('ext', '')})"
                                format_options[quality] = f.get('format_id')
                        
                        if format_options:
                            selected_format = st.selectbox(
                                "Selecione a qualidade:",
                                options=list(format_options.keys()),
                                index=len(format_options)-1
                            )
                            format_code = format_options[selected_format]
                        else:
                            format_code = None
                    else:
                        format_code = None
                except:
                    format_code = None
            else:
                format_code = None
                st.info("Baixando apenas áudio em MP3")
            
            # Botão de download
            st.markdown("---")
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn2:
                download_button = st.button(
                    "🚀 Iniciar Download",
                    type="primary",
                    use_container_width=True
                )
            
            if download_button:
                if not url:
                    st.error("❌ Por favor, cole uma URL válida")
                elif not os.path.exists(download_dir):
                    st.error("❌ Diretório de download não existe")
                else:
                    # Iniciar download
                    success, message = download_video(url, download_dir, format_code, audio_only)
                    
                    if success:
                        st.balloons()
                        st.success(f"✅ {message}")
                        
                        # Mostrar arquivo baixado
                        try:
                            import glob
                            latest_file = max(glob.glob(os.path.join(download_dir, "*")), 
                                            key=os.path.getctime)
                            st.info(f"📄 Arquivo salvo como: `{os.path.basename(latest_file)}`")
                        except:
                            pass
                    else:
                        st.error(f"❌ {message}")
        
        elif url and not video_info:
            st.error("❌ Não foi possível obter informações do vídeo. Verifique a URL.")

with col2:
    # Instruções e dicas
    st.subheader("📝 Como Usar")
    
    with st.expander("💡 Instruções", expanded=True):
        st.markdown("""
        1. **Cole a URL** do vídeo na caixa de texto
        2. **Escolha o local** para salvar o arquivo
        3. **Selecione a qualidade** desejada
        4. Clique em **Iniciar Download**
        
        **Sites suportados:**
        - YouTube
        - Vimeo
        - Twitter
        - Instagram
        - Facebook
        - E muitos outros
        """)
    
    with st.expander("⚠️ Avisos Legais"):
        st.warning("""
        **Use com responsabilidade:**
        - Respeite os direitos autorais
        - Não distribua conteúdo protegido
        - Use apenas para conteúdo pessoal
        - Verifique as políticas de uso de cada site
        
        Esta ferramenta é apenas para fins educacionais.
        """)
    
    # Status do sistema
    st.subheader("🔧 Status do Sistema")
    
    # Verificar espaço em disco
    try:
        total, used, free = shutil.disk_usage(download_dir)
        st.metric("Espaço livre", f"{free // (2**30)} GB")
    except:
        pass
    
    # Versão do yt-dlp
    try:
        result = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], 
                              capture_output=True, text=True)
        st.caption(f"yt-dlp v{result.stdout.strip()}")
    except:
        st.caption("yt-dlp não disponível")

# Rodapé
st.markdown("---")
st.caption("🔄 Atualize a página para começar um novo download")