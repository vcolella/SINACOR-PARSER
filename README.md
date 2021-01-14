# SINACOR-PARSER
Parser gratuito para notas de corretagem no formato SINACOR que não requer conexão com internet ou compartilhamento de suas notas de corretagem.

O objetivo inicial é fornecer um resumo simples da quantidade de cotas de cada ativo, preço médio e total do patrimônio.

## Utilização

1. Coloque suas notas de corretagem na pasta `pdf`
2. Abra um terminal e navegue até a raíz do repo
3. Rode o script `parser.py`
    ```
    > python .\parser.py
    ```
    > :warning: **ATENÇÃO** : Esta ferramenta encontra-se em desenvolvimento e pode produzir resultados incorretos. Deste modo, não me responsabilizo pela confiabilidade das informações geradas com esta aplicação.

## TODO
- [x] Reorganizar arquivos para o repo
- [ ] Separar relatórios por cpf
- [ ] Rastrear vendas
- [ ] Cálculo de DARF para vendas (?)
- [x] Implementar exportação p/ planilha
- [x] Ler arquivos de múltiplas páginas
- [x] Desconsiderar notas de corretagem repetidas
- [ ] Adicionar exportação de `csv` 

