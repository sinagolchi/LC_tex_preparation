import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import math
import datetime


st.title('LC-OCD sample prepartion')

@st.experimental_singleton
def cleanup():
    if os.path.exists('file.pdf'):
        os.remove('file.pdf')
    if os.path.exists('file2.pdf'):
        os.remove('file2.pdf')
cleanup()




with st.sidebar:
    files = st.file_uploader(label='upload COC form(s)',accept_multiple_files=True)
    file_dict = {key: value for key, value in zip(range(1, len(files) + 1), files)}

def form_func(key):
    return file_dict[key].name

try:
    order = st.sidebar.multiselect(label='File order', options=file_dict.keys(),default=file_dict.keys(),format_func=form_func)
except:
    st.info('Upload file(s) to start')
    st.stop()

@st.experimental_singleton
def load_files(order,file_dict):
    df_list = []
    for index in order:
        if file_dict[index].type == 'text/csv':
            df_list.append(pd.read_csv(file_dict[index]))
        else:
            df_list.append(pd.read_excel(file_dict[index],header=7))

    for df in df_list:
        df.fillna(0,inplace=True)
        for row in range(len(df)):
            if all(item==0 for item in list(df.iloc[row,:])) or df.iloc[row,0]=='* Need to know whether chemicals in particular organics, oxidants, coagulant aids etc. were  used in the process stream prior to this sampling point. The LC-OCD measures carbon and nitrogen based compounds and addition of these type of chemicals will influnce the appperance of the LC-OCD chromatograms.':
                df.drop(df.index[row::],inplace=True)
                break

    return df_list

df_list = load_files(order,file_dict)

tab1, tab2, tab3 = st.tabs(['list setup','labels','report'])

initials = []
names = []
submit_dates = []
with tab1:
    for index,df in zip(order,df_list):
        with st.expander(label=file_dict[index].name):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(label='Researcher first and last name',key=file_dict[index].name)
                names.append(name)
                initials.append("".join([i[0] for i in name.split()]))
            with col2:
                submit_date = st.date_input(label='Submission date of the COC form',key=file_dict[index].name + ' date')
                submit_dates.append(submit_date.strftime('%b %d, %Y'))
            #st.dataframe(df) #streamlit dataframe api have problems with the data types in versions 1.10 and 1.13
            st.dataframe(df.astype(str)) #a workaround for problem described in line above




#%%
with tab2:
    colu1 , colu2 = st.columns(2)
    numbr = int(colu1.number_input(label='sample number override',min_value=1,value=1,max_value=35))
    report_dfs = [] #a new list for storing new dataframes (this is to prevent mutation of df_list which is returned by a cached fundtion)
    for df_coc,re_init in zip(df_list,initials):
        samples = []
        inj_volumes = []
        samples_latex = []
        codes = []
        codes_latex = []
        report_df = pd.DataFrame()
        report_df[r'Sample ID/ name'] = df_coc['Sample ID/ name'] #carry over the sample name to the new dataframe for reports

        report_df[r'Collection Date/Time'] = [t.strftime('%b %d, %Y %H:%M') if t.time == datetime.time(0) else t.strftime('%b %d, %Y') for t in pd.to_datetime(df_coc['Collection Date /Time'],exact=True)] #convert date time strings into datetime objects and then reformat

        df_coc['Collection Date /Time'] = pd.to_datetime(df_coc['Collection Date /Time']).dt.date
        DF_dict= {1 : 'No Dilution', 2: '5ml + 5ml', 3:'4ml + 8ml', 4:'3ml + 9ml', 5:'2ml + 8ml', 6:'2ml + 10ml' , 7: '1.5ml + 9ml', 8: '1.5ml + 10.5ml', 9: '1.5ml + 12ml', 10: '1ml + 9ml', 11: '1ml + 10ml'} #a dictionary that maps dilution factors to dilution instructions
        bins = [0,5,10,15,20,25,30,35,40,45,50,55] #bining for DOC value in mg/L mp.digitize will use this to find the dilution factor of the sample
        report_df['TOC value'] = df_coc['DOC**             (mg/L Carbon)']
        report_df['DF'] = np.digitize(df_coc['DOC**             (mg/L Carbon)'],bins) #assigning dilution factor to each sample based on its DOC concentration
        researcher = re_init
        for row in range(len(df_coc)):
            if df_coc['DOC**             (mg/L Carbon)'][row] < 1:
                vol = 'inject 4000 ml'
                volume = 4000
            else:
                vol = 'inject 1000 ml'
                volume = 1000
            samples.append(str(numbr) + ': ' +  str(df_coc['Collection Date /Time'][row]) + '_' + researcher + '_' + str(df_coc['Sample ID/ name'][row]) + '\n' + DF_dict[report_df['DF'][row]] + '\n' + vol)
            samples_latex.append(str(numbr) + ': ' +  str(df_coc['Collection Date /Time'][row]) + r'\_SN\_' + str(df_coc['Sample ID/ name'][row]) + r'\\' + DF_dict[report_df['DF'][row]] + r'\\' + vol)
            codes.append(df_coc['Collection Date /Time'][row].strftime('%Y%m%d') + r'\_'+researcher+ r'\_' + str(df_coc['Sample ID/ name'][row]))
            codes_latex.append(str(numbr) + ': ' +df_coc['Collection Date /Time'][row].strftime('%Y%m%d') + r'\_'+researcher+ r'\_' + str(df_coc['Sample ID/ name'][row]+ r'\\' + DF_dict[report_df['DF'][row]] + r'\\' + vol))
            inj_volumes.append(volume)
            numbr += 1
        report_df[r'Injection \mewline volume'] = inj_volumes
        report_df[r'Dilution \newline instructions'] = [DF_dict[report_df['DF'][i]] for i in report_df['DF']]
        report_df['Codes for log'] = codes
        report_df.set_index(r'Sample ID/ name', inplace=True)
        report_dfs.append(report_df)
    #%%report
    # df_import = pd.DataFrame()
    # df_import['Sample name'] = df_coc['Sample ID/ name']
    # df_import['DOC'] = df_coc['DOC**             (mg/L Carbon)']
    # df_import['date'] = df_coc['Collection Date /Time']
    # df_import['Injection volume'] = inj_volumes
    # df_import['Dilution factor'] = df_coc['DF']
    # codes = []
    # for row in range(len(df_coc)):
    #     codes.append(df_coc['Collection Date /Time'][row].strftime('%Y%m%d') + '_SN_' + str(df_coc['Sample ID/ name'][row]))
    # df_import['codes for log'] = codes
#%% generate report

    used_labels= colu2.number_input(label='Used labels',min_value=0,value=0,max_value=79)


    def generate_labels():
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


        try:
            doc.generate_pdf('file',clean_tex=True)
        except:
            st.download_button('Download log', data=open('file.log', 'rb'), file_name='error.log')



    st.button(label='generate labels',on_click=generate_labels)
    try:
        with open('file.pdf', "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')

        pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="650" height="850" type="application/pdf"></iframe>'

        st.markdown(pdf_display, unsafe_allow_html=True)
        st.download_button('Download PDF', data=open('file.pdf', 'rb'), file_name='Labels_{}.pdf'.format(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')))
    except:
        st.info('No report available')

def generate_report():
    for df in report_dfs:
        with tab3:
            st.dataframe(df)

with tab3:
    st.button(label='show dataframe',on_click=generate_report)

with tab3:
    for df in report_dfs:
        with tab3:
            from pylatex import Document, Section, Subsection, Tabular, Math, TikZ, Axis, \
                Plot, Figure, Matrix, Alignat, NoEscape, Package, escape_latex, NewLine, Command

            geometry_options = {"tmargin": "1cm", "lmargin": "1cm"}
            doc2 = Document(geometry_options=geometry_options)
            doc2.packages.append(Package('grffile'))
            doc2.packages.append(Package('booktabs'))
            doc2.packages.append(Package('float'))

            doc2.preamble.append(Command('title', 'LC-OCD sample processing report'))
            doc2.preamble.append(Command('author', 'NSERC Chair in Water Treatment'))
            doc2.preamble.append(Command('date', NoEscape(r'\today')))
            doc2.append(NoEscape(r'\maketitle'))

            for df,name,date in zip(report_dfs,names,submit_dates):
                with doc2.create(Section('Samples submitted by {} on {}'.format(name,date))):
                    t1 = df.to_latex(escape=False,column_format='lp{2cm}cc p{1.5cm} c p{4}')
                    doc2.append(NoEscape(r'\begin{table}[H]'))
                    doc2.append(NoEscape(r'\centering'))
                    doc2.append(NoEscape(t1))
                    doc2.append(NoEscape(r'\end{table}'))

            doc2.generate_pdf('file2',clean_tex=True)

            try:
                with open('file2.pdf', "rb") as f:
                    base64_pdf2 = base64.b64encode(f.read()).decode('utf-8')

                pdf_display2 = F'<iframe src="data:application/pdf;base64,{base64_pdf2}" width="650" height="850" type="application/pdf"></iframe>'

                st.markdown(pdf_display2, unsafe_allow_html=True)
                st.download_button('Download log file', data=open('file2.pdf', 'rb'), file_name='log_report_{}.pdf'.format(
                    datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')))
            except:
                st.info('No report available')