# fastgrid-videos

Vídeos do FastGrid hospedados para postagem automática no Instagram (Reels).

- `videos/`: arquivos finais (.mp4, 9:16), nomeados com a data de publicação no Instagram
- `videos/legendas/`: legenda de cada vídeo (mesmo nome, .txt), pronta pra repostar no TikTok/YouTube
- `longos/`: vídeos longos do YouTube (16:9), com thumbnail e texto (título, descrição com capítulos e tags). Os cortes de cada longo ficam em `videos/` com o nome `<data>_<tema>_corteNN`.

## noticias/

Posts automáticos de notícias do automobilismo para o Instagram (@fast_grid).

- `gerar_cards.py`: gera os cards 1080x1350 (JPEG) a partir de um JSON (ver docstring).
- `posts/<data>_<tipo>/`: cada post numa pasta: imagens (JPEG, servidas pelo raw.githubusercontent.com para a API do Instagram), `legenda.txt` (legenda exata, pronta pra repostar no TikTok), `post.json` e `fontes.md` (links das matérias).
- `estado.json`: notícias já publicadas (para não repetir) e urgentes aguardando aprovação.

Rotinas: resumo semanal (segunda de manhã, publica direto) e checagem de urgentes (a cada 6 h, só publica após aprovação do Gabriel).
