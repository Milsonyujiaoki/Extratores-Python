async def process_page_async(client, page_image_data, page_num, total_pages, prompt_text, logger=None):
    """Processa uma página de forma assíncrona"""
    try:
        if logger:
            logger.log_api_call(page_num, total_pages, "enviando")
        else:
            print(f"   🤖 [{page_num}/{total_pages}] Enviando para OpenAI Vision API...")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{page_image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        page_text = response.choices[0].message.content
        response_size = len(page_text) if page_text else 0
        
        if logger:
            logger.log_api_call(page_num, total_pages, "sucesso", response_size)
        else:
            print(f"   ✅ [{page_num}/{total_pages}] Resposta recebida: {response_size} caracteres")
        
        return page_num, page_text
        
    except Exception as e:
        if logger:
            logger.log_api_call(page_num, total_pages, "erro", error=str(e))
        else:
            print(f"   ❌ [{page_num}/{total_pages}] Erro: {e}")
        return page_num, f"[ERRO NA API OPENAI: {e}]"

async def extract_text_openai_vision_async(pdf_path, txt_path, api_key=api_key, max_concurrent=3, logger=None):
    """
    Extrai texto usando OpenAI Vision API de forma ASSÍNCRONA
    """
    if not OPENAI_AVAILABLE:
        error_msg = "❌ Biblioteca OpenAI não está instalada. Execute: pip install openai"
        if logger:
            logger.logger.error(error_msg)
        else:
            print(error_msg)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
        return False
    
    # Configuração da API
    if api_key is None:
        api_key = os.environ.get('OPENAI_API_KEY', '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')
    
    if not api_key:
        error_msg = "❌ OPENAI_API_KEY não configurada. Defina a variável de ambiente."
        if logger:
            logger.logger.error(error_msg)
        else:
            print(error_msg)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(error_msg + "\n")
            f.write("Configure: set OPENAI_API_KEY=sua_chave_aqui\n")
        return False
    
    try:
        # Fase de inicialização
        if logger:
            logger.start_phase('INIT', f"Configurando extração para {os.path.basename(pdf_path)}")
            logger.logger.info(f"🔑 API Key configurada: {api_key[:20]}...")
            logger.logger.info(f"⚡ Máximo de requisições simultâneas: {max_concurrent}")
        
        client = AsyncOpenAI(api_key=api_key)
        
        if not logger:
            print(f"🤖 Iniciando extração OpenAI Vision ASSÍNCRONA para {os.path.basename(pdf_path)}...")
            print(f"🔑 API Key configurada: {api_key[:20]}...")
            print(f"⚡ Máximo de requisições simultâneas: {max_concurrent}")
        
        # Fase de conversão PDF
        if logger:
            logger.end_phase('INIT', True)
            logger.start_phase('PDF_CONV', "Convertendo PDF para imagens")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            if not logger:
                print("📄 Convertendo PDF para imagens...")
            
            try:
                poppler_path = r"C:\Users\Maoki\poppler\poppler-23.11.0\Library\bin"
                pages = convert_from_path(pdf_path, dpi=300, output_folder=temp_dir, poppler_path=poppler_path)
                if logger:
                    logger.logger.info(f"✅ PDF convertido: {len(pages)} páginas detectadas")
                else:
                    print(f"✅ PDF convertido: {len(pages)} páginas detectadas")
            except Exception as e:
                if logger:
                    logger.logger.error(f"❌ Erro na conversão PDF: {e}")
                    logger.end_phase('PDF_CONV', False)
                else:
                    print(f"❌ Erro na conversão PDF: {e}")
                raise
            
            # Fase de preparação das páginas
            if logger:
                logger.end_phase('PDF_CONV', True)
                logger.start_phase('TEXT_PROC', "Preparando páginas para processamento")
            
            page_data = []
            prompt_text = """Extraia todo o texto visível nesta imagem de documento PDF. 
                            Mantenha a formatação original o máximo possível, incluindo quebras de linha, 
                            espaçamentos e estrutura do documento. Se houver tabelas, preserve a estrutura tabular.
                            Retorne apenas o texto extraído, sem comentários adicionais."""
            
            if not logger:
                print(f"🔄 Preparando {len(pages)} páginas para processamento paralelo...")
            
            for i, page in enumerate(pages, 1):
                page_path = os.path.join(temp_dir, f"page_{i}.png")
                page.save(page_path, "PNG")
                
                # Verifica tamanho da imagem
                img_size = os.path.getsize(page_path) / 1024  # KB
                
                if logger:
                    logger.log_progress('TEXT_PROC', i, len(pages), f"Página {i}", f"{img_size:.1f} KB")
                else:
                    print(f"   📊 Página {i}: {img_size:.1f} KB")
                
                # Codifica para base64
                base64_image = encode_image_to_base64(page_path)
                page_data.append((i, base64_image))
            
            # Fase de processamento API
            if logger:
                logger.end_phase('TEXT_PROC', True)
                logger.start_phase('API_CALL', f"Processamento paralelo de {len(pages)} páginas")
            else:
                print(f"🚀 Iniciando processamento PARALELO de {len(pages)} páginas...")
            
            # Cria semáforo para limitar requisições simultâneas
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(page_num, image_data):
                async with semaphore:
                    return await process_page_async(client, image_data, page_num, len(pages), prompt_text, logger)
            
            # Processa todas as páginas em paralelo
            tasks = [process_with_semaphore(page_num, image_data) for page_num, image_data in page_data]
            results = await asyncio.gather(*tasks)
            
            # Fase de salvamento
            if logger:
                logger.end_phase('API_CALL', True)
                logger.start_phase('FILE_SAVE', "Organizando e salvando resultados")
            
            # Organiza resultados
            extracted_text = []
            extracted_text.append("=== EXTRAÇÃO OPENAI VISION API (ASSÍNCRONA) ===\n")
            extracted_text.append(f"Arquivo: {os.path.basename(pdf_path)}\n")
            extracted_text.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            extracted_text.append(f"Páginas processadas: {len(pages)}\n")
            extracted_text.append(f"Processamento: PARALELO ({max_concurrent} requisições simultâneas)\n")
            extracted_text.append("="*50 + "\n\n")
            
            # Ordena resultados por número da página
            results.sort(key=lambda x: x[0])
            
            for page_num, page_text in results:
                if page_text and page_text.strip() and not page_text.startswith("[ERRO"):
                    extracted_text.append(f"=== PÁGINA {page_num} ===\n")
                    extracted_text.append(page_text.strip())
                    extracted_text.append(f"\n\n{'='*30}\n\n")
                    if logger:
                        logger.logger.info(f"📝 Página {page_num}: Texto extraído com sucesso")
                    else:
                        print(f"   📝 Página {page_num}: Texto extraído com sucesso")
                else:
                    extracted_text.append(f"=== PÁGINA {page_num} ===\n")
                    extracted_text.append(page_text if page_text else "[PÁGINA EM BRANCO OU SEM TEXTO DETECTADO]")
                    extracted_text.append(f"\n\n{'='*30}\n\n")
                    if logger:
                        logger.logger.warning(f"⚠️ Página {page_num}: {page_text if page_text and page_text.startswith('[ERRO') else 'Sem texto detectado'}")
                    else:
                        print(f"   ⚠️ Página {page_num}: {page_text if page_text and page_text.startswith('[ERRO') else 'Sem texto detectado'}")
        
        # Salva resultado
        if logger:
            logger.logger.info(f"💾 Salvando resultado em: {txt_path}")
        else:
            print(f"💾 Salvando resultado em: {txt_path}")
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("".join(extracted_text))
        
        # Verifica arquivo salvo
        if os.path.exists(txt_path):
            file_size = os.path.getsize(txt_path)
            if logger:
                logger.log_file_operation("save", txt_path, True, file_size)
                logger.end_phase('FILE_SAVE', True)
            else:
                print(f"✅ OpenAI Vision ASSÍNCRONA: Arquivo salvo ({file_size} bytes)")
        else:
            if logger:
                logger.log_file_operation("save", txt_path, False, error="Arquivo não foi criado")
                logger.end_phase('FILE_SAVE', False)
            else:
                print(f"❌ Erro: Arquivo não foi criado")
            return False
        
        return True
        
    except Exception as e:
        if logger:
            logger.logger.error(f"❌ Erro na OpenAI Vision API ASSÍNCRONA: {e}")
            # Finaliza todas as fases ativas
            for phase in list(logger.phase_times.keys()):
                logger.end_phase(phase, False)
        else:
            print(f"❌ Erro na OpenAI Vision API ASSÍNCRONA: {e}")
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"ERRO NA OPENAI VISION API ASSÍNCRONA: {e}\n")
            f.write("Verifique se a chave da API está configurada corretamente.\n")
        return False

def extract_text_openai_vision(pdf_path, txt_path, api_key=api_key, logger=None):
    """Wrapper síncrono para a função assíncrona"""
    return asyncio.run(extract_text_openai_vision_async(pdf_path, txt_path, api_key, max_concurrent=3, logger=logger))
