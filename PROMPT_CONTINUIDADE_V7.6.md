# Prompt de continuidade — Minerador de Produtos v7.6

Continue o desenvolvimento do projeto **Minerador de Produtos**, disponível no repositório `kleberfreitas1990/dev`, a partir da versão **v7.6 — Manual Metadata Cleanup**.

## Estado atual

O ponto de entrada usado no ambiente de desenvolvimento é `marketplace.app.py`. A aba **Metadata Pro** chama `render_metadados_pro()` do ficheiro `modules/metadados_pro.py`.

A versão v7.6 substituiu o processamento automático por um fluxo totalmente manual. O utilizador escolhe um ficheiro local ou informa uma URL, configura a resolução e, opcionalmente, uma localização, e então inicia o trabalho através do botão **“Limpar metadados”**. Nenhum download nem processamento deve ocorrer apenas por colar ou alterar uma URL.

Depois da conclusão, a interface mantém o resultado em `st.session_state` e apresenta somente o botão **“Baixar vídeo limpo”**. A alteração da fonte, resolução ou localização invalida o resultado anterior. Não devem ser exibidos botões adicionais de análise forense, comparação ou processamento automático.

## Regras técnicas do Metadata Pro

O processamento deve continuar a remover metadados anteriores com `-map_metadata -1` e `-map_chapters -1`, reencodificar vídeo com `libx264`, áudio com AAC e gerar um MP4 com `faststart`. Quando o utilizador escolher uma resolução, deve preservar as proporções da imagem e completar a área restante com `pad`, evitando deformação.

Não volte a injetar metadados falsos de fabricante, modelo, `VendorID`, codec proprietário, `AVFoundation`, `OMX`, Apple ou Samsung. O ficheiro é reencodificado por **FFmpeg/libx264**, portanto esses identificadores seriam tecnicamente contraditórios. O objetivo é produzir um ficheiro limpo e coerente, não alegar que se trata de um ficheiro bruto criado diretamente por uma câmara.

Mantenha o aviso de transparência: a limpeza remove metadados anteriores, mas não garante invisibilidade forense. Ferramentas especializadas ainda podem encontrar características compatíveis com FFmpeg/libx264. Não prometa que o vídeo será “indetetável”, “100% original”, “igual à galeria” ou impossível de distinguir de uma captura nativa.

A localização é opcional e deve ser descrita como informação escolhida pelo utilizador, não como prova do local real de gravação. Se for aplicada, utilize a representação ISO 6709 coerente suportada pelo contentor MP4/QuickTime.

## Ficheiros alterados na v7.6

| Ficheiro | Finalidade |
|---|---|
| `modules/metadados_pro.py` | Fluxo manual, download persistente, limpeza coerente, configuração autónoma de resolução/localização e eliminação da dependência circular com `app.py`. |
| `marketplace.app.py` | Atualização da identificação visual para `v7.6 - Manual Metadata Cleanup`. |
| `test_metadados_pro.py` | Testes do comando FFmpeg, remoção de metadados e ausência de falsificação de origem. |
| `test_metadata_ui_smoke.py` | Teste de carregamento da interface Streamlit do Metadata Pro. |
| `validate_metadata_pro.py` | Validação funcional com vídeo sintético, FFmpeg e FFprobe. |

## Validação já executada

Os testes específicos do Metadata Pro passam: **5 testes aprovados**. A validação ponta a ponta também foi executada com um vídeo sintético e confirmou a geração de um MP4 válido, remoção de identificadores falsos de iPhone/Apple e preservação apenas de metadados coerentes com a reencodificação real.

O FFprobe pode apresentar `vendor_id=[0][0][0][0]` e `encoder=Lavc libx264`. Esses valores são gerados pelo contentor/codificador real e não devem ser substituídos por identificadores de dispositivos móveis.

A suíte completa do repositório possui uma falha preexistente e não relacionada com esta alteração: `test_import_produtos_dinamicos.py` espera o atributo `TERMOS_PRINT` em `modules.produtos_dinamicos`, mas o atributo não existe. Não associe essa falha ao Metadata Pro sem primeiro corrigir a compatibilidade desse módulo.

## Próximos passos recomendados

Primeiro, valide a aba Metadata Pro no ambiente publicado e teste um upload local e uma URL de cada plataforma suportada. Em seguida, confirme limites de tamanho e memória no Streamlit, porque o ficheiro processado é mantido em memória para permitir o download. Para ficheiros grandes, considere armazenamento temporário externo com expiração, sem reintroduzir processamento automático.

Depois, trate a falha preexistente de `TERMOS_PRINT` numa alteração separada. Preserve a separação entre correções do Metadata Pro e manutenção dos módulos de descoberta de produtos.

Antes de qualquer novo commit, execute:

```bash
python3 -m compileall -q modules/metadados_pro.py test_metadados_pro.py validate_metadata_pro.py
pytest -q test_metadados_pro.py test_metadata_ui_smoke.py
python3 validate_metadata_pro.py
```

Ao finalizar, apresente claramente os ficheiros alterados, os testes executados e quaisquer limitações restantes. Não exponha credenciais ou tokens em commits, logs, documentação ou mensagens.
