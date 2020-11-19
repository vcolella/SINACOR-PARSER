import pdfplumber
import re
import os
# import numpy as np
import pandas as pd
from collections import namedtuple


def trunc(num, digits):
    '''
    Funciona truncando um valor para um numero de decimais
    e retorna um float
    '''
    sp = str(num).split('.')  # divide em parte inteira e decimais
    # junta string da parte inteira e numero de digitos desejados
    return float('.'.join([sp[0], sp[1][:digits]]))


# Lista com caminhos das notas
notas = [os.path.join(root, file) for root, dirs, files in os.walk(
    ".\pdf") for file in files if file.endswith(".pdf")]

# var stockType = {' ON': 3, ' UNT': 11, ' PNA': 5, ' PNB': 6, ' PNC': 7, ' PND': 8, ' PNE': 11, ' PNF': 12, ' PNG': 12, ' PN': 4};

# Namedtuple para organizar a lista de negociacoes
Neg = namedtuple(
    'Neg', 'compra_venda titulo ativo qtd preco valor_operacao taxas total data')

# REGEX
# market_types = [
#   'OPCAO DE COMPRA',
#   'OPCAO DE VENDA',
#   'EXERC OPC VENDA',
#   'VISTA',
#   'FRACIONARIO',
#   'TERMO',
# ]
# .*([A-Z])\sVISTA([\w ]*)([A-Z]{2})(.*)([A-Z]{1})

# reg_geral = r'1-BOVESPA (C|V)\s*(OPCAO DE COMPRA|OPCAO DE VENDA|EXERC OPC VENDA|VISTA|FRACIONARIO|TERMO)?(.*(\w{4}\d{2}).*)\s(\d{1,})\s(\d+,\d{2})\s(.*,\d{2})\s(C|D)' # Funcinona para fiis mas nao para acoes
# Nao captura sigla do fii
reg_geral = r'^1-BOVESPA (C|V)\s+(OPCAO DE COMPRA|OPCAO DE VENDA|EXERC OPC VENDA|VISTA|FRACIONARIO|TERMO)\s+(.*)\s+(\d+)\s(\d+,\d{2})\s(.*,\d{2})\s(C|D)$'
linha_negocio_re = re.compile(reg_geral)

# REGEX para ativos no caso de corretoras que trazem
reg_ativo = r'[A-Z]{4}\d{1,2}'
ativo_re = re.compile(reg_ativo)

reg_val_liq = r'Valor líquido das operações (.*,\d{2})'
val_liq_re = re.compile(reg_val_liq)

reg_taxa_liq = r'Taxa de liquidação (.*,\d{2})'
taxa_liq_re = re.compile(reg_taxa_liq)

reg_emol = r'Emolumentos (.*,\d{2})'
emol_re = re.compile(reg_emol)

reg_valor_tot = r'Líquido para \d{2}/\d{2}/\d{4} (.*,\d{2}).*'
valor_tot_re = re.compile(reg_valor_tot)


reg_data = r'\d{2}/\d{2}/\d{4}'
data_re = re.compile(reg_data)


# LISTAS
negociacoes = []

for nota in notas:
    with pdfplumber.open(nota) as pdf:
        # Leitura do arquivo
        page = pdf.pages[0]
        text = page.extract_text()

        data = data_re.search(text).group(0)  # Data
        valor_liq = float(val_liq_re.search(text).group(
            1).replace('.', '').replace(',', '.'))  # Valor liquido
        taxa_liq = float(taxa_liq_re.search(text).group(1).replace(
            '.', '').replace(',', '.'))  # Taxa de liquidacao
        emol = float(emol_re.search(text).group(1).replace(
            '.', '').replace(',', '.'))  # Emolumentos
        valor_tot = float(valor_tot_re.search(text).group(
            1).replace('.', '').replace(',', '.'))  # Valor total

        if data == r'25/07/2019':
            print(data)

        for line in text.split('\n'):
            # print(line)

            if linha_negocio_re.match(line):
                COMPRA_VENDA = linha_negocio_re.match(line).group(1)
                ESP_TITULO = linha_negocio_re.match(line).group(3)

                if ativo_re.search(ESP_TITULO):
                    ATIVO = ativo_re.search(ESP_TITULO).group(0)
                else:
                    ATIVO = ESP_TITULO

                QUANTIDADE = int(linha_negocio_re.match(line).group(4))
                PRECO_AJUSTE = float(linha_negocio_re.match(
                    line).group(5).replace(',', '.'))
                VALOR_OPERACAO = float(linha_negocio_re.match(
                    line).group(6).replace('.', '').replace(',', '.'))
                TAXAS = QUANTIDADE * PRECO_AJUSTE * \
                    (emol + taxa_liq) / valor_liq
                TOTAL = QUANTIDADE * PRECO_AJUSTE * \
                    (1 + (emol + taxa_liq) / valor_liq)

                negociacoes.append(Neg(COMPRA_VENDA, ESP_TITULO, ATIVO, QUANTIDADE,
                                       PRECO_AJUSTE, VALOR_OPERACAO, TAXAS, TOTAL, data))

    # print(f'Valor líquido das operações : {valor_liq}')
    # print(f'Taxa de liquidação : {taxa_liq}')
    # print(f'Emolumentos : {emol}')
    # print(f'Líquido para data : {valor_tot}')


resumo = pd.DataFrame(negociacoes)

# print(resumo)

resumo['data'] = pd.to_datetime(resumo['data'], dayfirst=True)

# Funcao para criar grupos


def my_fun(grp_obj):
    d = {}
    d['cotas'] = grp_obj.qtd.sum()
    d['total'] = grp_obj.total.sum()
    d['preco_medio'] = grp_obj.total.sum() / grp_obj.qtd.sum()

    return pd.Series(d, index=['cotas', 'preco_medio', 'total'])


bla = resumo.groupby(['ativo'], as_index=True).apply(my_fun).round(2)
print(bla)
# print(resumo.sum())
