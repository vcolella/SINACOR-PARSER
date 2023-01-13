# SINACOR-PARSER
Parser gratuito para notas de corretagem no formato SINACOR que não requer conexão com internet ou compartilhamento de suas notas de corretagem.

O objetivo inicial é fornecer um resumo simples da quantidade de cotas de cada ativo, preço médio e total do patrimônio.

---

## Running in command line:

1. Add all of your pdf notes to the `pdf` directory. 
2. Open a terminal window and navigate to the repo's root.
3. Run the script `parser.py`
    ```shell
    $  python .\parser.py
    ```
    > :warning: **CAUTION** : This tool is under development and might generate wrong results. Thus, I don't take any responsability for the reliability of the generated data.

## Running programmatically:

### Instantiating

If you're running your script from the repo's root, create a `parser` object with:
```python
from sinacor_parser import SinacorParser

parser = SinacorParser()
```  
&nbsp;  
By default, the pdfs with broker notes are read from the `.\pdf` directory. If you wish to read from anywhere else, use the `pdf_directory` keyword :

```python
parser = SinacorParser(pdf_directory="full_path_to_directory")
```  
### Processing

To start reading the pdfs, run :

```python
report, negotiations = parser.process()
```

where `report` and `negotiations` are dataframes with the extracted data.  

### Exporting

Finally, to export the data to a spreadsheet use:  

```python
parser.export()
```

 or

```python
parser.export(output_name="my_name_without_extension")
```
to specify the name of the spreadsheet. If no keyword is provided, the default name of the output is `output.xlsx` and it's saved to the `.\output` directory.



---

## TODO
- [x] Implement import as module
- [x] Reorganize files for repo
- [ ] Split reports by *cpf*
- [ ] Track sales
- [ ] Calculate DARF for sales
- [x] Implement export to spreadsheet
- [x] Read files with multiple pages
- [x] Skip repeated notes
- [ ] Adicionar exportação de `csv` 

