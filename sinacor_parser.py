import pdfplumber
import re
import os
import json
import pandas as pd
from collections import namedtuple
import sys

class SinacorParser:

    # Properties
    print_output = False
    command_line = False
    report, negotiations = None, None
    pdf_directory = ".\pdf"

    def __init__(self, command_line=False, pdf_directory=""):
        if pdf_directory:
            self.pdf_directory = pdf_directory
        if command_line:
            self.command_line = command_line
            self.printBreak()
            print('Bem vindo ao SINACOR-PARSER')
            self.command_line_menu()

    def trunc(self, num, digits):
        """
        Truncates a num for digits decimals, returns float
        """
        sp = str(num).split('.')
        return float('.'.join([sp[0], sp[1][:digits]]))

    def get_ticker(self, esp_titulo):
        """
        Search for the stock's ticker based on the title specification
        """
        with open('.\DB_ativos.json', encoding='utf8') as f:
            data = json.load(f)

            if 'ON' in esp_titulo:  # Workaround to get right title
                tituloAtivo = (esp_titulo.split('ON', 1)[
                               0] + 'ON').replace(' ', '')
            for ativo in data['result']:
                if 'ON' in esp_titulo:  # Workaround to get right title
                    if ativo['nome_pregao'].replace(' ', '') == tituloAtivo:
                        return ativo['sigla']
                else:
                    # Sometimes might fail incorrectly
                    if ativo['nome_pregao'].replace(' ', '') in esp_titulo.replace(' ', ''):
                        return ativo['sigla']

    def process(self):
        if self.command_line:
            print('Processando notas em ' + os.path.join(os.getcwd(), self.pdf_directory) + ' ...')

        # List which notes to process
        notes = [os.path.join(root, file) for root, dirs, files in os.walk(
            self.pdf_directory) for file in files if file.endswith(".pdf")]

        # var stockType = {' ON': 3, ' UNT': 11, ' PNA': 5, ' PNB': 6, ' PNC': 7, ' PND': 8, ' PNE': 11, ' PNF': 12, ' PNG': 12, ' PN': 4};

        # Namedtuple to organize the transactions list
        Transaction = namedtuple(
            'Transaction', 'buy_sell title stock quantity price transaction_value taxes total note_number page_number date broker')

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
        
        # REGEX for identifying values
        linha_negocio_pattern = re.compile(
            r'^1-BOVESPA (C|V)\s+(OPCAO DE COMPRA|OPCAO DE VENDA|EXERC OPC VENDA|VISTA|FRACIONARIO|TERMO)\s+(.*)\s+(\d+)\s(\d+,\d{2})\s(.*,\d{2})\s(C|D)$')  # Nao captura sigla do fii

        stock_pattern = re.compile(r'[A-Z]{4}\d{1,2}')

        val_liq_pattern = re.compile(r'Valor líquido das operações (.*,\d{2})')

        taxa_liq_pattern = re.compile(r'Taxa de liquidação (.*,\d{2})')

        emol_pattern = re.compile(r'Emolumentos (.*,\d{2})')

        valor_tot_pattern = re.compile(
            r'Líquido para \d{2}/\d{2}/\d{4} (.*,\d{2}).*')

        header_pattern = re.compile(r'(\d+)\s+(\d+)\s+(\d{2}/\d{2}/\d{4})')
        data_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')

        # LISTAS
        transactions = []
        index_document = 1
        for note in notes:
            with pdfplumber.open(note) as pdf:
                for j, page in enumerate(pdf.pages):
                    # page = pdf.pages[0]
                    text = page.extract_text()
                    broker = text.splitlines()[3]
                    header = header_pattern.search(text)
                    note_number = header.group(1)
                    page_number = header.group(2)
                    date = header.group(3)

                    # Check if note was already read
                    if [transaction for transaction in transactions if transaction.note_number == note_number and transaction.page_number == page_number and transaction.date == date] == []:
                        
                        # Net value
                        valor_liq = float(val_liq_pattern.search(text).group(
                            1).replace('.', '').replace(',', '.'))
                        
                        # Taxa de liquidacao
                        taxa_liq = float(taxa_liq_pattern.search(text).group(1).replace(
                            '.', '').replace(',', '.'))
                        
                        # Emolumentos
                        emol = float(emol_pattern.search(text).group(1).replace(
                            '.', '').replace(',', '.'))
                        
                        # Valor total
                        valor_tot = float(valor_tot_pattern.search(text).group(
                            1).replace('.', '').replace(',', '.'))

                        for line in text.split('\n'):
                            if linha_negocio_pattern.match(line):
                                buy_sell = linha_negocio_pattern.match(
                                    line).group(1)
                                title = linha_negocio_pattern.match(
                                    line).group(3)

                                if stock_pattern.search(title):
                                    stock = stock_pattern.search(
                                        title).group(0)
                                else:
                                    stock = self.get_ticker(title)

                                quantity = int(
                                    linha_negocio_pattern.match(line).group(4))

                                price = float(linha_negocio_pattern.match(
                                    line).group(5).replace(',', '.'))

                                transaction_value = float(linha_negocio_pattern.match(
                                    line).group(6).replace('.', '').replace(',', '.'))

                                taxes = quantity * price * \
                                    (emol + taxa_liq) / valor_liq

                                total = quantity * price * \
                                    (1 + (emol + taxa_liq) / valor_liq)

                                transactions.append(Transaction(buy_sell, title, stock, quantity,
                                                       price, transaction_value, taxes, total, note_number, page_number, date, broker))
                                # End of file reading
            if self.command_line:
                print(str(index_document) + ' de ' + str(len(notes)) + ' documentos lidos.', end='\r')
            index_document += 1

        self.negotiations = pd.DataFrame(transactions)
        self.negotiations['date'] = pd.to_datetime(self.negotiations['date'], dayfirst=True)

        self.report = self.negotiations.groupby(['stock'], as_index=True).apply(self.groupReport).round(2)

        if self.command_line:
            print('\n\n')
            print(self.report)
            self.command_line_menu()

        return self.report, self.negotiations

    def printBreak(self):
        print('===============================================')

    def command_line_menu(self):
        self.printBreak()
        print('#### MENU DE FUNÇÕES####')
        print('(P) - Processar notas de corretagem')
        print('(E) - Exportar notas de corretagem')
        print('(R) - Resumo das operações')
        print('(Q) - Sair')
        self.printBreak()
        menuOptions = {'P': self.process,
                       'E': self.export,
                       'R': self.summary,
                       'Q': sys.exit
                       }

        oper = input('Comando: ').upper()

        menuOptions[oper]()


    def groupReport(self, grp_obj):
        """
        Creates group filters
        """
        d = {}
        d['quantity'] = grp_obj.quantity.sum()
        d['total'] = grp_obj.total.sum()
        d['avg_price'] = grp_obj.total.sum() / grp_obj.quantity.sum()

        return pd.Series(d, index=['quantity', 'avg_price', 'total'])

    def export(self, file_name=""):
        
        if not file_name and self.command_line:
            name = input('  >> Nome do arquivo : ')
        elif file_name:
            name = file_name
        else:
            name = "export"
        
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(os.path.join(
            os.getcwd(), 'output', name + ".xlsx"), engine='xlsxwriter')

        # Convert the dataframe to an XlsxWriter Excel object. Turn off the default
        # header and index and skip one row to allow us to insert a user defined
        # header.
        self.report.to_excel(
            writer, sheet_name='Consolidated', startrow=1, header=False, index=True)

        self.negotiations.to_excel(
            writer, sheet_name='Negociações', startrow=1, header=False, index=False)

        # Get the xlsxwriter workbook and worksheet objects.
        workbook = writer.book
        worksheet_report = writer.sheets['Consolidado']
        worksheet_negotiations = writer.sheets['Transactions']

        # Get the dimensions of the dataframe.
        (max_row_report, max_col_report) = self.report.shape
        (max_row_negotiations, max_col_negotiations) = self.negotiations.shape

        # Create a list of column headers, to use in add_table().
        column_settings_report = [{'header': 'stock'}]
        column_settings_negotiations = []
        for header in self.report.columns:
            column_settings_report.append({'header': header})

        for header in self.negotiations.columns:
            column_settings_negotiations.append({'header': header})

        # Add the table.
        worksheet_report.add_table(0, 0, max_row_report, max_col_report,
                                    {'columns': column_settings_report})
        worksheet_negotiations.add_table(0, 0, max_row_negotiations, max_col_negotiations - 1,
                                            {'columns': column_settings_negotiations})

        # Make the columns wider for clarity.
        worksheet_report.set_column(0, max_col_report - 1, 12)
        worksheet_negotiations.set_column(0, max_col_negotiations - 1, 12)

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

        if self.command_line:
            self.command_line_menu()

    def summary(self):
        if self.command_line:
            print(self.report)
            self.command_line_menu()
        return self.report

if __name__ == "__main__":
    SinacorParser(command_line=True)
