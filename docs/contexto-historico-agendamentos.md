# Contexto Histórico e Operacional: Agendamentos e Fila do Sistema

Este documento registra o histórico completo de conteúdos, configurações de canais, pacotes já agendados e a arquitetura da **Fila Inteligente do Sistema** no **Shadow System**.

---

## 1. Arquitetura da Fila Inteligente do Sistema (Smart Queue)

### O Problema do Limite Gratuito do Buffer
- O Buffer (plano gratuito) impõe um limite estrito de **no máximo 10 posts agendados por rede social**.
- Quando o usuário tenta agendar o 11º post para um canal, o Buffer recusa com o erro:
  `Scheduled posts limit reached. You have 10 scheduled posts out of 10 allowed.`

### A Solução Implementada
Criamos a **Fila do Sistema** no Shadow System:
- **Tabela:** `buffer_queue_posts` (migration `c4d9e8f1a234_buffer_queue_posts.py`).
- **Modelo:** `app.core.models.BufferQueuePost`.
- **Módulo de Lógica:** `app.integrations.buffer.queue`.

### Regras de Negócio e Envio em Lotes
1. **Sem Polling Excessivo:**
   O sistema não fica consultando a API do Buffer a cada minuto. A verificação é realizada:
   - Ao acessar a aba de postagens no painel `/integrations/buffer/`.
   - Ao clicar no botão `⚡ Sincronizar Fila (+5)`.
   - Ao criar novos agendamentos via interface ou script.
2. **Gatilho de Despacho (+5 quando postar 5):**
   - Para cada canal, o sistema conta quantos posts ainda estão com status `scheduled` no Buffer.
   - Quando restarem **5 ou menos posts agendados** (ou seja, 5 já foram publicados e abriram vaga), o sistema puxa automaticamente os próximos **5 posts** pendentes daquela rede na Fila do Sistema e os envia ao Buffer.
3. **Cronologia Progressiva para Frente:**
   - O sistema detecta a data/hora do **último post agendado** atualmente no Buffer para aquele canal (ex.: se o último post for no dia 20 às 18:30).
   - O novo lote de 5 posts é agendado sequencialmente a partir do dia seguinte: **dias 21, 22, 23, 24 e 25**.
   - Garante que nenhum post seja agendado no passado ou encavale com posts existentes.

---

## 2. Canais Ativos do Buffer

| Rede Social | Nome do Perfil | ID do Canal no Buffer | Service |
| :--- | :--- | :--- | :--- |
| 💼 **LinkedIn** | Ilton Batista | `6adad356778b240e2f973d6f` | `linkedin` |
| 📷 **Instagram** | iltonbsilva | `6adad2fa778b240e2f973a98` | `instagram` |
| 🎵 **TikTok** | iltonbsilva | `6ae7a6ebe29c69a1712d1408` | `tiktok` |

---

## 3. Inventário Completo de Postagens

### A. Pacote `01_Ja_Agendados` (Humor Tech #01 a #10)
- **Origem:** `C:\Users\ilton\Downloads\postagens\Humor_Tecnologia_Ilton\01_Ja_Agendados`
- **Arquivos:** `humor_tech_01.png` até `humor_tech_10.png` + `legendas_ja_agendados.txt`.
- **Status:** Agendados anteriormente no Buffer e publicados ao longo dos primeiros dias.

---

### B. Pacote `02_Falta_Agendar` (Humor Tech #11 a #20)
- **Origem:** `C:\Users\ilton\Downloads\postagens\Humor_Tecnologia_Ilton\02_Falta_Agendar`
- **Arquivos:** `humor_tech_11.png` até `humor_tech_20.png` + `legendas_falta_agendar.txt`.
- **Status no LinkedIn:** **10 de 10 agendados com sucesso no Buffer** (datas de 10/11 a 13/11).
- **Status no Instagram:**
  - **#11 ao #18 (8 posts):** Agendados com sucesso no Buffer (preencheram as 8 vagas livres, completando 10/10 com os 2 posts de lifestyle existentes).
  - **#19 e #20 (2 posts):** Salvos como **Rascunhos (Drafts)** diretamente no Buffer (ids `6af271b826f9e6aeead734ad` e `6af271b8e261c09acc90cd42`) com imagem e legenda prontas para liberar quando houver vaga.
- **Status no TikTok:** Esse pacote não continha roteiro específico para TikTok (apenas LinkedIn e Instagram).

---

### C. Pacote `Matematica_Discreta` (#01 a #04)
- **Origem:** `C:\Users\ilton\Downloads\postagens\linkedin e instagram\Matematica_Discreta`
- **Arquivos:**
  - `01_Infográfico Neon_ Testes vs Demonstração.png` (#01)
  - `02_Infográfico Neon_ Indução e Recursão.png` (#02)
  - `03_Infográfico Neon_ Diagonal de Cantor e Problema da Parada.png` (#03)
  - `04_Infográfico Neon_ Matemática Discreta no Dia a Dia.png` (#04)
- **Status:** **Enfileirados na Fila do Sistema** para as 3 redes (LinkedIn, Instagram e TikTok) = **12 itens**.

---

### D. Pacote `Posts_Out_2026` (15 posts)
- **Origem:** `C:\Users\ilton\Downloads\postagens\linkedin e instagram\Posts_Out_2026`
- **Arquivos e Ordem Estratégica Intercalada:**
  1. **N01:** `Noticias/01_PHP2Shell_Atualiza_o_PHP.png`
  2. **M01:** `Memes/01_Sexta_17h58_deploy_rapido.png`
  3. **E01:** `Engajamento/01_Comenta_sua_linguagem.png`
  4. **N02:** `Noticias/02_LinuxFoundation_1_em_4_PRs_AI_Slop.png`
  5. **M02:** `Memes/02_Ta_90_porcento_pronto.png`
  6. **E03:** `Engajamento/03_Escolhe_um.png`
  7. **N03:** `Noticias/03_Linux_libera_codigo_com_IA.png`
  8. **M03:** `Memes/03_Git_blame_foi_voce.png`
  9. **E02:** `Engajamento/02_Pior_nome_de_variavel.png`
  10. **N04:** `Noticias/04_Anthropic_Git_nao_aguentou.png`
  11. **M04:** `Memes/04_Funcionou_de_primeira.png`
  12. **E04:** `Engajamento/04_Seu_codigo_em_3_emojis.png`
  13. **N05:** `Noticias/05_Cloudflare_comprou_o_Deno.png`
  14. **M05:** `Memes/05_47_abas_abertas.png`
  15. **E05:** `Engajamento/05_Do_zero_em_2026.png`
- **Status:** **Enfileirados na Fila do Sistema** para as 3 redes (LinkedIn, Instagram e TikTok) = **45 itens**.

---

### E. Pacote `Guia_Tech` (10 posts)
- **Origem:** `C:\Users\ilton\Downloads\postagens\linkedin e instagram\Posts_Out_2026\Guia_Tech`
- **Série Temática:** *"Um Sistema é um Restaurante 🍽️"*
- **Arquivos:**
  - `01_Linguagens.png` (01)
  - `02_Backend.png` (02)
  - `03_Frontend.png` (03)
  - `04_Banco_de_Dados.png` (04)
  - `05_Cloud.png` (05)
  - `06_Data_Engineering.png` (06)
  - `07_Mensageria.png` (07)
  - `08_DevOps.png` (08)
  - `09_Arquitetura.png` (09)
  - `10_Testes.png` (10)
- **Status:** **Enfileirados na Fila do Sistema** para as 3 redes (LinkedIn, Instagram e TikTok) = **30 itens**.

---

### 📊 Resumo Consolidado da Fila do Sistema:
- **Total de Posts Únicos:** 29 posts (4 Matemática Discreta + 15 Posts Out 2026 + 10 Guia Tech).
- **Total de Itens na Fila (29 × 3 redes):** **87 publicações cadastradas**.
- **Distribuição:**
  - 💼 LinkedIn: 29 posts aguardando.
  - 📷 Instagram: 29 posts aguardando.
  - 🎵 TikTok: 29 posts aguardando.

---

## 4. Hospedagem de Imagens e Tokens

- **Tabela:** `buffer_uploads` (com colunas `token`, `filename`, `mimetype`, `size`, `data`, `created_at`).
- **Endpoint Público:**
  `https://shadow-system-5v0w.onrender.com/integrations/buffer/uploads/<token>/<filename>`
- **Funcionamento:**
  O Buffer recebe apenas o link HTTPS público e busca a imagem diretamente do Shadow System no momento do agendamento ou publicação.

---

## 5. Endpoints e Ações no Shadow System

| Ação | Método / Rota | Descrição |
| :--- | :--- | :--- |
| **Aba da Fila** | `GET /integrations/buffer/?status=queue` | Lista todos os posts na fila com previsão e ações |
| **Sincronizar Lote (+5)** | `POST /integrations/buffer/queue/sync` | Verifica canais com &le; 5 agendados e despacha o próximo lote |
| **Despachar Post Único** | `POST /integrations/buffer/queue/<id>/dispatch` | Envia imediatamente o post específico para o Buffer |
| **Editar Post da Fila** | `GET/POST /integrations/buffer/queue/<id>/edit` | Edita texto, data ou horário previstos |
| **Excluir Post da Fila** | `POST /integrations/buffer/queue/<id>/delete` | Remove o item da fila local |
| **Postar Agora no Buffer** | `POST /integrations/buffer/posts/<id>/share-now` | Publica imediatamente um post já agendado no Buffer |
| **Editar Post no Buffer** | `GET/POST /integrations/buffer/posts/<id>/edit` | Edita legenda/horário de um post já no Buffer |
| **Excluir Post no Buffer** | `POST /integrations/buffer/posts/<id>/delete` | Deleta a publicação do Buffer |
