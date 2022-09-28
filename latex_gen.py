import pandas as pd
import numpy as np
import streamlit as st


st.title('LC-OCD sample prepartion')

with st.sidebar:
    files = st.file_uploader(label='upload COC form(s)',accept_multiple_files=True)
    file_dict = {key: value for key, value in zip(range(1, len(files) + 1), files)}
    def form_func(key):
        return file_dict[key].name

    order = st.multiselect(label='File order', options=file_dict.keys(),default=file_dict.keys(),format_func=form_func)
print(order)

st.write(order)



df_coc = pd.read_csv(files[0])
#%%
df_coc['Collection Date /Time'] = pd.to_datetime(df_coc['Collection Date /Time']).dt.date
samples= []
DF_dict= {1 : 'sample only', 2: '5ml + 5ml', 3:'4ml + 8ml', 4:'3ml + 9ml', 5:'2ml + 8ml', 6:'2ml + 10ml' , 7: '1.5ml + 9ml', 8: '1.5ml + 10.5ml', 9: '1.5ml + 12ml', 10: '1ml + 9ml', 11: '1ml + 10ml'}
bins = [0,5,10,15,20,25,30,35,40,45,50,55]
df_coc['DF'] = np.digitize(df_coc['DOC**             (mg/L Carbon)'],bins)
numbr = 7
researcher = 'NM'
inj_volumes = []
samples_latex = []
codes = []
codes_latex = []
for row in range(len(df_coc)):
    if df_coc['DOC**             (mg/L Carbon)'][row] < 1:
        vol = 'inject 4000 ml'
        volume = 4000
    else:
        vol = 'inject 1000 ml'
        volume = 1000
    samples.append(str(numbr) + ': ' +  str(df_coc['Collection Date /Time'][row]) + '_' + researcher + '_' + str(df_coc['Sample ID/ name'][row]) + '\n' + DF_dict[df_coc['DF'][row]] + '\n' + vol)
    samples_latex.append(str(numbr) + ': ' +  str(df_coc['Collection Date /Time'][row]) + r'\_SN\_' + str(df_coc['Sample ID/ name'][row]) + r'\\' + DF_dict[df_coc['DF'][row]] + r'\\' + vol)
    codes_latex.append(str(numbr) + ': ' +df_coc['Collection Date /Time'][row].strftime('%Y%m%d') + r'\_'+researcher+ r'\_' + str(df_coc['Sample ID/ name'][row]+ r'\\' + DF_dict[df_coc['DF'][row]] + r'\\' + vol))
    inj_volumes.append(volume)
    numbr += 1
#%%
df_import = pd.DataFrame()
df_import['Sample name'] = df_coc['Sample ID/ name']
df_import['DOC'] = df_coc['DOC**             (mg/L Carbon)']
df_import['date'] = df_coc['Collection Date /Time']
df_import['Injection volume'] = inj_volumes
df_import['Dilution factor'] = df_coc['DF']
codes = []
for row in range(len(df_coc)):
    codes.append(df_coc['Collection Date /Time'][row].strftime('%Y%m%d') + '_SN_' + str(df_coc['Sample ID/ name'][row]))
df_import['codes for log'] = codes
#%% generate report
used_labels=6
from pylatex import Document, Section, Subsection, Tabular, Math, TikZ, Axis, \
    Plot, Figure, Matrix, Alignat, NoEscape, Package, escape_latex, NewLine

doc = Document(documentclass='article',document_options=['letterpaper'])
doc.packages.append(Package('labels','newdimens'))
doc.packages.append(Package('geometry','pass'))
doc.preamble.append(NoEscape(r'\LabelCols=4'))
doc.preamble.append(NoEscape(r'\LabelRows=20'))
doc.preamble.append(NoEscape(r'\LeftPageMargin=7.6mm'))
doc.preamble.append(NoEscape(r'\RightPageMargin=7.4mm'))
doc.preamble.append(NoEscape(r'\TopPageMargin=12.8mm'))
doc.preamble.append(NoEscape(r'\BottomPageMargin=13.2mm'))
doc.preamble.append(NoEscape(r'\InterLabelColumn=7.4mm'))
doc.preamble.append(NoEscape('\\LeftLabelBorder=1mm\n\\RightLabelBorder=1mm\n\\TopLabelBorder=1mm\n\\BottomLabelBorder=1mm'))

if used_labels != 0:
    for n in range(used_labels):
        doc.append(NoEscape(r'\addresslabel[\centering\scriptsize]{\centering''}'))
for sample in codes_latex:
    doc.append(NoEscape(r'\addresslabel[\centering\scriptsize]{\centering' + sample + '}'))

# doc.generate_tex('test 2')
file = doc.generate_pdf('NM_Sep 28, 2022')
st.download_button('Download PDF',data=open('NM_Sep 28, 2022.pdf','rb'),file_name='test.pdf')



