# Posts de fim de semana de GP (F1)

Depois de cada sessão de F1 do fim de semana (TL1, TL2, TL3, Sprint Qualifying, Sprint, Classificação e Corrida), sai um carrossel no Instagram do FastGrid (@fast_grid) com o resultado. **Publica direto, sem aprovação** (o Gabriel autorizou). Tudo em português do Brasil.

Cada sessão tem uma tarefa agendada que roda ~35 min depois do fim previsto (corrida: ~2h15 depois da largada). A tarefa diz qual é o GP, a sessão e a pasta.

## 1. Preparar
- Anexe o repo com add_repo (owner `fastgridf11-a`, repo `fastgrid-videos`, access `push`) e clone: `git clone --depth 1 https://github.com/fastgridf11-a/fastgrid-videos /home/claude/fastgrid-videos`
- Leia este arquivo, a docstring de `noticias/gerar_cards.py` (formato do JSON, tipo `sessao`) e `noticias/estado.json`.
- Se a pasta da sessão já estiver em `estado.json → publicadas`, pare: já foi publicado.

## 2. Confirmar que a sessão acabou e pegar o resultado oficial
- Fonte principal: formula1.com → Results → 2026 (página da sessão). Confirme com mais uma fonte (FIA, Motorsport.com, The Race, Autosport, RacingNews365).
- Se a sessão ainda não terminou ou o resultado oficial ainda não saiu (atraso, bandeira vermelha, chuva): espere 15 min e tente de novo, até 6 tentativas (~1h30). Se ainda assim não tiver, avise o Gabriel e pare.
- Se a sessão foi cancelada: não gere carrossel; publique só se houver notícia relevante (use o tipo `urgente` do gerador) e avise o Gabriel.
- Pegue TODOS os carros na ordem oficial: posição, nome, equipe, tempo (treinos/classificação: melhor volta do 1º e diferença dos demais; corrida/sprint: tempo total do vencedor e diferença, "+1 volta", "Abandono", "Não largou"). Use "AB" para abandono, "NL" para não largou, "DSQ" para desclassificado.
- Classificação: a tabela vira o grid; se houver punição de grid já confirmada, cite em `nota_tabela`.
- Marque `"br": true` em todo piloto brasileiro (ex.: Gabriel Bortoleto, Rafael Câmara, ou outro brasileiro que esteja correndo).
- Nomes de equipe curtos: McLaren, Ferrari, Mercedes, Red Bull, Racing Bulls, Aston Martin, Alpine, Williams, Haas, Audi, Cadillac.

## 3. Montar o post
- JSON tipo `sessao` (ver docstring). `pasta`: `noticias/gp/<pasta-do-gp>/<NN_sigla>` (ex.: `noticias/gp/2026-22-las-vegas/01_tl1`).
  - `sessao`: "Treino Livre 1", "Treino Livre 2", "Treino Livre 3", "Sprint Qualifying", "Sprint", "Classificação", "Corrida".
  - `sigla`: TL1, TL2, TL3, SQ, SPRINT, CLASSIF, CORRIDA.
  - `eh_corrida`: true na Corrida e na Sprint. `eh_classificacao`: true na Classificação e no Sprint Qualifying.
  - `gancho`: 1 ou 2 frases chamativas e honestas sobre o principal fato da sessão (nunca exagerar).
  - `destaques`: 2 a 4 frases curtas: o fato principal, surpresas, incidentes/bandeiras vermelhas, punições e SEMPRE como foram os brasileiros. Na corrida, inclua o efeito no campeonato se houver.
  - `pergunta`: ex. TL: "Quem chega mais forte pra classificação?"; Classificação: "Quem vence amanhã?"; Corrida: "Quem foi o piloto do dia?".
  - `fonte`: "Formula1.com" (+ outra se usada).
- Textos com suas próprias palavras; nunca copie frases das matérias nem use fotos (os cards são só tipografia). Confira nomes, números e posições.
- Rode `python3 noticias/gerar_cards.py <json>`, abra TODAS as imagens com Read e confira se nada ficou cortado ou sobreposto. Ajuste e gere de novo se preciso.

## 4. Legenda e arquivos
- Legenda: 1ª linha com gancho + emoji da sessão (🏁 corrida, ⏱️ classificação, 🔧 treinos); 2–3 linhas com o top 3 e os brasileiros; pergunta para comentar; "Fonte: Formula1.com"; "Segue o @fast_grid pra acompanhar o fim de semana inteiro!"; 6–12 hashtags (#F1 #Formula1 #F1Brasil #<GP> #automobilismo #FastGrid ...).
- Na pasta do post, salve: `legenda.txt` (legenda exata, pro Gabriel repostar no TikTok), `post.json` e `fontes.md` (links).

## 5. Publicar
- Commit e push: `git -c user.name="FastGrid Bot" -c user.email="fastgridf11@gmail.com" commit -m "GP <nome> <sigla>"` e `git -c push.negotiate=true push origin HEAD`.
- URLs: `https://raw.githubusercontent.com/fastgridf11-a/fastgrid-videos/main/<caminho>`. Confirme que respondem antes de publicar.
- Windsor.ai: execute_action, connector `instagram`, account `17841475989170251`, action `create_carousel_post`, params `{image_urls: [na ordem], caption}`.
- Se der erro, tente uma vez de novo; se continuar, avise o Gabriel com o erro e pare.

## 6. Registrar e avisar
- Em `noticias/estado.json → publicadas`, adicione `{data, tipo: "gp", gp, sessao, pasta, media_id (se vier)}` e faça commit/push.
- SendUserMessage ao Gabriel em 2–3 linhas: sessão, top 3 + brasileiros, publicado (ou erro) e o link da pasta para o TikTok: `https://github.com/fastgridf11-a/fastgrid-videos/tree/main/<pasta>`.
