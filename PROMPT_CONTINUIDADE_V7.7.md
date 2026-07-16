# Prompt de continuidade — Minerador de Produtos v7.7

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v7.7 — Auto-Location Rotation**.

## Estado atual

O Metadata Pro (v7.7) agora automatiza a seleção de localização. 

### Novidades da v7.7:
1.  **Localização Automática:** O checkbox "Adicionar localização" agora vem marcado por padrão e seleciona uma cidade aleatória do Brasil.
2.  **Rotação de Local:** A cada processamento concluído, uma nova localização é sorteada para a próxima execução.
3.  **Controle de Sessão:** O utilizador pode visualizar a localização sorteada e forçar uma nova troca através do botão "🔄 Trocar local".
4.  **Fluxo de URL:** O botão de limpeza é o único gatilho para download e processamento, garantindo que o estado da interface permaneça limpo até a ação explícita.

## Ficheiros alterados na v7.7

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Implementação da lógica de `metadata_pro_localizacao_fixa` no `st.session_state` e rotação pós-sucesso. |
| `marketplace.app.py` | Versão atualizada para `v7.7 - Auto-Location Rotation`. |

## Validação

Os testes de unidade e fumaça continuam a passar (**5/5**). A lógica de rotação foi validada e garante que cada "limpeza" resulte num ficheiro com metadados de localização distintos, se a opção estiver ativa.

## Próximos passos

1.  Monitorizar a reatividade do Streamlit ao trocar de local manualmente.
2.  Avaliar se a marcação padrão (checkbox marcado) atende a todos os casos de uso ou se deve ser opcional em certas categorias.
