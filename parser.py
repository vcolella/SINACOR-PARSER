import pdfplumber
import re
import os
import json
import pandas as pd
from collections import namedtuple


class SinacorParser():

    # Properties

    report, negotiations = None, None

    def trunc(self, num, digits):
        '''
        Funciona truncando um valor para um numero de decimais
        e retorna um float
        '''
        sp = str(num).split('.')  # divide em parte inteira e decimais
        # junta string da parte inteira e numero de digitos desejados
        return float('.'.join([sp[0], sp[1][:digits]]))

    def busca_sigla(self, esp_titulo):
        '''
        Busca sigla de um ativo na base de dados a partir da especificacao do titulo
        '''
        with open('.\DB_ativos.json', encoding='utf8') as f:
            data = json.load(f)

            if 'ON' in esp_titulo:  # Gambiarra para pegar titulo certo
                tituloAtivo = (esp_titulo.split('ON', 1)[
                               0] + 'ON').replace(' ', '')
            for ativo in data['result']:
                if 'ON' in esp_titulo:  # Gambiarra para pegar titulo certo
                    if ativo['nome_pregao'].replace(' ', '') == tituloAtivo:
                        return ativo['sigla']
                else:
                    # Este metodo pode falhar retornando correspondecias incorretas
                    if ativo['nome_pregao'].replace(' ', '') in esp_titulo.replace(' ', ''):
                        return ativo['sigla']

    def groupReport(self, grp_obj):
        '''
        Funcao para criar filtro de grupos
        '''
        d = {}
        d['cotas'] = grp_obj.qtd.sum()
        d['total'] = grp_obj.total.sum()
        d['preco_medio'] = grp_obj.total.sum() / grp_obj.qtd.sum()

        return pd.Series(d, index=['cotas', 'preco_medio', 'total'])

    def run(self):

        print('Processando notas em ' + os.path.join(os.getcwd(), "pdf") + ' ...')

        # Lista com caminhos das notas
        notas = [os.path.join(root, file) for root, dirs, files in os.walk(
            ".\pdf") for file in files if file.endswith(".pdf")]

        # var stockType = {' ON': 3, ' UNT': 11, ' PNA': 5, ' PNB': 6, ' PNC': 7, ' PND': 8, ' PNE': 11, ' PNF': 12, ' PNG': 12, ' PN': 4};

        # Namedtuple para organizar a lista de negociacoes
        Neg = namedtuple(
            'Neg', 'compra_venda titulo ativo qtd preco valor_operacao taxas total nr_nota nr_folha data corretora')

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

        valor_tot_re = re.compile(
            r'Líquido para \d{2}/\d{2}/\d{4} (.*,\d{2}).*')

        cabecalho_re = re.compile(r'(\d+)\s+(\d+)\s+(\d{2}/\d{2}/\d{4})')
        data_re = re.compile(r'\d{2}/\d{2}/\d{4}')

        # LISTAS
        negociacoes = []
        i = 1
        for nota in notas:

            with pdfplumber.open(nota) as pdf:

                for j, page in enumerate(pdf.pages):
                    # Leitura do arquivo
                    # page = pdf.pages[0]
                    text = page.extract_text()
                    corretora = text.splitlines()[3]
                    cabecalho = cabecalho_re.search(text)
                    nr_nota = cabecalho.group(1)
                    nr_folha = cabecalho.group(2)
                    data = cabecalho.group(3)  # Data

                    # Cheque de nota repetida
                    if [neg for neg in negociacoes if neg.nr_nota == nr_nota and neg.nr_folha == nr_folha and neg.data == data] == []:

                        valor_liq = float(val_liq_re.search(text).group(
                            1).replace('.', '').replace(',', '.'))  # Valor liquido
                        taxa_liq = float(taxa_liq_re.search(text).group(1).replace(
                            '.', '').replace(',', '.'))  # Taxa de liquidacao
                        emol = float(emol_re.search(text).group(1).replace(
                            '.', '').replace(',', '.'))  # Emolumentos
                        valor_tot = float(valor_tot_re.search(text).group(
                            1).replace('.', '').replace(',', '.'))  # Valor total

                        for line in text.split('\n'):
                            if linha_negocio_re.match(line):
                                compra_venda = linha_negocio_re.match(
                                    line).group(1)
                                esp_titulo = linha_negocio_re.match(
                                    line).group(3)

                                if ativo_re.search(esp_titulo):
                                    ativo = ativo_re.search(
                                        esp_titulo).group(0)
                                else:
                                    ativo = self.busca_sigla(esp_titulo)

                                quantidade = int(
                                    linha_negocio_re.match(line).group(4))

                                preco_ajuste = float(linha_negocio_re.match(
                                    line).group(5).replace(',', '.'))

                                valor_operacao = float(linha_negocio_re.match(
                                    line).group(6).replace('.', '').replace(',', '.'))

                                taxas = quantidade * preco_ajuste * \
                                    (emol + taxa_liq) / valor_liq

                                total = quantidade * preco_ajuste * \
                                    (1 + (emol + taxa_liq) / valor_liq)

                                negociacoes.append(Neg(compra_venda, esp_titulo, ativo, quantidade,
                                                       preco_ajuste, valor_operacao, taxas, total, nr_nota, nr_folha, data, corretora))
                                # FIM DA LEITURA DO ARQUIVO

            print(str(i) + ' de ' +
                  str(len(notas)) + ' documentos lidos.', end='\r')
            i += 1

        print('\n\n')
        resumo = pd.DataFrame(negociacoes)
        resumo['data'] = pd.to_datetime(resumo['data'], dayfirst=True)

        report = resumo.groupby(['ativo'], as_index=True).apply(
            self.groupReport).round(2)
        print(report)

        return resumo, negociacoes

    def printBreak(self):
        print('===============================================')

    def menu(self):
        self.printBreak()
        print('#### MENU DE FUNÇÔES####')
        print('(P) - Processar notas de corretagem')
        print('(E) - Exportar notas de corretagem')
        print('(R) - Resumo das operações')
        print('(Q) - Sair')
        self.printBreak()

        def process():
            self.report, self.negotiations = self.run()
            self.menu()

        def export():
            name = input('  >> Nome do arquivo : ')
            self.report.to_excel(os.path.join(
                os.getcwd(), 'output', name + ".xlsx"))
            self.menu()

        def resumo():
            print(self.report)
            self.menu()

        menuOptions = {'P': process,
                       'E': export, 'R': resumo, 'Q': exit}

        oper = input('Comando: ').upper()

        menuOptions[oper]()

    def __init__(self):
        self.printBreak()
        print('Bem vindo ao SINACOR-PARSER')
        self.menu()


SinacorParser()
