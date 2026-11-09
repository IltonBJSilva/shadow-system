# Guia de Prompts para Agendamento Automático via Buffer no Shadow System

Este documento contém os modelos de prompts prontos para você copiar, personalizar e enviar ao agente de IA sempre que desejar que ele organize seus conteúdos, redija as legendas e faça agendamentos de forma autônoma através da integração Buffer do **Shadow System**.

---

## Sumário

1. [Como Usar](#como-usar)
2. [Prompt Mestre: Agendamento em Lote a partir de Pastas de Mídia](#1-prompt-mestre-agendamento-em-lote-a-partir-de-pastas)
3. [Prompt Rápido: Publicação Única ou Pontual](#2-prompt-rápido-publicação-única-ou-pontual)
4. [Prompt de Manutenção: Reagendamento, Edição ou Exclusão](#3-prompt-de-manutenção-edição-ou-exclusão)
5. [Boas Práticas e Regras Técnicas](#4-boas-práticas-e-regras-técnicas)

---

## Como Usar

1. Escolha o template adequado para a sua necessidade abaixo.
2. Substitua os campos entre colchetes (ex.: `[SEU_LOGIN]`, `[CAMINHO_DA_PASTA]`, `[DATA]`).
3. Cole o prompt no chat com o agente.
4. O agente acessará o Shadow System, autenticará se necessário, lerá os arquivos do seu computador, redigirá os textos otimizados para cada rede social e fará o cadastro diretamente pelo formulário de agendamento.
5. Ao final, o agente apresentará uma tabela com a validação de todos os agendamentos registrados.

---

## 1. Prompt Mestre: Agendamento em Lote a partir de Pastas

> **Quando usar:** Para organizar uma pasta com vários conteúdos, ensaios fotográficos, rotinas ou campanhas distribuídas em várias redes (Instagram, TikTok, LinkedIn, etc.) ao longo dos dias.

```markdown
# EXECUÇÃO AUTOMÁTICA DE AGENDAMENTOS | SHADOW SYSTEM

Atue como um agente autônomo especializado em automação de redes sociais, redação de copy estratégica e operação de sistemas web.

Sua tarefa é analisar a minha pasta de mídias, criar as publicações com suas respectivas legendas personalizadas por rede social e realizar todos os agendamentos diretamente no meu sistema Shadow System.

---

### 1. Sistema e Acesso

Acesse a página de novo agendamento do Shadow System:
- URL de Produção: https://shadow-system-5v0w.onrender.com/integrations/buffer/new
(ou URL Local se estiver rodando: http://127.0.0.1:5050/integrations/buffer/new)

Credenciais de Acesso:
- Usuário: [SEU_USUARIO_AQUI]
- Senha: [SUA_SENHA_AQUI]

IMPORTANTE:
- Não utilize o site Buffer.com diretamente.
- Todos os cadastros devem ser feitos exclusivamente dentro da interface do Shadow System.
- Utilize o recurso nativo de upload de imagens do computador que desenvolvemos no sistema.
- Se a sessão não estiver ativa, faça o login e retome a operação imediatamente.

---

### 2. Diretório de Mídias

Pasta raiz:
`[CAMINHO_COMPLETO_DA_PASTA, ex: C:\Users\ilton\Downloads\Fotos]`

Regras para os arquivos:
- Se houver pastas chamadas "Já feito", "Enviados" ou "Lixeira", ignore-as completamente.
- Preserve a ordem dos arquivos indicada pelo nome ao montar carrosséis.
- Não altere, mova ou apague os arquivos originais do meu computador.

---

### 3. Conteúdos e Publicações

Crie as publicações conforme as especificações abaixo:

#### Publicação 1: [Nome / Tema da Publicação]
- **Pasta / Imagem:** [Nome da subpasta ou arquivo]
- **Tipo de Mídia:** [Imagem única / Carrossel com todas as fotos da pasta]
- **Objetivo / Descrição:** [Ex: Registro de treino representando disciplina e progresso]
- **Tom da Legenda:** [Ex: Motivacional moderado, autêntico, descontraído]
- **Destinos:** [Instagram, TikTok, LinkedIn - escolher os canais desejados]

#### Publicação 2: [Nome / Tema da Publicação]
- **Pasta / Imagem:** [Nome da subpasta ou arquivo]
- **Tipo de Mídia:** [Imagem única / Carrossel com todas as fotos da pasta]
- **Objetivo / Descrição:** [Ex: Ensaio reflexivo sobre trajetória de carreira e aprendizados]
- **Tom da Legenda:** [Ex: Texto autoral mais profundo, reflexivo]
- **Destinos:** [Instagram, TikTok, LinkedIn]

[Adicione mais publicações se necessário]

---

### 4. Matriz de Distribuição e Regras de Copy por Rede

- **Instagram:**
  - Legenda engajadora com quebras de linha limpas.
  - No máximo 5 hashtags relevantes no final.
  - Sempre inclua `#PraTodosVerem` seguido de uma breve audiodescrição da imagem.
  - Pelo menos uma imagem obrigatória.
- **TikTok:**
  - Legenda dinâmica, curta e focada em retenção/curiosidade.
  - Hashtags estratégicas de nicho (ex: #FYP e tags do tema).
- **LinkedIn:**
  - Texto profissional, narrativo, focado em insights, aprendizados e valor de carreira.
  - Formatação com parágrafos legíveis e até 3 hashtags no final.

---

### 5. Estratégia de Datas e Horários

- **Início dos agendamentos:** [Ex: A partir de amanhã, 10/11/2026]
- **Horários preferenciais:**
  - Manhã: 08:30 às 09:30
  - Almoço: 12:30 às 13:30
  - Noite: 18:30 às 20:00
- **Distribuição:** Distribua as publicações ao longo dos dias sem concentrar múltiplos posts na mesma rede no mesmo dia.
- **Modo:** Utilize exclusivamente o modo "Data e hora definidas". Não publique imediatamente.

---

### 6. Execução e Validação Final

Para cada postagem:
1. Abra o formulário de novo post.
2. Selecione os canais de destino marcados na matriz.
3. Insira o texto padrão e, quando aplicável, o texto específico nos campos dedicados de cada rede (`text_instagram`, `text_linkedin`, etc.).
4. Faça o upload das imagens locais correspondentes.
5. Configure a data e a hora definidas.
6. Marque a caixa de confirmação e envie ao Buffer.
7. Confirme na listagem (`/integrations/buffer/`) que o post foi registrado com sucesso.

Ao concluir todas as publicações, apresente um relatório final contendo:
- Título da publicação
- Redes sociais atendidas
- Quantidade de mídias enviadas
- Data e horário agendados
- Status de confirmação retornado pelo Shadow System
```

---

## 2. Prompt Rápido: Publicação Única ou Pontual

> **Quando usar:** Para agendar rapidamente um post específico sem precisar configurar uma estrutura completa de lote.

```markdown
# AGENDAMENTO RÁPIDO | SHADOW SYSTEM BUFFER

Por favor, agende uma nova publicação no meu Shadow System com os dados a seguir:

1. **Acesso:**
   - URL: https://shadow-system-5v0w.onrender.com/integrations/buffer/new
   - Usuário: [SEU_USUARIO]
   - Senha: [SUA_SENHA]

2. **Canais de Destino:**
   - [ ] Instagram
   - [ ] TikTok
   - [ ] LinkedIn

3. **Mídia:**
   - Arquivo(s) no computador: `[CAMINHO_DO_ARQUIVO, ex: C:\Users\ilton\Downloads\foto1.jpg]`

4. **Diretrizes do Conteúdo:**
   - **Tema:** [Descreva o assunto do post]
   - **Tom de voz:** [Descontraído / Profissional / Inspirador / Informativo]
   - **Detalhes a mencionar:** [Pontos que não podem faltar no texto]

5. **Agendamento:**
   - **Data:** [DD/MM/AAAA]
   - **Horário:** [HH:MM]

Execute o cadastro diretamente pelo formulário web do Shadow System, faça o upload das imagens e confirme quando estiver agendado, exibindo a legenda gerada e o status.
```

---

## 3. Prompt de Manutenção: Edição ou Exclusão

> **Quando usar:** Para pedir ao agente que reorganize horários, atualize legendas ou limpe postagens agendadas.

```markdown
# MANUTENÇÃO DE POSTAGENS AGENDADAS | SHADOW SYSTEM

Acesse a página de listagem de posts do meu Shadow System:
https://shadow-system-5v0w.onrender.com/integrations/buffer/

Credenciais:
- Usuário: [SEU_USUARIO]
- Senha: [SUA_SENHA]

Por favor, execute as seguintes ações de manutenção nas postagens agendadas:

1. **Localize o post:** [Ex: O post do TikTok sobre "Demon Vexus" agendado para o dia 13/11]
2. **Ação desejada:**
   - [ ] **Editar texto:** Altere o texto para: "[Novo texto desejado]"
   - [ ] **Reagendar:** Mude a data/hora para: [Nova data e hora]
   - [ ] **Postar agora:** Dispare a publicação imediata utilizando o botão "Postar agora".
   - [ ] **Excluir:** Remova a postagem do agendamento utilizando o botão "Excluir".

Confirme a execução conferindo a listagem atualizada e apresente o resultado.
```

---

## 4. Boas Práticas e Regras Técnicas

Ao solicitar agendamentos ao agente, as seguintes regras são aplicadas automaticamente pela integração do Shadow System:

| Plataforma | Limite de Caracteres | Regras de Imagem | Hashtags Recomendadas |
|---|---|---|---|
| **Instagram** | Até 2.200 caracteres | Mínimo 1 imagem (até 10 viram carrossel) | Máximo 5 hashtags (inclui `#PraTodosVerem`) |
| **LinkedIn** | Até 3.000 caracteres | Opcional (suporta 1 ou mais imagens) | De 2 a 4 hashtags no final |
| **TikTok** | Até 2.200 caracteres | Suporta imagens e fotos para carrossel de fotos | Hashtags curtas de nicho (#FYP, #Tema) |

> [!NOTE]
> **Modo Local vs Produção:** Quando você executa localmente em `http://127.0.0.1:5050`, o app armazena as imagens no banco local. Quando executado em produção no Render (`https://shadow-system-5v0w.onrender.com`), o Buffer consome as imagens diretamente com links HTTPS públicos persistentes gerados pelo próprio Shadow System.
