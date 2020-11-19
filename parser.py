import pdfplumber
import re
import os
import json
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


def busca_sigla(esp_titulo):
    with open('.\DB_ativos.json', encoding='utf8') as f:
        data = json.load(f)
        for ativo in data['result']:
            if ativo['nome_pregao'].replace(' ', '') in esp_titulo.replace(' ', ''):
                return ativo['sigla']


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

linha_negocio_re = re.compile(
    r'^1-BOVESPA (C|V)\s+(OPCAO DE COMPRA|OPCAO DE VENDA|EXERC OPC VENDA|VISTA|FRACIONARIO|TERMO)\s+(.*)\s+(\d+)\s(\d+,\d{2})\s(.*,\d{2})\s(C|D)$')  # Nao captura sigla do fii

# REGEX para ativos no caso de corretoras que trazem
ativo_re = re.compile(r'[A-Z]{4}\d{1,2}')

val_liq_re = re.compile(r'Valor líquido das operações (.*,\d{2})')

taxa_liq_re = re.compile(r'Taxa de liquidação (.*,\d{2})')

emol_re = re.compile(r'Emolumentos (.*,\d{2})')

valor_tot_re = re.compile(r'Líquido para \d{2}/\d{2}/\d{4} (.*,\d{2}).*')

data_re = re.compile(r'\d{2}/\d{2}/\d{4}')


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
                compra_venda = linha_negocio_re.match(line).group(1)
                esp_titulo = linha_negocio_re.match(line).group(3)

                if ativo_re.search(esp_titulo):
                    ativo = ativo_re.search(esp_titulo).group(0)
                else:
                    ativo = busca_sigla(esp_titulo)

                quantidade = int(linha_negocio_re.match(line).group(4))

                preco_ajuste = float(linha_negocio_re.match(
                    line).group(5).replace(',', '.'))

                valor_operacao = float(linha_negocio_re.match(
                    line).group(6).replace('.', '').replace(',', '.'))

                taxas = quantidade * preco_ajuste * \
                    (emol + taxa_liq) / valor_liq

                total = quantidade * preco_ajuste * \
                    (1 + (emol + taxa_liq) / valor_liq)

                negociacoes.append(Neg(compra_venda, esp_titulo, ativo, quantidade,
                                       preco_ajuste, valor_operacao, taxas, total, data))

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
